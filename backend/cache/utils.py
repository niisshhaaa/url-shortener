import asyncio
from datetime import date
from typing import Optional
from backend.cache._cache import REDIS_LOCK_BLOCKING_TIMEOUT, REDIS_LOCK_TIMEOUT, TTL_DEFAULT, redis_client
from backend.__init__ import logger
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError

# ---- Small typed container to return cached rows ----
def make_cached_obj(original_url: str, password: Optional[str], expiry_date: Optional[date], version: int):
    return {"original_url":original_url,"password":password,"expiry_date":expiry_date,"version":version}

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
        # try a single acquire; if Redis error, fall back to not-acquired
        acquired = await redis_lock.acquire(blocking=True, blocking_timeout=REDIS_LOCK_BLOCKING_TIMEOUT)
        return redis_lock, acquired
    except (RedisConnectionError, RedisTimeoutError):
        # Redis unavailable: return lock object and False so in-process lock path runs
        return redis_lock, False
    except Exception:
        return redis_lock, False
    

async def lock_release(redis_lock):
    try:
        await redis_lock.release()
    except Exception:
        pass

def redis_retry_log(attempt, retries, delay, exc):
    logger.warning("Redis retry %d/%d after %.3fs due to %s: %s", attempt, retries, delay, type(exc).__name__, exc)




