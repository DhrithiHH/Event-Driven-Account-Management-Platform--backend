from collections.abc import AsyncIterator

import redis.asyncio as aioredis
from dishka import Provider, Scope, provide

from fastapi_example.application.interfaces.cache.repositories import (
    IRateLimiterCacheRepository,
)
from fastapi_example.infrastructure import RedisSettings
from fastapi_example.infrastructure.cache import create_client
from fastapi_example.infrastructure.cache.repositories import RateLimiterCacheRepository


class CacheProvider(Provider):
    def __init__(self, cache_settings: RedisSettings, scope=None, component=None):
        super().__init__(scope, component)
        self._cache_settings = cache_settings

    @provide(scope=Scope.APP)
    async def client(self) -> AsyncIterator[aioredis.Redis]:
        client = create_client(self._cache_settings.url)
        try:
            yield client
        finally:
            await client.aclose()


class CacheRepositoriesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def rate_limiter_cache_repository(
        self, redis_client: aioredis.Redis
    ) -> IRateLimiterCacheRepository:
        return RateLimiterCacheRepository(redis_client)
