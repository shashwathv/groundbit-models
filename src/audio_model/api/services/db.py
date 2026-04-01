import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

MAIN_DB_URL  = os.getenv("MAIN_DB_URL")  
AUDIO_DB_URL = os.getenv("AUDIO_DB_URL")  

main_engine  = create_async_engine(MAIN_DB_URL,  echo=False, pool_pre_ping=True)
audio_engine = create_async_engine(AUDIO_DB_URL, echo=False, pool_pre_ping=True)

MainSession  = sessionmaker(main_engine,  class_=AsyncSession, expire_on_commit=False)
AudioSession = sessionmaker(audio_engine, class_=AsyncSession, expire_on_commit=False)

async def get_main_db():
    async with MainSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def get_audio_db():
    async with AudioSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def check_connections() -> dict:
    results = {"main_db": False, "audio_db": False}
    try:
        async with main_engine.connect() as conn:
            await conn.execute("SELECT 1")
        results["main_db"] = True
    except Exception as e:
        print(f"Main DB connection failed: {e}")
    try:
        async with audio_engine.connect() as conn:
            await conn.execute("SELECT 1")
        results["audio_db"] = True
    except Exception as e:
        print(f"Audio DB connection failed: {e}")
    return results