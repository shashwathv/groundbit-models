from fastapi import FastAPI
from contextlib import asynccontextmanager

from .api import router as api_router
from .middleware.cors import add_cors
from .services.result_store import ResultStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = ResultStore()
    yield


app = FastAPI(
    title="Groundbit audio api",
    version="1.0.0",
    description="API for audio detection model",
    lifespan=lifespan
)

add_cors(app=app)

app.include_router(api_router)