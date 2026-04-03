# models/schemas.py

from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class DetectionEvent(BaseModel):
    model_config = {"frozen": False}

    timestamp:     datetime
    pest_detected: bool
    confidence:    float          # 0.0–1.0 — dashboard multiplies by 100
    label:         str            # "PEST DETECTED" or "No pest"
    alerted:       bool = False

    @field_validator('confidence')
    @classmethod
    def clamp_confidence(cls, v):
        # dashboard spec: strictly clamped 0.0–1.0
        return round(max(0.0, min(1.0, float(v))), 4)


class SoilReading(BaseModel):
    timestamp:    datetime
    moisture_pct: float           # dashboard expects moisture_pct not moisture
    temp_c:       Optional[float] = None   # optional — ESP32 doesn't send this yet


class StatusResponse(BaseModel):
    listening: bool
    latest:    Optional[DetectionEvent] = None
    soil:      Optional[SoilReading]    = None


class HistoryResponse(BaseModel):
    total:  int
    events: list[DetectionEvent]


# ── Soil input from ESP32 ─────────────────────────────────────────
class SoilInput(BaseModel):
    soil_moisture: float          # ESP32 sends this key
    temp_c:        Optional[float] = None


# ── Predict response — dashboard expects full event back ──────────
class PredictResponse(BaseModel):
    status:        str
    timestamp:     Optional[datetime]  = None
    pest_detected: Optional[bool]      = None
    confidence:    Optional[float]     = None
    label:         Optional[str]       = None
    alerted:       Optional[bool]      = None
    recording_id:  Optional[str]       = None