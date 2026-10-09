from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from fastapi_example.domain.entities import (
    NotificationEvent,
    NotificationEventStatus,
    NotificationEventType,
)
from fastapi_example.presentation.faststream.consumers.email_notifications import (
    email_notifications,
)
from fastapi_example.presentation.faststream.dto import EmailNotificationDTO


def make_event(event_id):
    return NotificationEvent(
        id=event_id,
        user_id=uuid4(),
        event_type=NotificationEventType.ACCOUNT_UPDATED,
        recipient="user@example.com",
        status=NotificationEventStatus.PENDING,
        created_at=datetime.now(UTC),
        processed_at=None,
    )


@pytest.mark.asyncio
async def test_consumer_marks_event_sent_after_successful_email(
    mock_notification_events, mock_transaction_manager, mock_email_notifications
) -> None:
    event_id = uuid4()
    mock_notification_events.get_notification_event = AsyncMock(
        return_value=make_event(event_id)
    )
    message = EmailNotificationDTO(
        event_id=event_id,
        event_type=NotificationEventType.ACCOUNT_UPDATED,
        recipient="user@example.com",
        subject="Account updated",
        content="Your account details have been updated.",
    )

    await email_notifications(
        message,
        mock_email_notifications,
        mock_notification_events,
        mock_transaction_manager,
    )

    mock_notification_events.get_notification_event.assert_awaited_once_with(
        event_id, for_update=True
    )
    assert mock_notification_events.update_status.await_args_list[0].args == (
        event_id,
        NotificationEventStatus.PROCESSING,
    )
    assert mock_notification_events.update_status.await_args_list[1].args == (
        event_id,
        NotificationEventStatus.SENT,
    )
    assert mock_notification_events.update_status.await_args_list[1].kwargs == {
        "processed": True
    }


@pytest.mark.asyncio
async def test_consumer_marks_event_failed_when_email_delivery_raises(
    mock_notification_events, mock_transaction_manager, mock_email_notifications
) -> None:
    event_id = uuid4()
    mock_notification_events.get_notification_event = AsyncMock(
        return_value=make_event(event_id)
    )
    mock_email_notifications.send = AsyncMock(side_effect=RuntimeError("SMTP down"))
    message = EmailNotificationDTO(
        event_id=event_id,
        event_type=NotificationEventType.ACCOUNT_UPDATED,
        recipient="user@example.com",
        subject="Account updated",
        content="Your account details have been updated.",
    )

    await email_notifications(
        message,
        mock_email_notifications,
        mock_notification_events,
        mock_transaction_manager,
    )

    assert mock_notification_events.update_status.await_args_list[0].args == (
        event_id,
        NotificationEventStatus.PROCESSING,
    )
    assert mock_notification_events.update_status.await_args_list[1].args == (
        event_id,
        NotificationEventStatus.FAILED,
    )
    assert mock_notification_events.update_status.await_args_list[1].kwargs == {
        "processed": True
    }
