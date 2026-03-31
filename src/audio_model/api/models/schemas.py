from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DetectionEvent(BaseModel):
    model_config = {"frozen": False}
    timestamp: datetime
    pest_detected: bool
    confidence: float
    label: str
    alerted: bool = False

class StatusResponse(BaseModel):
    listening: bool
    latest: Optional[DetectionEvent] = None

class HistoryRepsonse(BaseModel):
    total: int
    events: list[DetectionEvent]