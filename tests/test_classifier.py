from unittest.mock import MagicMock

from email_sorter.classifier import classify
from email_sorter.gmail_client import EmailMessage


def _message(**overrides) -> EmailMessage:
    defaults = dict(
        id="1",
        sender_name="Test",
        sender_email="test@example.com",
        subject="Bonjour",
        snippet="Un message",
        has_list_unsubscribe=False,
    )
    defaults.update(overrides)
    return EmailMessage(**defaults)


def test_list_unsubscribe_is_pub_without_calling_llm():
    client = MagicMock()
    message = _message(has_list_unsubscribe=True)

    result = classify(client, message)

    assert result.category == "pub"
    client.messages.create.assert_not_called()


def test_promo_keyword_in_subject_is_pub():
    client = MagicMock()
    message = _message(subject="Soldes : -50% sur tout le site !")

    result = classify(client, message)

    assert result.category == "pub"
    client.messages.create.assert_not_called()


def test_newsletter_sender_is_pub():
    client = MagicMock()
    message = _message(sender_email="newsletter@brand.com")

    result = classify(client, message)

    assert result.category == "pub"
    client.messages.create.assert_not_called()


def test_ambiguous_email_falls_back_to_llm():
    client = MagicMock()
    client.messages.create.return_value = MagicMock(
        content=[MagicMock(text='{"category": "important", "reason": "message personnel"}')]
    )
    message = _message(subject="Réunion demain")

    result = classify(client, message)

    assert result.category == "important"
    client.messages.create.assert_called_once()


def test_llm_failure_defaults_to_important():
    client = MagicMock()
    client.messages.create.return_value = MagicMock(content=[MagicMock(text="pas du json")])
    message = _message(subject="Sujet neutre")

    result = classify(client, message)

    assert result.category == "important"
