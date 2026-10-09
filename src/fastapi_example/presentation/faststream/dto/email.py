from uuid import UUID

from fastapi_example.domain.entities import NotificationEventType

from .base import BaseDTO


class EmailNotificationDTO(BaseDTO):
    event_id: UUID
    event_type: NotificationEventType
    recipient: str
    subject: str
    content: str
