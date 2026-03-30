import os
from datetime import datetime
from ..models.schemas import DetectionEvent
from .alerting import send_alert
from .result_store import ResultStore
from audio_model.core.audio_cnn import detect

async def run_inference(wav_path: str, store: ResultStore) -> None:
    if not wav_path.endswith('.wav'):
        return 
    try:
        pest_detected, prob_pest = detect(wav_path=wav_path)

        event = DetectionEvent(
            timestamp= datetime.now(),
            pest_detected= pest_detected,
            confidence= prob_pest,
            label="PEST DETECTED" if pest_detected else "NO PEST",
            alerted=False
        )
        
        if pest_detected:
            altered = send_alert(event=event)
            event.alerted = altered

        store.add_event(event=event)
    except Exception as e:
        print(f"Inference failed - {e}")
        return 
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)