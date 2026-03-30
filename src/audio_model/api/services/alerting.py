import os
import httpx
from datetime import datetime
from dotenv import load_dotenv # type: ignore
from ..models.schemas import DetectionEvent

load_dotenv()

ACCESS_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_ID")
API_VERSION = os.getenv("WHATSAPP_API_VERSION")
VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
RECIPIENT_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")

URL = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"

last_alert_time: datetime | None = None
COOLDOWN_SECONDS = 600

def send_alert(event: DetectionEvent) -> bool:
    global last_alert_time

    if last_alert_time != None:
        elapsed = (datetime.now() - last_alert_time).seconds
        if elapsed < COOLDOWN_SECONDS:
            print(f"Cooldown active - {COOLDOWN_SECONDS - elapsed}s remaining...")
            return False
        
    message = (
        f"Pest Detected on your farm! \n\n"
        f"Confidence: {event.confidence:.2f}\n"
        f"Time      : {event.timestamp.strftime('%H:%M:%S')}\n"
        f"Action    : Check your crops immediately"
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
        if response.status_code == 200:
            last_alert_time = datetime.now()
            print(f"Whatsapp message sent successfully...")
            return True
        else:
            print(f"Alert failed - status {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"Alert failed - {e}")
        return False
