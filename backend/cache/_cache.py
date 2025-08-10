from asyncio import Lock
import redis.asyncio as redis ,weakref
from config.config import configSettgs

redis_client = redis.Redis(
    host=configSettgs.REDIS_HOST, port=configSettgs.REDIS_PORT, db=configSettgs.REDIS_DB, 
    decode_responses=True)

# Optional: a lock to serialize first-time DB fetches per key
# _locks: dict[str, Lock] = {}

cache_stats={
    "cache_hits" : 0,
    "cache_misses" : 0,
}

HITS_KEY="cache:stats:hits"
MISSES_KEY="cache:stats:misses"

TTL_DEFAULT=3600

# use a weak dict so locks can be GC'd when not referenced
# Per-process small lock dict to fallback when Redis or lock acquisition fails
_process_locks: "weakref.WeakValueDictionary[str, Lock]" = weakref.WeakValueDictionary()

# Redis lock tuning
REDIS_LOCK_TIMEOUT = 5              # how long the lock auto-expires in Redis (seconds)
REDIS_LOCK_BLOCKING_TIMEOUT = 1     # how long to wait to acquire lock (seconds)

async def configure_redis():
    await redis_client.config_set("maxmemory",configSettgs.REDIS_MAX_MEMORY)
    await redis_client.config_set("maxmemory-policy",configSettgs.REDIS_MEMORY_POLICY)


# for testing purpose
async def cache_clear():
    """Clear the entire cache (useful in tests)."""
    keys = await redis_client.keys()
    if keys:
        await redis_client.delete(*keys)


