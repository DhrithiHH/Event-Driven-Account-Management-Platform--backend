from unittest.mock import AsyncMock, MagicMock

import pytest
from dishka import make_async_container
from sqlalchemy.ext.asyncio import AsyncEngine

from fastapi_example.infrastructure.di_providers import database as database_provider
from fastapi_example.infrastructure.di_providers.database import DatabaseProvider
from fastapi_example.infrastructure.settings import DatabaseSettings


@pytest.mark.asyncio
async def test_database_engine_is_disposed_when_container_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = MagicMock(spec=AsyncEngine)
    engine.dispose = AsyncMock()
    monkeypatch.setattr(database_provider, "create_sa_engine", lambda _: engine)
    container = make_async_container(
        DatabaseProvider(
            DatabaseSettings(
                host="localhost",
                port=5432,
                username="user",
                password="password",
                database="database",
            )
        )
    )

    assert await container.get(AsyncEngine) is engine

    await container.close()

    engine.dispose.assert_awaited_once()
