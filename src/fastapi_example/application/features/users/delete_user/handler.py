import logging

from fastapi_example.application.exceptions.http_exceptions import (
    ForbiddenError,
    NotFoundError,
)
from fastapi_example.application.interfaces.database import ITransactionManager
from fastapi_example.application.interfaces.database.repositories import (
    INotificationEventsRepository,
    IUsersRepository,
    TCreateNotificationEvent,
)
from fastapi_example.application.interfaces.security import IHasher
from fastapi_example.application.interfaces.services import (
    IEmailNotificationsService,
    TEmailMessage,
)
from fastapi_example.domain.entities import (
    NotificationEventStatus,
    NotificationEventType,
    User,
)

from .command import DeleteUserCommand

log = logging.getLogger(__name__)


class DeleteUserHandler:
    def __init__(
        self,
        repository: IUsersRepository,
        hasher: IHasher,
        transaction_manager: ITransactionManager,
        email_notifications: IEmailNotificationsService,
        notification_events: INotificationEventsRepository,
    ):
        self._repository = repository
        self._hasher = hasher
        self._transaction_manager = transaction_manager
        self._email_notifications = email_notifications
        self._notification_events = notification_events

    async def execute(self, cmd: DeleteUserCommand) -> User:
        async with self._transaction_manager:
            user = await self._repository.get_user(user_id=cmd.user_id, for_update=True)
            if not user:
                log.warning("User does not exist with ID: '%s'", cmd.user_id)
                raise NotFoundError("User not found")

            if not self._hasher.verify_password(cmd.password, user.password):
                log.warning(
                    "User deletion failed - incorrect password confirmation for user ID: '%s'",
                    cmd.user_id,
                )
                raise ForbiddenError("Incorrect password confirmation")

            event = await self._notification_events.create_notification_event(
                TCreateNotificationEvent(
                    user_id=user.id,
                    event_type=NotificationEventType.ACCOUNT_DELETED,
                    recipient=user.email,
                    status=NotificationEventStatus.PENDING,
                )
            )
            result = await self._repository.delete_user(user_id=cmd.user_id)

        await self._email_notifications.enqueue(
            TEmailMessage(
                event_id=event.id,
                event_type=event.event_type,
                recipient=result.email,
                subject="Account deleted",
                content=(
                    f"Hello, {result.username}!\n\nYour account has been deleted."
                ),
            )
        )
        log.info("User deleted with ID: %s", result.id)
        return result
