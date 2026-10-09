from typing import TypedDict
from uuid import UUID

from fastapi_example.domain.entities import NotificationEventType


class TEmailMessage(TypedDict):
    event_id: UUID
    event_type: NotificationEventType
    recipient: str
    subject: str
    content: str


class IEmailNotificationsProducer:
    async def publish(self, message: TEmailMessage) -> None: ...
