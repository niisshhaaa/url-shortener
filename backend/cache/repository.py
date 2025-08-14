from asyncio import Lock
from datetime import date
import json
from backend.cache._cache import HITS_KEY, MISSES_KEY, TTL_DEFAULT, redis_client,_process_locks
from backend.cache.utils import acquire_redis_lock, incr_stat,retry_scode_cache_set
from backend.url_shortener.repository import load_url
from sqlalchemy.ext.asyncio import  AsyncSession


async def utilise_cache(key):
    try:
        cached = await redis_client.get(key)
    except Exception:
        # Redis unavailable
        return None
    if cached:
        try:
            data=json.loads(cached)
        except Exception as e:
             # corrupted payload: delete it and treat as miss
            try:
                await redis_client.delete(key)
            except Exception:
                pass
            return None
        
        await incr_stat(HITS_KEY)
        
        if data["expiry_date"]:
            data["expiry_date"]= date.fromisoformat(data["expiry_date"])
        return data
        # return make_cached_obj(original_url, password, expiry_date)
    return None


async def loaddb_nset_cache(key,short_code,session,bg_tasks,ttl):
        cached_url=await utilise_cache(key)
        if cached_url:
            return cached_url
        
        # no cache and we hold the lock → load from DB
        await incr_stat(MISSES_KEY)
        url_obj=await load_url(short_code,session)

        if url_obj:
            
            payload = {
                "original_url": url_obj["original_url"],
                "password": url_obj["password"],
                "expiry_date": url_obj["expiry_date"]
            }
            payload=json.dumps(payload,default=str)
            try:
                await redis_client.set(key, payload, ex=ttl)
            except Exception:
                bg_tasks.add_task(retry_scode_cache_set, key, payload, TTL_DEFAULT)
            
        return url_obj 

async def cache_load_url(short_code,session:AsyncSession,bg_tasks,ttl:int=3600):
    key = f"url:{short_code}"
    #  Attempt to fetch from Redis
    cached_url=await utilise_cache(key)
    if cached_url:
        return cached_url
    
    # Cache miss : Only one coroutine should hit the DB for a cache-miss
    # in case if more than 1 request reached at this point to fetch from db .lock one request and complete it fully and then proceed one by one .
    # get or create per-process lock 

    redis_lock,acquired=await acquire_redis_lock(key)
    
    if acquired:
        url_obj=None
        try:
            url_obj=await loaddb_nset_cache(key,short_code,session,bg_tasks,ttl)
        finally:
            # release lock
            try:
                await redis_lock.release()
            except Exception:
                pass
        return url_obj
    
    
    lock=_process_locks.get(short_code)
    if lock is None:
        lock=Lock()
        _process_locks[short_code]=lock
        
    async with lock:
        cached_url=await utilise_cache(key)
        if cached_url:
            return cached_url
        
        # no cache and we hold the lock → load from DB
        await incr_stat(MISSES_KEY)
        url_obj=await load_url(short_code,session)

        if url_obj:
            
            payload = {
                "original_url": url_obj.original_url,
                "password": url_obj.password,
                "expiry_date": url_obj.expiry_date if url_obj.expiry_date else None
            }
            try:
                await redis_client.set(key, json.dumps(payload,default=str), ex=ttl)
            except Exception:
                bg_tasks.add_task(retry_scode_cache_set, key, payload, TTL_DEFAULT)
            
        return url_obj
    


