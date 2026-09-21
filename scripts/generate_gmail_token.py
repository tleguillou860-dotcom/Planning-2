"""One-time local helper: run this on your own machine (not in CI) to get a
Gmail OAuth refresh token, then paste it into the GMAIL_REFRESH_TOKEN GitHub
secret. Requires a Google Cloud OAuth client (Desktop app) — see README.md.
"""
from __future__ import annotations

import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from email_sorter.gmail_client import SCOPES


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/generate_gmail_token.py path/to/client_secret.json")
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES)
    credentials = flow.run_local_server(port=0)

    print("\nAjoute ce refresh token dans le secret GitHub GMAIL_REFRESH_TOKEN :\n")
    print(credentials.refresh_token)


if __name__ == "__main__":
    main()
