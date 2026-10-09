import logging

from fastapi_example.application.interfaces.database import ITransactionManager
from fastapi_example.application.interfaces.database.repositories import (
    INotificationEventsRepository,
)
from fastapi_example.domain.entities import NotificationEvent

from .query import GetNotificationEventsQuery

log = logging.getLogger(__name__)


class GetNotificationEventsHandler:
    def __init__(
        self,
        repository: INotificationEventsRepository,
        transaction_manager: ITransactionManager,
    ) -> None:
        self._repository = repository
        self._transaction_manager = transaction_manager

    async def execute(self, query: GetNotificationEventsQuery) -> list[NotificationEvent]:
        async with self._transaction_manager:
            events = await self._repository.list_notification_events(query.user_id)

        log.info("Notification events received for user ID: %s", query.user_id)
        return events
