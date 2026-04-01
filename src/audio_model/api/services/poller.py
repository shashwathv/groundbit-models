import asyncio
from datetime import datetime, timezone

from sqlalchemy import text  # ✅ REQUIRED for SQLAlchemy 2.0

from .db import AudioSession, MainSession
from .s3 import download_wav
from .worker import run_inference
from .result_store import ResultStore


async def start_poller(app) -> None:
    """
    Entry point called from main.py lifespan.
    Runs forever, polling every 5 seconds.
    """
    print("Poller started — checking for unprocessed recordings every 5s")
    while True:
        try:
            await poll_once(app.state.store)
        except Exception as e:
            print(f"Poller cycle error: {e}")
        await asyncio.sleep(5)


async def poll_once(store: ResultStore) -> None:
    """
    One polling cycle:
    - fetch all rows with status = 'uploaded'
    - process each one
    """
    async with AudioSession() as audio_db:
        result = await audio_db.execute(
            text("""
                SELECT id, session_id, farmer_id, s3_key
                FROM audio_recordings
                WHERE status = 'uploaded'
                ORDER BY recorded_at ASC
                LIMIT 10
            """)
        )
        rows = result.mappings().all()  # ✅ safer for async

    if not rows:
        return

    print(f"Poller found {len(rows)} unprocessed recording(s)")

    for row in rows:
        recording_id = str(row["id"])
        session_id   = str(row["session_id"])
        farmer_id    = str(row["farmer_id"])
        s3_key       = row["s3_key"]

        wav_path = None
        try:
            wav_path = download_wav(s3_key=s3_key)

            async with AudioSession() as audio_db:
                async with MainSession() as main_db:
                    await run_inference(
                        wav_path=wav_path,
                        store=store,
                        recording_id=recording_id,
                        session_id=session_id,
                        farmer_id=farmer_id,
                        audio_db=audio_db,
                        main_db=main_db
                    )

        except Exception as e:
            print(f"Failed to process recording {recording_id}: {e}")

            try:
                async with AudioSession() as audio_db:
                    await audio_db.execute(
                        text("""
                            UPDATE audio_recordings
                            SET status = 'failed'
                            WHERE id = :id
                        """),
                        {"id": recording_id}
                    )
                    await audio_db.commit()
            except Exception as db_err:
                print(f"Could not mark as failed: {db_err}")