import asyncio
import logging
import aiosmtplib
from email.message import EmailMessage

from fastapi_example.application.interfaces.communication import IEmailSender
from fastapi_example.infrastructure.settings import SMTPSettings

log = logging.getLogger(__name__)

_CONNECTION_ERRORS = (
    aiosmtplib.SMTPConnectError,
    aiosmtplib.SMTPConnectTimeoutError,
    aiosmtplib.SMTPReadTimeoutError,
    aiosmtplib.SMTPServerDisconnected,
    aiosmtplib.SMTPTimeoutError,
    OSError,
)


class EmailSender(IEmailSender):
    def __init__(self, client: aiosmtplib.SMTP, settings: SMTPSettings):
        self._client = client
        self._settings = settings
        self._send_lock = asyncio.Lock()

    async def send_email(
        self, message: EmailMessage
    ) -> tuple[dict[str, aiosmtplib.SMTPResponse], str]:
        async with self._send_lock:
            await self._ensure_connection()
            try:
                return await self._client.send_message(message)
            except _CONNECTION_ERRORS:
                # The message may have reached the SMTP server before the
                # transport error, so do not retry it. Reset the client for
                # the next notification and let the caller mark this one failed.
                self._client.close()
                raise

    async def _ensure_connection(self) -> None:
        if self._client.is_connected:
            try:
                await self._client.noop()
                return
            except _CONNECTION_ERRORS:
                log.warning("SMTP transport is stale; reconnecting before send")
                self._client.close()

        await self._client.connect()
        if self._settings.username and self._settings.password:
            await self._client.login(
                self._settings.username, self._settings.password
            )
