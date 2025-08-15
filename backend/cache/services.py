import asyncio
import json
import random
from typing import Any, Dict, Optional
from backend.cache._cache import CAS_LUA, HITS_KEY, TTL_DEFAULT, redis_client
from backend.cache.utils import incr_stat, redis_retry_log
from backend.url_shortener.utils import general_retry
from redis.exceptions import ConnectionError as RedisConnectionError, TimeoutError as RedisTimeoutError
from backend.__init__ import logger




async def update_short_code_cache(code,res,background_tasks):
    key = f"url:{code}"
    payload = {
        "original_url": getattr(res, "original_url"),
        "password": getattr(res, "password"),
        "expiry_date": getattr(res, "expiry_date"),
        "updated_at":getattr(res,"updated_at")
    }  #*chnage here as well to get fileds differently when update only return updated_at 
   
    try:
        ok = await cas_set_cache(key, payload)
        if not ok:
            # Some newer version is already in cache. This is OK.
            pass
    except Exception:
        # schedule retry
        if background_tasks is not None:
            background_tasks.add_task(retry_set_cas, key, payload)
       
async def cas_set_cache(key: str, payload: Dict[str, Any], ttl: int = TTL_DEFAULT) -> bool:
    """
    Returns True if Lua CAS wrote the cache, False if refused because existing version is newer.
    Raises Redis exceptions if Redis unreachable (caller should handle and schedule retry).
    """
    global CAS_SCRIPT_SHA

    if redis_client is None:
        raise RuntimeError("redis_client not initialized")  #* check these it should do something else 

    if CAS_SCRIPT_SHA is None:
        try:
            CAS_SCRIPT_SHA = await general_retry(
                lambda: redis_client.script_load(CAS_LUA),
                retry_exceptions=(RedisConnectionError, RedisTimeoutError),
                on_retry_log=redis_retry_log,
                retries=3,
                base_delay=0.05,
                max_delay=0.5,
            )
        except Exception as exc:
            # Script couldn't be loaded — propagate to caller so they can schedule background retry
            raise

    original_url = payload.get("original_url")
    password = payload.get("password") or ""
    expiry_date = payload.get("expiry_date") or ""
    version_int = int(payload.get("updated_at").timestamp())
    
    # we can add few sync retries before sending to background tasks 
    try:
        return_code = await redis_client.evalsha(
        CAS_SCRIPT_SHA,
        1,
        key,
        str(version_int),
        original_url,
        password,
        expiry_date,
        str(int(ttl)),
        )

        return bool(return_code)
    except Exception as exc:
        # Redis error — propagate to caller so they can schedule background retry
        raise exc


async def retry_set_cas(key: str, payload, ttl: int = TTL_DEFAULT,
                        retries: int = 5, base_delay: float = 0.2):
    for i in range(retries):
        try:
            ok = await cas_set_cache(key, payload, ttl)
            return ok
        except (RedisConnectionError, RedisTimeoutError) as e:
            # backoff with jitter
            delay = min(10.0, base_delay * (2 ** i))
            delay = random.uniform(0, delay)
            logger.warning("retry_set_cas attempt %d failed; sleeping %.2fs: %s", i + 1, delay, e)
            await asyncio.sleep(delay)
        except Exception as e:
            # non-transient or script problem: try a couple more times or give up
            logger.exception("retry_set_cas fatal error: %s", e)
            await asyncio.sleep(min(5.0, base_delay * (2 ** i)))
    # final attempt failed
    return False