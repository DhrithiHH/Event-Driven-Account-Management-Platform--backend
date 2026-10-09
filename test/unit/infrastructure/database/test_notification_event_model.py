from fastapi_example.infrastructure.database.models import NotificationEventModel


def test_notification_event_model_has_expected_columns_and_foreign_key() -> None:
    table = NotificationEventModel.__table__

    assert table.name == "notification_events"
    assert {"id", "user_id", "event_type", "recipient", "status", "created_at", "processed_at"} <= set(table.c.keys())
    assert table.c.user_id.nullable is True
    foreign_key = next(iter(table.c.user_id.foreign_keys))
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "SET NULL"
    assert {"ix_notification_events_user_id", "ix_notification_events_created_at"} <= {
        index.name for index in table.indexes
    }
