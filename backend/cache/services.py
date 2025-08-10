
import json
from backend.cache._cache import TTL_DEFAULT, redis_client
from backend.cache.utils import acquire_redis_lock, retry_scode_cache_set


async def update_short_code_cache(code,res,background_tasks):
    key = f"url:{code}"
    redis_lock,acquired=await acquire_redis_lock(key)
    payload = {
        "original_url": getattr(res, "original_url", None),
        "password": getattr(res, "password", None),
        "expiry_date": getattr(res, "expiry_date") if getattr(res, "expiry_date", None) else None,
    }
    payload= json.dumps(payload,default=str)
    if acquired:
        try:
            try:
                await redis_client.set(key, payload, ex=TTL_DEFAULT)
                print("cache set")
            except Exception:
                # schedule retry
                background_tasks.add_task(retry_scode_cache_set, key, payload, TTL_DEFAULT)
        finally:
            try:
                await redis_lock.release()
            except Exception:
                pass
    else:
        # couldn't acquire lock fast: schedule async retry to set cache 
        background_tasks.add_task(retry_scode_cache_set, key, payload, TTL_DEFAULT)