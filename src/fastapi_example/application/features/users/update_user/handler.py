import logging
from dataclasses import asdict
from typing import cast

from fastapi_example.application.exceptions.http_exceptions import (
    ConflictError,
    NotFoundError,
)
from fastapi_example.application.interfaces.database import ITransactionManager
from fastapi_example.application.interfaces.database.repositories import (
    INotificationEventsRepository,
    IUsersRepository,
    TCreateNotificationEvent,
    TUpdateUser,
)
from fastapi_example.application.interfaces.services import (
    IEmailNotificationsService,
    IEmailValidatorService,
    TEmailMessage,
)
from fastapi_example.domain.entities import (
    NotificationEventStatus,
    NotificationEventType,
    User,
)

from .command import UpdateUserCommand

log = logging.getLogger(__name__)


class UpdateUserHandler:
    def __init__(
        self,
        repository: IUsersRepository,
        transaction_manager: ITransactionManager,
        email_validator: IEmailValidatorService,
        email_notifications: IEmailNotificationsService,
        notification_events: INotificationEventsRepository,
    ):
        self._repository = repository
        self._transaction_manager = transaction_manager
        self._email_validator = email_validator
        self._email_notifications = email_notifications
        self._notification_events = notification_events

    async def execute(self, cmd: UpdateUserCommand) -> User:
        async with self._transaction_manager:
            user = await self._repository.get_user(user_id=cmd.user_id, for_update=True)
            if not user:
                log.warning("User does not exist with ID: '%s'", cmd.user_id)
                raise NotFoundError("User not found")

            if (
                cmd.username
                and cmd.username != user.username
                and await self._repository.exists_user(username=cmd.username)
            ):
                log.warning(
                    "User update failed - user already exists with username: '%s'",
                    cmd.username,
                )
                raise ConflictError(
                    f"User already exists with username: {cmd.username}"
                )

            if cmd.email:
                if (cmd.email != user.email) and await self._repository.exists_user(
                    email=cmd.email
                ):
                    log.warning(
                        "User update failed - user already exists with email: '%s'",
                        cmd.email,
                    )
                    raise ConflictError(f"User already exists with email: {cmd.email}")

                await self._email_validator.validate(cast(str, cmd.email))

            raw_data = {
                k: v for k, v in asdict(cmd).items() if v is not None and k != "user_id"
            }
            updated = await self._repository.update_user(
                cmd.user_id, TUpdateUser(**raw_data)
            )
            event = await self._notification_events.create_notification_event(
                TCreateNotificationEvent(
                    user_id=updated.id,
                    event_type=NotificationEventType.ACCOUNT_UPDATED,
                    recipient=updated.email,
                    status=NotificationEventStatus.PENDING,
                )
            )

        await self._email_notifications.enqueue(
            TEmailMessage(
                event_id=event.id,
                event_type=event.event_type,
                recipient=updated.email,
                subject="Account updated",
                content=(
                    f"Hello, {updated.username}!\n\n"
                    "Your account details have been updated."
                ),
            )
        )
        return updated
