"""
עוזר רעות - AI conversation logic.
Handles message processing, conversation history, and LLM calls.
"""

import os
import anthropic

from config import settings
from database import get_history, save_message

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def get_response(phone: str, message: str, sender_name: str = "") -> str:
    """Process a message and return an AI response."""

    # Load conversation history
    history = get_history(phone, limit=settings.MAX_HISTORY)

    # Build messages (exclude system from history list)
    messages = []
    messages.extend(history)
    messages.append({"role": "user", "content": message})

    # Call Anthropic Claude
    response = client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        system=settings.SYSTEM_PROMPT,
        messages=messages,
    )
    reply = response.content[0].text

    # Save conversation
    save_message(phone, "user", message)
    save_message(phone, "assistant", reply)

    return reply
