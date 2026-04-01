from fastapi import APIRouter, File, UploadFile, HTTPException
from PIL import Image
import io

from api.services.inference import run_pipeline
from api.models.schemas import PredictionResponse

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}

@router.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {file.content_type}")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        image = Image.open(io.BytesIO(raw))
    except Exception:
        raise HTTPException(status_code=422, detail="Could not decode image.")

    try:
        result = run_pipeline(image)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

    return PredictionResponse(filename=file.filename, **result)