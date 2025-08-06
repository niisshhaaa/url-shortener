from asyncio import Lock
import redis.asyncio as redis
from config.config import configSettgs

redis_client = redis.Redis(
    host=configSettgs.REDIS_HOST, port=configSettgs.REDIS_PORT, db=configSettgs.REDIS_DB, 
    decode_responses=True)

# Optional: a lock to serialize first-time DB fetches per key
_locks: dict[str, Lock] = {}

cache_stats={
    "cache_hits" : 0,
    "cache_misses" : 0,
}

async def configure_redis():
    await redis_client.config_set("maxmemory",configSettgs.REDIS_MAX_MEMORY)
    await redis_client.config_set("maxmemory-policy",configSettgs.REDIS_MEMORY_POLICY)


# for testing purpose
async def cache_clear():
    """Clear the entire cache (useful in tests)."""
    keys = await redis_client.keys("url:*")
    if keys:
        await redis_client.delete(*keys)


