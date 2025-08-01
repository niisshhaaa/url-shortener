_cache_urls={}
def cache_clear():
    """Clear the entire cache (useful in tests)."""
    _cache_urls.clear()