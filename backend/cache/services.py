import asyncio
import json
from typing import Any, Dict, Optional
from backend.cache._cache import CAS_LUA, HITS_KEY, TTL_DEFAULT, redis_client
from backend.cache.utils import incr_stat

CAS_SCRIPT_SHA: Optional[str] = None


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
        # best-effort: try to load script now
        CAS_SCRIPT_SHA = await redis_client.script_load(CAS_LUA)

    original_url = payload.get("original_url")
    password = payload.get("password") or ""
    expiry_date = payload.get("expiry_date") or ""
    version_int = int(payload.get("updated_at").timestamp())

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


async def retry_set_cas(key: str, payload, ttl: int = TTL_DEFAULT,
                        retries: int = 5, base_delay: float = 0.2):
    for i in range(retries):
        try:
            ok = await cas_set_cache(key, payload, ttl)
            return ok
        except Exception:
            await asyncio.sleep(base_delay * (2 ** i))
    # final attempt failed
    return False