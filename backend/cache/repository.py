from asyncio import Lock
import asyncio
from datetime import date, datetime
import json
from typing import Any, Dict, Optional
from backend.cache._cache import HITS_KEY, MISSES_KEY, TTL_DEFAULT, redis_client,_process_locks
from backend.cache.services import cas_set_cache, retry_set_cas
from backend.cache.utils import  acquire_redis_lock, incr_stat, retry_scode_cache_set,make_cached_obj
from backend.url_shortener.repository import load_url
from db.schema import URL_SHORTENER
from sqlalchemy.ext.asyncio import  AsyncSession


async def utilise_cache(key):
    try:
        cached = await redis_client.hgetall(key)
    except Exception:
        # Redis unavailable
        return None
    if cached:
        try:
            data=parse_cached_hash(cached)
            await incr_stat(HITS_KEY)
        except Exception:
             # corrupted payload: delete it and treat as miss
            try:
                await redis_client.delete(key)
            except Exception:
                pass
            return None
        
        return data

def parse_cached_hash(h: Dict[str, Any]):
 
    orig = h.get("original_url")
    if not orig:
        return None
    pwd = h.get("password") or None
    exp = date.fromisoformat(h["expiry_date"]) if h.get("expiry_date") else None
    
    ver = h.get("version")
    try:
        ver_int = int(ver) if ver is not None else 0
    except Exception:
        ver_int = 0
    return make_cached_obj(orig, pwd, exp, ver_int)

async def cache_load_url(short_code,session:AsyncSession,bg_tasks,ttl:int=3600):
    key = f"url:{short_code}"
    #  Attempt to fetch from Redis
    cached_url=await utilise_cache(key)
    if cached_url:
        return cached_url
    
    redis_lock,acquired=await acquire_redis_lock(key)
    url_obj=None

    if acquired:
        try:
            url_obj=await load_url(short_code,session)
        finally:
            # release lock
            try:
                await redis_lock.release()
            except Exception:
                pass
    
    lock=_process_locks.get(short_code)
    if lock is None:
        lock=Lock()
        _process_locks[short_code]=lock
        
    async with lock:
        cached_url=await utilise_cache(key)
        if cached_url:
            return cached_url
        
        # no cache and we hold the lock → load from DB
        url_obj=await load_url(short_code,session)
    
    await incr_stat(MISSES_KEY)

    if not url_obj:
        return url_obj

    
    version_val = int(url_obj["updated_at"].timestamp())
    
    try:
        ok = await cas_set_cache(key, url_obj, version_val,ttl)
        if not ok:
            # CAS refused because cache has newer -> that's fine, return whatever is in cache (re-read)
            cached_url=await utilise_cache(key)
            if cached_url:
                await incr_stat(HITS_KEY)
                return cached_url
        return url_obj
    except Exception:  #* chnage it to specific errors 
        # Redis error: schedule background retry (if background_tasks given) or create-task
        if bg_tasks is not None:
            bg_tasks.add_task(retry_set_cas, key, url_obj,version_val, ttl)


    
    

    
    


