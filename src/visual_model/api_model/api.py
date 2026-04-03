from fastapi import APIRouter
from api.routes import predict, health

router = APIRouter()
router.include_router(health.router, tags=["Health"])
router.include_router(predict.router, tags=["Prediction"])