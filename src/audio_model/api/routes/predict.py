import os
import uuid
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Request, HTTPException

from ..services.worker import run_inference
from ..services.s3 import upload_wav
from ..services.db import AudioSession

router = APIRouter()


@router.post("/predict")
async def predict(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    farmer_id: str = None,    
    device_id: str = None,     
    session_id: str = None     
):
    if not file.filename.endswith('.wav') and \
       file.content_type not in ['audio/wav', 'audio/wave']:
        raise HTTPException(
            status_code=400,
            detail="Only .wav files accepted"
        )

    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp:
            temp.write(content)
            temp_path = temp.name
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File processing failed: {e}"
        )

    store       = request.app.state.store
    recording_id = str(uuid.uuid4())

    if farmer_id and device_id and session_id:
        try:
            s3_key = upload_wav(
                local_path=temp_path,
                farmer_id=farmer_id,
                recording_id=recording_id
            )

            async with AudioSession() as audio_db:
                await audio_db.execute(
                    """INSERT INTO audio_recordings
                       (id, session_id, device_id, farmer_id,
                        s3_key, s3_bucket, sample_rate, status, recorded_at)
                       VALUES
                       (:id, :session_id, :device_id, :farmer_id,
                        :s3_key, :s3_bucket, :sample_rate, 'uploaded', :recorded_at)""",
                    {
                        "id":          recording_id,
                        "session_id":  session_id,
                        "device_id":   device_id,
                        "farmer_id":   farmer_id,
                        "s3_key":      s3_key,
                        "s3_bucket":   "agri-file-upload",
                        "sample_rate": 16000,
                        "recorded_at": datetime.now(timezone.utc)
                    }
                )
                await audio_db.commit()
            return {
                "status":       "queued",
                "recording_id": recording_id,
                "filename":     file.filename
            }

        except Exception as e:
            print(f"DB/S3 integration failed, falling back to direct inference: {e}")


    background_tasks.add_task(
        run_inference,
        temp_path,
        store
    )

    return {
        "status":   "received",
        "filename": file.filename
    }