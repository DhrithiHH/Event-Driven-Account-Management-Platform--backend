import logging

from dishka.integrations.faststream import FromDishka
from faststream.kafka import KafkaRouter

from fastapi_example.application.interfaces.database import ITransactionManager
from fastapi_example.application.interfaces.database.repositories import (
    INotificationEventsRepository,
)
from fastapi_example.application.interfaces.services import (
    IEmailNotificationsService,
    TEmailMessage,
)
from fastapi_example.domain.entities import NotificationEventStatus
from fastapi_example.presentation.faststream.dto import EmailNotificationDTO

log = logging.getLogger(__name__)

email_notifications_router = KafkaRouter()


@email_notifications_router.subscriber("email_notifications")
async def email_notifications(
    message: EmailNotificationDTO,
    service: FromDishka[IEmailNotificationsService],
    repository: FromDishka[INotificationEventsRepository],
    transaction_manager: FromDishka[ITransactionManager],
) -> None:
    data = TEmailMessage(**message.model_dump())
    async with transaction_manager:
        event = await repository.get_notification_event(data.event_id, for_update=True)
        if not event:
            log.error("Notification event not found for Kafka message: %s", data.event_id)
            return
        await repository.update_status(data.event_id, NotificationEventStatus.PROCESSING)

    try:
        _, smtp_response = await service.send(data)
    except Exception:
        log.exception("Email delivery failed for notification event: %s", data.event_id)
        async with transaction_manager:
            await repository.update_status(
                data.event_id, NotificationEventStatus.FAILED, processed=True
            )
        return

    log.info(
        "SMTP server accepted notification event %s: %s",
        data.event_id,
        smtp_response,
    )
    async with transaction_manager:
        await repository.update_status(
            data.event_id, NotificationEventStatus.SENT, processed=True
        )
