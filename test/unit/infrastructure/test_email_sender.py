from email.message import EmailMessage
from unittest.mock import AsyncMock, MagicMock

import aiosmtplib
import pytest

from fastapi_example.infrastructure.communication.email_communication import EmailSender
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
