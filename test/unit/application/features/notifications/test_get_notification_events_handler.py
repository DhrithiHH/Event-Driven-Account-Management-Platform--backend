from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from fastapi_example.application.features.notifications.get_events import (
    GetNotificationEventsHandler,
    GetNotificationEventsQuery,
)


@pytest.mark.asyncio
async def test_get_notification_events_scopes_query_to_authenticated_user(
    mock_notification_events, mock_transaction_manager
) -> None:
    user_id = uuid4()
    mock_notification_events.list_notification_events = AsyncMock(return_value=[])
    handler = GetNotificationEventsHandler(
        mock_notification_events, mock_transaction_manager
    )

    result = await handler.execute(GetNotificationEventsQuery(user_id=user_id))

    assert result == []
    mock_notification_events.list_notification_events.assert_awaited_once_with(user_id)
