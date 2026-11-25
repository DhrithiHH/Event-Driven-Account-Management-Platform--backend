import redis.asyncio as aioredis


def create_client(url: str) -> aioredis.Redis:
    if url.startswith("rediss://"):
        return aioredis.from_url(url, ssl_cert_reqs="none")
    return aioredis.from_url(url)
