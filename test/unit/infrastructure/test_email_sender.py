from email.message import EmailMessage
from unittest.mock import AsyncMock, MagicMock, Mock

import aiosmtplib
import pytest

from fastapi_example.infrastructure.communication.email_communication import EmailSender
from fastapi_example.infrastructure.communication.email_communication.client import (
    create_smtp_client,
)
from fastapi_example.infrastructure.settings import SMTPSettings


def make_sender(client: MagicMock) -> EmailSender:
    return EmailSender(
        client,
        SMTPSettings(
            host="maildev",
            port=1025,
            username="smtp-user",
            password="smtp-password",
        ),
    )


def make_message() -> EmailMessage:
    message = EmailMessage()
    message["To"] = "user@example.com"
    message.set_content("Test message")
    return message


def test_smtp_client_configures_starttls(monkeypatch: pytest.MonkeyPatch) -> None:
    smtp_factory = Mock()
    monkeypatch.setattr(
        "fastapi_example.infrastructure.communication.email_communication.client.aiosmtplib.SMTP",
        smtp_factory,
    )
    settings = SMTPSettings(host="smtp-relay.brevo.com", port=2525, starttls=True)

    create_smtp_client(settings)

    smtp_factory.assert_called_once_with(
        hostname="smtp-relay.brevo.com",
        port=2525,
        use_tls=False,
        start_tls=True,
    )


@pytest.mark.asyncio
async def test_sender_reconnects_stale_transport_before_sending() -> None:
    client = MagicMock()
    client.is_connected = True
    client.noop = AsyncMock(
        side_effect=aiosmtplib.SMTPServerDisconnected("Server not connected")
    )
    client.connect = AsyncMock()
    client.login = AsyncMock()
    client.send_message = AsyncMock(return_value=({}, "queued"))
    sender = make_sender(client)

    result = await sender.send_email(make_message())

    assert result == ({}, "queued")
    client.noop.assert_awaited_once()
    client.close.assert_called_once()
    client.connect.assert_awaited_once()
    client.login.assert_awaited_once_with("smtp-user", "smtp-password")
    client.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_sender_connects_before_sending_when_transport_is_disconnected() -> None:
    client = MagicMock()
    client.is_connected = False
    client.connect = AsyncMock()
    client.login = AsyncMock()
    client.send_message = AsyncMock(return_value=({}, "queued"))
    sender = make_sender(client)

    await sender.send_email(make_message())

    client.noop.assert_not_called()
    client.connect.assert_awaited_once()
    client.login.assert_awaited_once_with("smtp-user", "smtp-password")
    client.send_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_sender_resets_transport_without_retrying_a_failed_send() -> None:
    client = MagicMock()
    client.is_connected = True
    client.noop = AsyncMock(return_value=None)
    client.send_message = AsyncMock(
        side_effect=aiosmtplib.SMTPServerDisconnected("Server not connected")
    )
    sender = make_sender(client)

    with pytest.raises(aiosmtplib.SMTPServerDisconnected):
        await sender.send_email(make_message())

    client.send_message.assert_awaited_once()
    client.close.assert_called_once()
    client.connect.assert_not_called()


@pytest.mark.asyncio
async def test_sender_raises_when_smtp_refuses_a_recipient() -> None:
    client = MagicMock()
    client.is_connected = True
    client.noop = AsyncMock(return_value=None)
    refused_response = MagicMock()
    refused_response.code = 550
    refused_response.message = "Mailbox unavailable"
    client.send_message = AsyncMock(
        return_value=({"user@example.com": refused_response}, "rejected")
    )
    sender = make_sender(client)

    with pytest.raises(aiosmtplib.SMTPRecipientsRefused) as exc_info:
        await sender.send_email(make_message())

    assert exc_info.value.recipients[0].recipient == "user@example.com"
