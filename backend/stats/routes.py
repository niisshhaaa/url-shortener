from fastapi import APIRouter
from backend.cache._cache import MISSES_KEY,HITS_KEY,redis_client

stats_router=APIRouter()

@stats_router.get("/cache-stats")
async def get_cache_stats():
    hits=int(await redis_client.get(HITS_KEY) or 0)
    misses=int(await redis_client.get(MISSES_KEY) or 0)
    total=misses+hits
    return {
        "hits": hits,
        "misses": misses,
        "hit_ratio": hits / total if total else None,
    }