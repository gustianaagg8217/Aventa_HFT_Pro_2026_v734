"""
Performance utilities for caching and optimization
"""
import functools
import time
from typing import Callable, Any

class TTLCache:
    """Time-To-Live cache for expensive operations"""
    
    def __init__(self, ttl_seconds: float = 1.0):
        self.ttl = ttl_seconds
        self.cache = {}
        self.timestamps = {}
    
    def get(self, key: str) -> Any:
        if key in self.cache:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.cache[key]
            else:
                # Expired
                del self.cache[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value:  Any):
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self):
        self.cache.clear()
        self.timestamps.clear()

def cache_with_ttl(ttl_seconds: float = 1.0):
    """Decorator to cache function results with TTL"""
    cache = TTLCache(ttl_seconds)
    
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name + args
            key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
            
            # Check cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Calculate and cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        return wrapper
    return decorator