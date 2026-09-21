from unittest.mock import MagicMock, patch

from email_sorter.telegram import send_telegram_summary


@patch("email_sorter.telegram.requests.post")
def test_short_summary_sent_as_single_message(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())

    send_telegram_summary("bot-token", "12345", "Résumé court")

    mock_post.assert_called_once_with(
        "https://api.telegram.org/botbot-token/sendMessage",
        data={"chat_id": "12345", "text": "Résumé court"},
        timeout=30,
    )


@patch("email_sorter.telegram.requests.post")
def test_long_summary_is_split_into_chunks(mock_post):
    mock_post.return_value = MagicMock(raise_for_status=MagicMock())
    long_body = "x" * 8500

    send_telegram_summary("bot-token", "12345", long_body)

    assert mock_post.call_count == 3
