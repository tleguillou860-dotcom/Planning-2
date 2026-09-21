from unittest.mock import MagicMock

from email_sorter.summarizer import build_summary


def test_no_important_messages_returns_placeholder():
    client = MagicMock()

    summary = build_summary(client, [])

    assert summary == "Aucun mail important ce matin."
    client.messages.create.assert_not_called()


def test_builds_summary_from_messages():
    from email_sorter.gmail_client import EmailMessage

    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="- Alice: RDV confirmé demain 10h")]
    )
    messages = [
        EmailMessage(
            id="1",
            sender_name="Alice",
            sender_email="alice@example.com",
            subject="RDV",
            snippet="Confirmation du rendez-vous",
            has_list_unsubscribe=False,
        )
    ]

    summary = build_summary(client, messages)

    assert "1 mail important" in summary
    assert "Alice" in summary
