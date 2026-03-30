from fastapi import APIRouter

from .routes.predict import router as predict_router
from .routes.status import router as status_router

router = APIRouter(prefix="/v1")

router.include_router(predict_router, tags=["predict"])
router.include_router(status_router, tags=["status"])