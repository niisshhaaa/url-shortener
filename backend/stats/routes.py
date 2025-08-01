from fastapi import APIRouter
from backend.url_shortener._cache import cache_stats

stats_router=APIRouter()

@stats_router.get("/cache-stats")
def get_cache_stats():
    total=cache_stats["cache_hits"]+cache_stats["cache_misses"]
    return {
        "hits": cache_stats["cache_hits"],
        "misses": cache_stats["cache_misses"],
        "hit_ratio": cache_stats["cache_hits"] / total if total else None,
    }