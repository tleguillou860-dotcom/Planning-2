from unittest.mock import MagicMock, patch

from email_sorter.whatsapp import send_whatsapp_summary


@patch("email_sorter.whatsapp.Client")
def test_short_summary_sent_as_single_message(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client

    send_whatsapp_summary("sid", "token", "+1000", "+2000", "Résumé court")

    mock_client.messages.create.assert_called_once_with(
        from_="whatsapp:+1000", to="whatsapp:+2000", body="Résumé court"
    )


@patch("email_sorter.whatsapp.Client")
def test_long_summary_is_split_into_chunks(mock_client_cls):
    mock_client = MagicMock()
    mock_client_cls.return_value = mock_client
    long_body = "x" * 3200

    send_whatsapp_summary("sid", "token", "+1000", "+2000", long_body)

    assert mock_client.messages.create.call_count == 3
