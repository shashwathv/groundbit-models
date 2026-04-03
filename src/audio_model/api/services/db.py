# services/db.py

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

MAIN_DB_URL  = os.getenv("MAIN_DB_URL")
AUDIO_DB_URL = os.getenv("AUDIO_DB_URL")

# ── Engines — only created if URLs are configured ──────────────────
# When connecting via SSH tunnel (localhost), skip SSL — the tunnel encrypts.
# When connecting directly to RDS, use the AWS CA bundle for SSL.
def _connect_args(db_url: str | None) -> dict:
    if not db_url:
        return {}
    if "127.0.0.1" in db_url or "localhost" in db_url:
        return {"ssl": "require"}
    import ssl
    ctx = ssl.create_default_context(cafile=str(Path(__file__).resolve().parents[2] / 'global-bundle.pem'))
    return {"ssl": ctx}

main_engine  = create_async_engine(MAIN_DB_URL,  echo=False, pool_pre_ping=True, connect_args=_connect_args(MAIN_DB_URL))  if MAIN_DB_URL  else None
audio_engine = create_async_engine(AUDIO_DB_URL, echo=False, pool_pre_ping=True, connect_args=_connect_args(AUDIO_DB_URL)) if AUDIO_DB_URL else None

MainSession  = sessionmaker(main_engine,  class_=AsyncSession, expire_on_commit=False) if main_engine  else None
AudioSession = sessionmaker(audio_engine, class_=AsyncSession, expire_on_commit=False) if audio_engine else None

DB_ENABLED = bool(MAIN_DB_URL and AUDIO_DB_URL)



async def get_audio_db():
    if not AudioSession:
        return 
    async with AudioSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_main_db():
    if not MainSession:
        return 
    async with MainSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_connections() -> dict:
    results = {"main_db": False, "audio_db": False, "db_enabled": DB_ENABLED}
    if not DB_ENABLED:
        return results
    try:
        async with main_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        results["main_db"] = True
    except Exception as e:
        print(f"Main DB check failed: {repr(e)}")
    try:
        async with audio_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        results["audio_db"] = True
    except Exception as e:
        print(f"Audio DB check failed: {repr(e)}")
    return results