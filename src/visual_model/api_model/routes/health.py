from fastapi import APIRouter
from api.services.inference import DISEASE_MODEL_MAP
from api.services.inference import DEVICE

router = APIRouter()

@router.get("/")
def root():
    return {"message": "GroundBit Visual API is running"}

@router.get("/health")
def health():
    return {"status": "ok", "device": str(DEVICE)}

@router.get("/crops")
def list_crops():
    return {"supported_crops": list(DISEASE_MODEL_MAP.keys())}