from unittest.mock import AsyncMock, MagicMock

import pytest
import redis.asyncio as aioredis
from dishka import make_async_container

from fastapi_example.infrastructure.di_providers import cache as cache_provider
from fastapi_example.infrastructure.di_providers.cache import CacheProvider
from fastapi_example.infrastructure.settings import RedisSettings


@pytest.mark.asyncio
async def test_redis_client_is_closed_when_container_closes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = MagicMock(spec=aioredis.Redis)
    client.aclose = AsyncMock()
    monkeypatch.setattr(cache_provider, "create_client", lambda _: client)
    container = make_async_container(
        CacheProvider(RedisSettings(host="localhost", port=6379))
    )

    assert await container.get(aioredis.Redis) is client

    await container.close()

    client.aclose.assert_awaited_once()
