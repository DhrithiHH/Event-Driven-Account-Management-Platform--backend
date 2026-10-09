from dataclasses import dataclass
from uuid import UUID

import aiosmtplib

from fastapi_example.domain.entities import NotificationEventType


@dataclass
class TEmailMessage:
    event_id: UUID
    event_type: NotificationEventType
    recipient: str
    subject: str
    content: str


class IEmailNotificationsService:
    async def enqueue(self, message: TEmailMessage) -> None: ...

    async def send(
        self, message: TEmailMessage
    ) -> tuple[dict[str, aiosmtplib.SMTPResponse], str]: ...
