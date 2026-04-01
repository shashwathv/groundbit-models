import os
from datetime import datetime, timezone
from pathlib import Path
import sys

from ..models.schemas import DetectionEvent
from .alerting import send_alert
from .result_store import ResultStore

sys.path.append(str(Path(__file__).resolve().parents[2]))
from core.audio_cnn import detect


async def run_inference(
    wav_path: str,
    store: ResultStore,
    recording_id: str = None,
    session_id: str = None,
    farmer_id: str = None,
    audio_db=None,
    main_db=None
) -> None:
    """
    Runs pest detection on a WAV file.
    Updates result_store for dashboard.
    Updates DB rows if recording_id provided.
    Deletes temp WAV file when done.
    """

    if not wav_path.endswith('.wav'):
        print(f"Invalid file format: {wav_path}")
        return

    try:
        if audio_db and recording_id:
            await audio_db.execute(
                """UPDATE audio_recordings
                   SET status = 'processing'
                   WHERE id = :id""",
                {"id": recording_id}
            )
            await audio_db.commit()

        pest_detected, prob_pest = detect(wav_path=wav_path)

        event = DetectionEvent(
            timestamp=datetime.now(timezone.utc),
            pest_detected=pest_detected,
            confidence=prob_pest,
            label="PEST DETECTED" if pest_detected else "No pest",
            alerted=False
        )

        if pest_detected:
            alerted = send_alert(event=event)
            event.alerted = alerted

        store.add_event(event=event)

        if audio_db and recording_id:
            await audio_db.execute(
                """UPDATE audio_recordings
                   SET status       = 'done',
                       pest_found   = :pest_found,
                       confidence   = :confidence,
                       processed_at = :processed_at
                   WHERE id = :id""",
                {
                    "id":           recording_id,
                    "pest_found":   pest_detected,
                    "confidence":   float(prob_pest),
                    "processed_at": datetime.now(timezone.utc)
                }
            )
            await audio_db.commit()

        if pest_detected and audio_db and session_id:
            await audio_db.execute(
                """UPDATE detection_sessions
                   SET pest_detections = pest_detections + 1,
                       alerted         = :alerted,
                       alert_sent_at   = :alert_sent_at
                   WHERE id = :id""",
                {
                    "id":            session_id,
                    "alerted":       event.alerted,
                    "alert_sent_at": datetime.now(timezone.utc) if event.alerted else None
                }
            )
            await audio_db.commit()

        if pest_detected and main_db and farmer_id:
            await main_db.execute(
                """UPDATE farmers
                   SET last_pest_detected_at  = :detected_at,
                       total_pest_detections  = total_pest_detections + 1
                   WHERE id = :id""",
                {
                    "id":          farmer_id,
                    "detected_at": datetime.now(timezone.utc)
                }
            )
            await main_db.commit()

    except Exception as e:
        print(f"Inference failed: {e}")

        if audio_db and recording_id:
            try:
                await audio_db.execute(
                    """UPDATE audio_recordings
                       SET status = 'failed'
                       WHERE id = :id""",
                    {"id": recording_id}
                )
                await audio_db.commit()
            except Exception as db_err:
                print(f"Failed to update status to failed: {db_err}")

    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
            print(f"Deleted temp file: {wav_path}")