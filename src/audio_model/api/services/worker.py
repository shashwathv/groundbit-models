# services/worker.py

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from ..models.schemas import DetectionEvent
from .alerting import send_alert
from .result_store import ResultStore

# ── Import detect() from audio_cnn ────────────────────────────────
sys.path.append(str(Path(__file__).resolve().parents[3]))
from core.audio_cnn import detect


async def run_inference(
    wav_path:     str,
    store:        ResultStore,
    recording_id: str | None = None,
    session_id:   str | None = None,
    farmer_id:    str | None = None,
    audio_db=None,
    main_db=None
) -> DetectionEvent | None:
    """
    Runs CNN14 pest detection on a WAV file.
    Updates result_store for dashboard polling.
    Updates DB rows if IDs are provided.
    Always deletes the temp WAV file when done.
    Returns the DetectionEvent so predict route can return it directly.
    """

    if not wav_path.endswith('.wav'):
        print(f"Invalid format — not a WAV file: {wav_path}")
        return None

    event = None

    try:
        # ── Mark as processing ─────────────────────────────────────
        if audio_db and recording_id:
            from sqlalchemy import text
            await audio_db.execute(
                text("UPDATE audio_recordings SET status = 'processing' WHERE id = :id"),
                {"id": recording_id}
            )
            await audio_db.commit()

        # ── Run inference ──────────────────────────────────────────
        print(f"Running inference on: {os.path.basename(wav_path)}")
        pest_detected, prob_pest = detect(wav_path=wav_path)
        pest_detected = bool(pest_detected)
        prob_pest = float(prob_pest)

        # ── Build event ────────────────────────────────────────────
        event = DetectionEvent(
            timestamp=datetime.now(timezone.utc),
            pest_detected=pest_detected,
            confidence=float(prob_pest),
            label="PEST DETECTED" if pest_detected else "No pest",
            alerted=False
        )

        # ── Send WhatsApp alert ────────────────────────────────────
        if pest_detected:
            soil = store.get_soil()
            alerted = send_alert(event=event, soil=soil)
            event.alerted = alerted

        # ── Store in result_store ──────────────────────────────────
        store.add_event(event=event)
        store.set_listening(True)

        # ── Update audio_recordings in audio DB ────────────────────
        if audio_db and recording_id:
            from sqlalchemy import text
            await audio_db.execute(
                text("""
                    UPDATE audio_recordings
                    SET status       = 'done',
                        pest_found   = :pest_found,
                        confidence   = :confidence,
                        processed_at = :processed_at
                    WHERE id = :id
                """),
                {
                    "id":           recording_id,
                    "pest_found":   pest_detected,
                    "confidence":   float(prob_pest),
                    "processed_at": datetime.now(timezone.utc)
                }
            )
            await audio_db.commit()

        # ── Update detection_sessions ──────────────────────────────
        if pest_detected and audio_db and session_id:
            from sqlalchemy import text
            await audio_db.execute(
                text("""
                    UPDATE detection_sessions
                    SET pest_detections = pest_detections + 1,
                        alerted         = :alerted,
                        alert_sent_at   = :alert_sent_at
                    WHERE id = :id
                """),
                {
                    "id":            session_id,
                    "alerted":       event.alerted,
                    "alert_sent_at": datetime.now(timezone.utc) if event.alerted else None
                }
            )
            await audio_db.commit()

        # ── Update farmers in main DB ──────────────────────────────
        if pest_detected and main_db and farmer_id:
            from sqlalchemy import text
            await main_db.execute(
                text("""
                    UPDATE farmers
                    SET last_pest_detected_at  = :detected_at,
                        total_pest_detections  = total_pest_detections + 1
                    WHERE id = :id
                """),
                {
                    "id":          farmer_id,
                    "detected_at": datetime.now(timezone.utc)
                }
            )
            await main_db.commit()

        print(f"Inference complete — pest: {pest_detected} ({prob_pest:.2%})")
        return event

    except Exception as e:
        print(f"Inference failed — {e}")

        if audio_db and recording_id:
            try:
                from sqlalchemy import text
                await audio_db.execute(
                    text("UPDATE audio_recordings SET status = 'failed' WHERE id = :id"),
                    {"id": recording_id}
                )
                await audio_db.commit()
            except Exception as db_err:
                print(f"Could not mark as failed: {db_err}")

        return None

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
            print(f"Temp file deleted: {wav_path}")