from datetime import datetime
from uuid import UUID

from fastapi_example.domain.entities import (
    NotificationEventStatus,
    NotificationEventType,
)

from .base import BaseSchema


class NotificationEventResponseDTO(BaseSchema):
    id: UUID
    event_type: NotificationEventType
    recipient: str
    status: NotificationEventStatus
    created_at: datetime
    processed_at: datetime | None
