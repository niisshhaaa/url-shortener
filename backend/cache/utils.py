import asyncio
from backend.cache._cache import REDIS_LOCK_BLOCKING_TIMEOUT, REDIS_LOCK_TIMEOUT, TTL_DEFAULT, redis_client

async def incr_stat(key: str):
    try:
        await redis_client.incr(key)
    except Exception:
        # fallback: maybe increment in-memory metric or log
        # e.g. metrics.counter.inc('cache_stat_error') if you have metrics
        pass

async def acquire_redis_lock(key):
    redis_lock = redis_client.lock(f"lock:{key}", timeout=REDIS_LOCK_TIMEOUT)
    try:
        acquired = await redis_lock.acquire(blocking=True, blocking_timeout=REDIS_LOCK_BLOCKING_TIMEOUT)
        return redis_lock,acquired
    except Exception:
        acquired = False
        return redis_lock,acquired
    
async def retry_scode_cache_set(key,payload,ex=TTL_DEFAULT,retries=5,base=0.2):
    delay=base
    for i in range(retries):
        try:
            await redis_client.set(key, payload, ex=ex)
            print("cache set")
            return True
        except Exception:
            await asyncio.sleep(delay)
            delay*=2
    return False



