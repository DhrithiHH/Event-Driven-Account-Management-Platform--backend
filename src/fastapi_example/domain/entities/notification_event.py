from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class NotificationEventType(StrEnum):
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_UPDATED = "ACCOUNT_UPDATED"
    ACCOUNT_DELETED = "ACCOUNT_DELETED"


class NotificationEventStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"


@dataclass
class NotificationEvent:
    id: UUID
    user_id: UUID | None
    event_type: NotificationEventType
    recipient: str
    status: NotificationEventStatus
    created_at: datetime
    processed_at: datetime | None
