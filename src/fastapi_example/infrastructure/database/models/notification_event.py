from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from fastapi_example.domain.entities import (
    NotificationEventStatus,
    NotificationEventType,
)

from .base import Base
from .mixins import ModelWithIDMixin


class NotificationEventModel(ModelWithIDMixin, Base):
    __tablename__ = "notification_events"

    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[NotificationEventType] = mapped_column(
        Enum(NotificationEventType, name="notification_event_type"), nullable=False
    )
    recipient: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[NotificationEventStatus] = mapped_column(
        Enum(NotificationEventStatus, name="notification_event_status"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
