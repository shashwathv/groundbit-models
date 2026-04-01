import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')

from .api import router as api_router
from .middleware.cors import add_cors
from .services.result_store import ResultStore
from .services.poller import start_poller


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.store = ResultStore()
    poller_task = asyncio.create_task(start_poller(app))
    print("Application started — poller running")
    yield

    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        print("Poller stopped cleanly")


app = FastAPI(
    title="Groundbit audio API",
    version="1.0.0",
    description="Pest detection API for Groundbit",
    lifespan=lifespan
)

add_cors(app=app)
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "audio_model.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
