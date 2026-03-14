from redis.asyncio import Redis

from app.core.config import settings

# Module-level singleton — same pattern as engine.py.
# retry_on_timeout + socket_keepalive guard against transient TCP drops.
# health_check_interval=30 auto-pings the server so stale connections are
# detected and recycled before the next real command fails.
_redis_client: Redis = Redis.from_url(
    settings.redis_url,
    decode_responses=True,
    retry_on_timeout=True,
    socket_keepalive=True,
    health_check_interval=30,
)


async def get_redis() -> Redis:
    return _redis_client
