from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from fastapi_example.application.interfaces.services import TEmailMessage
from fastapi_example.application.services.email_notifications import (
    EmailNotificationsService,
)
from fastapi_example.application.settings import EmailNotificationSettings
from fastapi_example.domain.entities import NotificationEventType


@pytest.mark.asyncio
async def test_enqueue_publishes_the_persisted_notification_event_id() -> None:
    producer = AsyncMock()
    service = EmailNotificationsService(
        producer, MagicMock(), EmailNotificationSettings(sender="root@localhost")
    )
    event_id = uuid4()
    message = TEmailMessage(
        event_id=event_id,
        event_type=NotificationEventType.ACCOUNT_CREATED,
        recipient="user@example.com",
        subject="Account created",
        content="Your account has been created successfully.",
    )

    await service.enqueue(message)

    producer.publish.assert_awaited_once()
    published = producer.publish.call_args.kwargs["message"]
    assert published["event_id"] == event_id
    assert published["event_type"] == NotificationEventType.ACCOUNT_CREATED
