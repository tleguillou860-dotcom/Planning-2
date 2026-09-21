"""Thin wrapper around the Gmail API: fetching unread inbox mail and
moving messages between the INBOX and the Important/Pub labels."""
from __future__ import annotations

import base64
from dataclasses import dataclass
from email.utils import parseaddr

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]

IMPORTANT_LABEL = "Important"
PUB_LABEL = "Pub"


@dataclass
class EmailMessage:
    id: str
    sender_name: str
    sender_email: str
    subject: str
    snippet: str
    has_list_unsubscribe: bool


class GmailClient:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )
        self.service = build("gmail", "v1", credentials=creds)
        self._label_ids: dict[str, str] = {}

    def _get_or_create_label(self, name: str) -> str:
        if name in self._label_ids:
            return self._label_ids[name]

        labels = self.service.users().labels().list(userId="me").execute().get("labels", [])
        for label in labels:
            if label["name"] == name:
                self._label_ids[name] = label["id"]
                return label["id"]

        created = (
            self.service.users()
            .labels()
            .create(
                userId="me",
                body={
                    "name": name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            .execute()
        )
        self._label_ids[name] = created["id"]
        return created["id"]

    def fetch_unread_inbox_messages(self) -> list[EmailMessage]:
        results = []
        request = (
            self.service.users()
            .messages()
            .list(userId="me", labelIds=["INBOX", "UNREAD"], maxResults=100)
        )
        response = request.execute()
        message_refs = response.get("messages", [])

        for ref in message_refs:
            msg = (
                self.service.users()
                .messages()
                .get(userId="me", id=ref["id"], format="metadata",
                     metadataHeaders=["From", "Subject", "List-Unsubscribe"])
                .execute()
            )
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            sender_name, sender_email = parseaddr(headers.get("From", ""))
            results.append(
                EmailMessage(
                    id=msg["id"],
                    sender_name=sender_name or sender_email,
                    sender_email=sender_email,
                    subject=headers.get("Subject", "(sans objet)"),
                    snippet=msg.get("snippet", ""),
                    has_list_unsubscribe="List-Unsubscribe" in headers,
                )
            )
        return results

    def move_to_important(self, message_id: str) -> None:
        self._move(message_id, add=IMPORTANT_LABEL, mark_read=False)

    def move_to_pub(self, message_id: str) -> None:
        self._move(message_id, add=PUB_LABEL, mark_read=True)

    def _move(self, message_id: str, add: str, mark_read: bool) -> None:
        label_id = self._get_or_create_label(add)
        remove_labels = ["INBOX"]
        if mark_read:
            remove_labels.append("UNREAD")
        self.service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"addLabelIds": [label_id], "removeLabelIds": remove_labels},
        ).execute()
