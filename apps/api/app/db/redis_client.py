from redis.asyncio import Redis

from app.core.config import settings

# Module-level singleton — same pattern as engine.py
_redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> Redis:
    return _redis_client
