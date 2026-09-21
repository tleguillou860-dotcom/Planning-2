"""Daily entry point: sort unread inbox mail into Important/Pub, mark Pub as
read, and send a Telegram summary of the important ones.

Runs from GitHub Actions twice a day (06:00 and 07:00 UTC) to land on 8:00
Europe/Paris time whether or not daylight saving is in effect; this gate
skips the run that doesn't land in the 8:00 window, so the work only
actually happens once.
"""
from __future__ import annotations

import os
import sys
from zoneinfo import ZoneInfo
from datetime import datetime

from anthropic import Anthropic

from .classifier import classify
from .gmail_client import GmailClient
from .summarizer import build_summary
from .telegram import send_telegram_summary

TARGET_HOUR = 8
TIMEZONE = "Europe/Paris"


def _should_run_now() -> bool:
    if os.environ.get("FORCE_RUN") == "1":
        return True
    now = datetime.now(ZoneInfo(TIMEZONE))
    return now.hour == TARGET_HOUR


def run() -> None:
    if not _should_run_now():
        print(f"Pas encore {TARGET_HOUR}h à {TIMEZONE}, on ne fait rien.")
        return

    gmail = GmailClient(
        client_id=os.environ["GMAIL_CLIENT_ID"],
        client_secret=os.environ["GMAIL_CLIENT_SECRET"],
        refresh_token=os.environ["GMAIL_REFRESH_TOKEN"],
    )
    anthropic_client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    messages = gmail.fetch_unread_inbox_messages()
    print(f"{len(messages)} mail(s) non lu(s) trouvé(s) dans la boîte de réception.")

    important_messages = []
    for message in messages:
        result = classify(anthropic_client, message)
        if result.category == "pub":
            gmail.move_to_pub(message.id)
            print(f"[pub] {message.subject!r} ({result.reason})")
        else:
            gmail.move_to_important(message.id)
            important_messages.append(message)
            print(f"[important] {message.subject!r} ({result.reason})")

    summary = build_summary(anthropic_client, important_messages)
    send_telegram_summary(
        bot_token=os.environ["TELEGRAM_BOT_TOKEN"],
        chat_id=os.environ["TELEGRAM_CHAT_ID"],
        body=summary,
    )
    print("Résumé envoyé sur Telegram.")


if __name__ == "__main__":
    try:
        run()
    except KeyError as exc:
        print(f"Variable d'environnement manquante: {exc}", file=sys.stderr)
        sys.exit(1)
