from typing import cast
from uuid import UUID

from fastapi_example.application.interfaces.database.repositories.mappers import (
    INotificationEventsRepositoryMapper,
)
from fastapi_example.domain.entities import NotificationEvent
from fastapi_example.infrastructure.database.models import NotificationEventModel


class NotificationEventsRepositoryMapper(INotificationEventsRepositoryMapper):
    def persistence_to_domain(self, model_event: NotificationEventModel) -> NotificationEvent:
        return NotificationEvent(
            id=cast(UUID, model_event.id),
            user_id=cast(UUID | None, model_event.user_id),
            event_type=model_event.event_type,
            recipient=model_event.recipient,
            status=model_event.status,
            created_at=model_event.created_at,
            processed_at=model_event.processed_at,
        )
