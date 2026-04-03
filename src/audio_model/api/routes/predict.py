# routes/predict.py

import os
import uuid
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy import text

from ..models.schemas import PredictResponse
from ..services.worker import run_inference
from ..services.db import AudioSession, DB_ENABLED

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
async def predict(
    request:          Request,
    background_tasks: BackgroundTasks,
    file:             UploadFile | None = File(default=None),
    farmer_id:        str | None = None,
    device_id:        str | None = None,
    session_id:       str | None = None
):
    """
    Accepts audio in two ways:
      1. Raw bytes   — ESP32 sends Content-Type: audio/wav
      2. Multipart   — dashboard tester sends file upload

    Returns the full detection result per dashboard spec.
    """

    store = request.app.state.store

    # ── Read audio bytes ───────────────────────────────────────────
    content_type = request.headers.get("content-type", "")

    if "multipart/form-data" in content_type:
        # dashboard tester or multipart upload
        if not file:
            raise HTTPException(status_code=400, detail="No file in multipart request")
        content = await file.read()
    else:
        # ESP32 raw binary stream
        content = await request.body()

    if not content:
        raise HTTPException(status_code=400, detail="Empty request body")

    # ── Validate WAV magic bytes ───────────────────────────────────
    if not content[:4] == b'RIFF':
        raise HTTPException(
            status_code=400,
            detail="Invalid audio — file must be a WAV (RIFF header missing)"
        )

    # ── Write to temp file ─────────────────────────────────────────
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp:
            tmp.write(content)
            temp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File write failed: {e}")

    recording_id = str(uuid.uuid4())

    # ── DB + S3 path — only when all three IDs are valid UUIDs ────
    def _is_uuid(val: str | None) -> bool:
        if not val:
            return False
        try:
            uuid.UUID(val)
            return True
        except ValueError:
            return False

    ids_valid = all(_is_uuid(v) for v in [farmer_id, device_id, session_id])

    if DB_ENABLED and ids_valid:
        try:
            from ..services.s3 import upload_wav

            # upload to S3 with verification
            s3_key = upload_wav(
                local_path=temp_path,
                farmer_id=farmer_id,
                recording_id=recording_id
            )

            # create row in audio_recordings
            async with AudioSession() as audio_db:
                await audio_db.execute(
                    text("""
                        INSERT INTO audio_recordings
                        (id, session_id, device_id, farmer_id,
                         s3_key, s3_bucket, sample_rate, status, recorded_at)
                        VALUES
                        (:id, :session_id, :device_id, :farmer_id,
                         :s3_key, :s3_bucket, :sample_rate, 'uploaded', :recorded_at)
                    """),
                    {
                        "id":          recording_id,
                        "session_id":  session_id,
                        "device_id":   device_id,
                        "farmer_id":   farmer_id,
                        "s3_key":      s3_key,
                        "s3_bucket":   os.getenv("S3_BUCKET", "agri-file-upload"),
                        "sample_rate": 16000,
                        "recorded_at": datetime.now(timezone.utc)
                    }
                )
                await audio_db.commit()

            print(f"Recording queued: {recording_id} — poller will process")

            # poller handles inference — return queued status
            return PredictResponse(
                status="queued",
                recording_id=recording_id
            )

        except Exception as e:
            # S3 or DB failed — log and fall through to direct inference
            print(f"S3/DB path failed ({e}) — falling back to direct inference")

    # ── Direct inference path ──────────────────────────────────────
    # Used when: no DB configured, IDs missing, or S3/DB failed
    # Run synchronously so we can return the result to the dashboard
    event = await run_inference(
        wav_path=temp_path,
        store=store
    )

    if event is None:
        raise HTTPException(status_code=500, detail="Inference failed — check server logs")

    # ── Return full event per dashboard spec ───────────────────────
    return PredictResponse(
        status="received",
        timestamp=event.timestamp,
        pest_detected=event.pest_detected,
        confidence=event.confidence,
        label=event.label,
        alerted=event.alerted,
        recording_id=recording_id
    )