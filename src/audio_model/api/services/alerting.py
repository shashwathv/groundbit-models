import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv # type: ignore
from pathlib import Path
from ..models.schemas import DetectionEvent

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")
API_VERSION = os.getenv("WHATSAPP_API_VERSION")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
RECIPIENT_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")

print(f"TOKEN LOADED: {ACCESS_TOKEN[:10] if ACCESS_TOKEN else 'NONE'}")

URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"

last_alert_time: datetime | None = None
COOLDOWN_SECONDS = 600

def send_alert(event: DetectionEvent) -> bool:
    global last_alert_time

    now = datetime.now(timezone.utc)

    if last_alert_time != None:
        elapsed = (datetime.now(timezone.utc) - last_alert_time).total_seconds()
        if elapsed < COOLDOWN_SECONDS:
            print(f"Cooldown active - {COOLDOWN_SECONDS - elapsed}s remaining...")
            return False
        
    message = (
    f"🚨 *PEST ALERT — Groundbit*\n\n"
    f"A pest has been detected on your farm!\n\n"
    f"📊 *Confidence :* {event.confidence:.2%}\n"
    f"🕐 *Time       :* {event.timestamp.strftime('%d %b %Y, %H:%M:%S')}\n\n"
    f"⚠️ *Action Required*\n"
    f"Check your crops immediately and take necessary measures.\n\n"
    f"_Sent by Groundbit Pest Detection System_"
)

    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json" 
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": RECIPIENT_NUMBER,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = httpx.post(url=URL, json=payload, headers=headers, timeout=10)

        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")

        if response.status_code == 200:
            last_alert_time = now
            print("Whatsapp message sent successfully...")
            return True

        return False

    except Exception as e:
        print(f"Alert failed - {e}")
        return False
