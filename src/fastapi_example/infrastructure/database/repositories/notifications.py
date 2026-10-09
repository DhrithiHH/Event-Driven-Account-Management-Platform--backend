from typing import Type
from uuid import UUID

from sqlalchemy import func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_example.application.interfaces.database.repositories import (
    INotificationEventsRepository,
    TCreateNotificationEvent,
)
from fastapi_example.application.interfaces.database.repositories.mappers import (
    INotificationEventsRepositoryMapper,
)
from fastapi_example.domain.entities import NotificationEvent, NotificationEventStatus
from fastapi_example.infrastructure.database.models import NotificationEventModel


class SQLAlchemyNotificationEventsRepository(INotificationEventsRepository):
    def __init__(
        self, session: AsyncSession, mapper: INotificationEventsRepositoryMapper
    ) -> None:
        self._session = session
        self._mapper = mapper

    @property
    def _model(self) -> Type[NotificationEventModel]:
        return NotificationEventModel

    async def create_notification_event(
        self, event: TCreateNotificationEvent
    ) -> NotificationEvent:
        stmt = insert(self._model).values(**event).returning(self._model)
        result = (await self._session.execute(stmt)).scalars().first()
        return self._mapper.persistence_to_domain(result)

    async def get_notification_event(
        self, event_id: UUID, for_update: bool = False
    ) -> NotificationEvent | None:
        stmt = select(self._model).where(self._model.id == event_id)
        if for_update:
            stmt = stmt.with_for_update()
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._mapper.persistence_to_domain(result) if result else None

    async def list_notification_events(self, user_id: UUID) -> list[NotificationEvent]:
        stmt = (
            select(self._model)
            .where(self._model.user_id == user_id)
            .order_by(self._model.created_at.desc())
        )
        result = (await self._session.execute(stmt)).scalars().all()
        return [self._mapper.persistence_to_domain(event) for event in result]

    async def update_status(
        self, event_id: UUID, status: NotificationEventStatus, processed: bool = False
    ) -> NotificationEvent | None:
        values = {"status": status}
        if processed:
            values["processed_at"] = func.now()
        stmt = (
            update(self._model)
            .where(self._model.id == event_id)
            .values(**values)
            .returning(self._model)
        )
        result = (await self._session.execute(stmt)).scalars().first()
        return self._mapper.persistence_to_domain(result) if result else None
