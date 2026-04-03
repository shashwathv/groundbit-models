from pydantic import BaseModel
from typing import Optional

class PredictionResponse(BaseModel):
    filename: str
    crop: Optional[str]
    crop_confidence_pct: Optional[float]
    disease: Optional[str]
    disease_confidence_pct: Optional[float]
    note: Optional[str] = None