from typing import Protocol, TypeVar

from fastapi_example.domain.entities import NotificationEvent


PersistenceModel = TypeVar("PersistenceModel", contravariant=True)


class INotificationEventsRepositoryMapper(Protocol[PersistenceModel]):
    def persistence_to_domain(
        self, persistence_event: PersistenceModel
    ) -> NotificationEvent: ...
