import redis.asyncio as aioredis
from loguru import logger
from redis.asyncio import Redis

from ...core.settings import settings
from ...core.utils.retry import with_retry

_redis_client: Redis | None = None


def get_redis() -> Redis:
    if _redis_client is None:
        raise RuntimeError("Redis client is not initialized")
    return _redis_client


def create_redis_client() -> Redis:
    return aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=settings.REDIS_DECODE_RESPONSES,
        socket_connect_timeout=settings.REDIS_SOCKET_CONNECT_TIMEOUT,
        socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
        retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )


@with_retry(max_attempts=3, base_delay=1.0)
async def verify_redis_connection() -> None:
    global _redis_client
    _redis_client = create_redis_client()
    await _redis_client.ping()  # type: ignore
    logger.info("Redis connection verified")


async def close_redis_connection() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
