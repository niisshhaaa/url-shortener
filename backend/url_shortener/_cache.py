from asyncio import Lock
import redis.asyncio as redis

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# Optional: a lock to serialize first-time DB fetches per key
_locks: dict[str, Lock] = {}



cache_stats={
    "cache_hits" : 0,
    "cache_misses" : 0,
}


async def cache_clear():
    """Clear the entire cache (useful in tests)."""
    keys = await redis_client.keys("url:*")
    if keys:
        await redis_client.delete(*keys)
