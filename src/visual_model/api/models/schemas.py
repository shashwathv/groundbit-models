from pydantic import BaseModel
from typing import Optional

class PredictionResponse(BaseModel):
    filename: str
    crop: str
    crop_confidence_pct: float
    disease: Optional[str]
    disease_confidence_pct: Optional[float]
    note: Optional[str] = None