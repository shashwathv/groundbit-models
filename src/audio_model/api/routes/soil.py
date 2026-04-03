# routes/soil.py

from fastapi import APIRouter, Request
from datetime import datetime, timezone

from ..models.schemas import SoilInput

router = APIRouter()


@router.post("/soil")
async def receive_soil(reading: SoilInput, request: Request):
    """
    Receives soil moisture from ESP32.
    Stores in result_store — included in /status and WhatsApp alerts.
    Dashboard spec: any confirming 200 payload.
    """
    store = request.app.state.store

    store.update_soil(
        moisture=reading.soil_moisture,
        timestamp=datetime.now(timezone.utc),
        temp_c=reading.temp_c
    )

    print(f"Soil reading received: {reading.soil_moisture:.1f}%"
          + (f" {reading.temp_c:.1f}°C" if reading.temp_c else ""))

    return {
        "status":        "received",
        "soil_moisture": round(reading.soil_moisture, 1),
        "temp_c":        reading.temp_c,
        "timestamp":     datetime.now(timezone.utc).isoformat()
    }