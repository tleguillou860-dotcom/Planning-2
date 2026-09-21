"""Send the daily summary over Telegram via a bot."""
from __future__ import annotations

import requests

# Telegram caps a single message at 4096 characters; split long summaries so
# nothing gets silently truncated.
MAX_MESSAGE_LENGTH = 4000


def _chunk(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


def send_telegram_summary(bot_token: str, chat_id: str, body: str) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for chunk in _chunk(body, MAX_MESSAGE_LENGTH):
        response = requests.post(url, data={"chat_id": chat_id, "text": chunk}, timeout=30)
        response.raise_for_status()
