# services/alerting.py

import os
import httpx
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from ..models.schemas import DetectionEvent, SoilReading

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

# ── Credentials ────────────────────────────────────────────────────
ACCESS_TOKEN     = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID  = os.getenv("WHATSAPP_PHONE_ID")
API_VERSION      = os.getenv("WHATSAPP_API_VERSION", "v19.0")
RECIPIENT_NUMBERS = [
    n.strip()
    for n in os.getenv("RECIPIENT_NUMBERS", os.getenv("RECIPIENT_PHONE_NUMBER", "")).split(",")
    if n.strip()
]

URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"

last_alert_time: datetime | None = None
COOLDOWN_SECONDS = 600   # 10 minutes — set to 30 for testing


def send_alert(event: DetectionEvent, soil: SoilReading | None = None) -> bool:
    global last_alert_time

    # ── Cooldown check ─────────────────────────────────────────────
    if last_alert_time is not None:
        elapsed = (datetime.now() - last_alert_time).seconds
        if elapsed < COOLDOWN_SECONDS:
            print(f"Cooldown active — {COOLDOWN_SECONDS - elapsed}s remaining")
            return False

    # ── Soil moisture line ─────────────────────────────────────────
    soil_line = ""
    if soil is not None:
        if soil.moisture_pct < 30:
            soil_status = "Low — consider irrigation"
        elif soil.moisture_pct < 70:
            soil_status = "Normal"
        else:
            soil_status = "High"
        soil_line = f"💧 *Soil Moisture :* {soil.moisture_pct:.1f}% ({soil_status})\n"
        if soil.temp_c is not None:
            soil_line += f"🌡️ *Soil Temp     :* {soil.temp_c:.1f}°C\n"

    # ── Build message ──────────────────────────────────────────────
    message = (
        f"🚨 *PEST ALERT — Groundbit*\n\n"
        f"A pest has been detected on your farm!\n\n"
        f"📊 *Confidence    :* {event.confidence * 100:.1f}%\n"
        f"🕐 *Time          :* {event.timestamp.strftime('%d %b %Y, %H:%M:%S')} UTC\n"
        f"{soil_line}"
        f"\n⚠️ *Action Required*\n"
        f"Check your crops immediately and take necessary measures.\n\n"
        f"_Sent by Groundbit Pest Detection System_"
    )

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type":  "application/json"
    }

    # ── Send to all recipients ─────────────────────────────────────
    try:
        all_sent = True
        for number in RECIPIENT_NUMBERS:
            payload = {
                "messaging_product": "whatsapp",
                "to":   number,
                "type": "text",
                "text": {"body": message}
            }
            response = httpx.post(URL, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"WhatsApp alert sent to {number}")
            else:
                print(f"Alert failed for {number} — {response.status_code}: {response.text}")
                all_sent = False

        if all_sent:
            last_alert_time = datetime.now()
            return True
        return False

    except Exception as e:
        print(f"Alert failed — {e}")
        return False