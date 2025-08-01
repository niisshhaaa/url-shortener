_cache_urls={}

cache_stats={
    "cache_hits" : 0,
    "cache_misses" : 0,
}


def cache_clear():
    """Clear the entire cache (useful in tests)."""
    _cache_urls.clear()