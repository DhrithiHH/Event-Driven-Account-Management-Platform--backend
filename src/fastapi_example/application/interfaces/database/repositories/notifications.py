from typing import Protocol, TypedDict
from uuid import UUID

from fastapi_example.domain.entities import (
    NotificationEvent,
    NotificationEventStatus,
    NotificationEventType,
)


class TCreateNotificationEvent(TypedDict):
    user_id: UUID
    event_type: NotificationEventType
    recipient: str
    status: NotificationEventStatus


class INotificationEventsRepository(Protocol):
    async def create_notification_event(
        self, event: TCreateNotificationEvent
    ) -> NotificationEvent: ...

    async def get_notification_event(
        self, event_id: UUID, for_update: bool = False
    ) -> NotificationEvent | None: ...

    async def list_notification_events(self, user_id: UUID) -> list[NotificationEvent]: ...

    async def update_status(
        self, event_id: UUID, status: NotificationEventStatus, processed: bool = False
    ) -> NotificationEvent | None: ...
