from dishka import Provider, Scope, provide

from fastapi_example.application.features.notifications.get_events import (
    GetNotificationEventsHandler,
)
from fastapi_example.application.interfaces.database import ITransactionManager
from fastapi_example.application.interfaces.database.repositories import (
    INotificationEventsRepository,
)


class NotificationsFeaturesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_notification_events_handler(
        self,
        repository: INotificationEventsRepository,
        transaction_manager: ITransactionManager,
    ) -> GetNotificationEventsHandler:
        return GetNotificationEventsHandler(repository, transaction_manager)
