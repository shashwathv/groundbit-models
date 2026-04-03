# main.py

import os
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).resolve().parent / '.env')

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .api import router as api_router
from .middleware.cors import add_cors
from .services.result_store import ResultStore
from .services.db import DB_ENABLED, check_connections


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ────────────────────────────────────────────────────
    print("=== Groundbit Audio API starting ===")

    app.state.store = ResultStore()

    # S3 bucket health check
    try:
        from .services.s3 import check_bucket_access
        s3_ok = check_bucket_access()
        if not s3_ok:
            print("WARNING: S3 bucket not accessible — uploads will fail")
    except Exception as e:
        print(f"WARNING: S3 check error — {e}")

    # DB connection check
    if DB_ENABLED:
        db_status = await check_connections()
        print(f"DB status: {db_status}")
    else:
        print("DB not configured — running in direct inference mode")

    # Start poller only if DB is configured
    poller_task = None
    if DB_ENABLED:
        from .services.poller import start_poller
        poller_task = asyncio.create_task(start_poller(app))
        print("Poller started — checking for uploads every 5 seconds")
    else:
        print("Poller disabled — no DB configured")

    print("=== API ready ===")
    yield

    # ── Shutdown ───────────────────────────────────────────────────
    if poller_task:
        poller_task.cancel()
        try:
            await poller_task
        except asyncio.CancelledError:
            print("Poller stopped cleanly")

    print("=== Groundbit Audio API stopped ===")


app = FastAPI(
    title="Groundbit Audio API",
    version="1.0.0",
    description="Pest detection API — ESP32 audio + soil monitoring",
    lifespan=lifespan
)

add_cors(app)
app.include_router(api_router)


# ── Health — available at both / and /v1 ───────────────────────────
@app.get("/health")
@app.get("/v1/health")
async def health_root():
    return {"status": "ok"}


# ── Run directly ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "audio_model.api.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )