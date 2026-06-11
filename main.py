"""
עוזר רעות - WhatsApp AI Agent
Webhook server that receives messages from Green API and responds using AI.
"""

import time
import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse

from config import settings
from agent import get_response
from database import init_db
import google_services as gs

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("עוזר-רעות")

# Simple deduplication: track recent message IDs
_seen_messages: dict[str, float] = {}
DEDUP_WINDOW = 60  # seconds


def _cleanup_seen():
    """Remove old entries from dedup cache."""
    now = time.time()
    expired = [k for k, v in _seen_messages.items() if now - v > DEDUP_WINDOW]
    for k in expired:
        del _seen_messages[k]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("עוזר רעות מוכן!")
    yield


app = FastAPI(title="עוזר רעות", lifespan=lifespan)


@app.get("/shaked", response_class=HTMLResponse)
async def shaked_game():
    """Serve Shaked's English vocabulary game."""
    import os
    html_path = os.path.join(os.path.dirname(__file__), "shaked-english.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/astro", response_class=HTMLResponse)
async def astro_chart():
    """Serve the AstroIL transit chart app."""
    import os
    html_path = os.path.join(os.path.dirname(__file__), "transit-chart.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/health")
async def health():
    google_connected = gs.get_credentials() is not None
    return {"status": "ok", "agent": "עוזר רעות", "google_connected": google_connected}


@app.get("/auth/google")
async def auth_google():
    """Start Google OAuth flow."""
    try:
        auth_url = gs.get_auth_url()
        return RedirectResponse(url=auth_url)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/oauth/callback")
async def oauth_callback(code: str):
    """Handle Google OAuth callback."""
    try:
        gs.exchange_code(code)
        return {"status": "success", "message": "Google חובר בהצלחה! אפשר לסגור את הדף."}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/webhook/green-api")
async def webhook(request: Request):
    """Handle incoming messages from Green API."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    # Process incoming and outgoing (from device) text messages
    webhook_type = data.get("typeWebhook")
    logger.info(f"Webhook type: {webhook_type}")
    if webhook_type not in ("incomingMessageReceived", "outgoingMessageReceived"):
        return {"ok": True, "skipped": webhook_type}

    message_data = data.get("messageData", {})
    message_type = message_data.get("typeMessage")
    if message_type != "textMessage":
        return {"ok": True, "skipped": message_type}

    # Extract sender and message
    sender_data = data.get("senderData", {})
    chat_id = sender_data.get("chatId", "")
    sender_name = sender_data.get("senderName", "")
    text = message_data.get("textMessageData", {}).get("textMessage", "")

    # For outgoing messages, skip bot's own replies to avoid infinite loop
    if webhook_type == "outgoingMessageReceived":
        sender_id = sender_data.get("sender", "")
        if not sender_id or sender_id == chat_id:
            return {"ok": True, "skipped": "self_reply"}
    message_id = data.get("idMessage", "")

    # Extract phone number from chat_id (remove @c.us)
    phone = chat_id.replace("@c.us", "")

    # Skip group messages (only respond to direct messages)
    if "@g.us" in chat_id:
        return {"ok": True, "skipped": "group_message"}

    # Skip empty messages
    if not text.strip():
        return {"ok": True, "skipped": "empty"}

    # Only respond to messages from the owner's phone number
    if settings.OWNER_PHONE and phone != settings.OWNER_PHONE:
        logger.info(f"Ignoring message from non-owner: {phone}")
        return {"ok": True, "skipped": "not_owner"}

    # Deduplication
    _cleanup_seen()
    if message_id in _seen_messages:
        return {"ok": True, "skipped": "duplicate"}
    _seen_messages[message_id] = time.time()

    logger.info(f"Message from {sender_name} ({phone}): {text[:50]}...")

    # Get AI response
    try:
        reply = get_response(phone, text, sender_name)
    except Exception as e:
        logger.error(f"Agent error: {e}")
        reply = "סליחה, משהו השתבש. נסי שוב בעוד רגע."

    # Send reply via Green API
    try:
        await send_whatsapp_message(chat_id, reply)
        logger.info(f"Reply sent to {phone}: {reply[:50]}...")
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")

    return {"ok": True}


async def send_whatsapp_message(chat_id: str, message: str):
    """Send a text message via Green API."""
    url = (
        f"{settings.GREEN_API_URL}"
        f"/waInstance{settings.GREEN_API_INSTANCE}"
        f"/sendMessage/{settings.GREEN_API_TOKEN}"
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"chatId": chat_id, "message": message},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
