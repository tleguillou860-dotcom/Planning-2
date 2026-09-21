"""Send the daily summary over WhatsApp via Twilio."""
from __future__ import annotations

from twilio.rest import Client

# Twilio caps a single WhatsApp message body; split long summaries so nothing
# gets silently truncated.
MAX_MESSAGE_LENGTH = 1500


def _chunk(text: str, size: int) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


def send_whatsapp_summary(
    account_sid: str,
    auth_token: str,
    from_number: str,
    to_number: str,
    body: str,
) -> None:
    client = Client(account_sid, auth_token)
    for chunk in _chunk(body, MAX_MESSAGE_LENGTH):
        client.messages.create(
            from_=f"whatsapp:{from_number}",
            to=f"whatsapp:{to_number}",
            body=chunk,
        )
