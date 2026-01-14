"""
Thread Safety Utilities for Aventa HFT Pro 2026
Ensures safe GUI updates from background threads
"""

import threading
from functools import wraps
from time import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ThreadSafeGUI: 
    """Wrapper for thread-safe GUI updates"""
    
    def __init__(self, root):
        self.root = root
        self._pending_updates = []
        self._lock = threading.Lock()
    
    def schedule_update(self, callback, *args, **kwargs):
        """Schedule a GUI update from any thread"""
        def safe_callback():
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"GUI update error: {e}")
        
        self.root.after(0, safe_callback)
    
    def batch_update(self, updates):
        """Batch multiple GUI updates together"""
        def apply_batch():
            for callback, args, kwargs in updates:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Batch update error: {e}")
        
        self.root.after(0, apply_batch)


class RateLimiter:
    """Rate limiter for logging and function calls"""
    
    def __init__(self):
        self._call_times = defaultdict(list)
        self._lock = threading.Lock()
    
    def __call__(self, seconds=5):
        """Decorator to rate limit function calls"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                now = time()
                key = func.__name__
                
                with self._lock:
                    # Clean old timestamps
                    self._call_times[key] = [
                        t for t in self._call_times[key] 
                        if now - t < seconds
                    ]
                    
                    # Check if we can call
                    if len(self._call_times[key]) == 0:
                        self._call_times[key].append(now)
                        return func(*args, **kwargs)
                    else:
                        # Rate limited - skip call
                        return None
            
            return wrapper
        return decorator


class ThreadSafeCallback:
    """Thread-safe callback wrapper"""
    
    def __init__(self, root, callback):
        self.root = root
        self.callback = callback
        self._lock = threading.Lock()
    
    def __call__(self, *args, **kwargs):
        """Call callback in GUI thread"""
        def safe_call():
            with self._lock:
                try:
                    self.callback(*args, **kwargs)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        self.root.after(0, safe_call)

class BatchedGUIUpdater:
    """Batch multiple GUI updates to reduce overhead"""
    
    def __init__(self, root, batch_interval_ms: int = 100):
        self.root = root
        self.batch_interval = batch_interval_ms
        self.pending_updates = []
        self.update_scheduled = False
    
    def schedule_update(self, callback, *args, **kwargs):
        """Schedule a GUI update (will be batched)"""
        self.pending_updates.append((callback, args, kwargs))
        
        if not self.update_scheduled:
            self.update_scheduled = True
            self.root.after(self.batch_interval, self._process_batch)
    
    def _process_batch(self):
        """Process all pending updates at once"""
        updates = self.pending_updates[:]
        self.pending_updates.clear()
        self.update_scheduled = False
        
        for callback, args, kwargs in updates:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Batch update error: {e}")

class ObjectPool:
    """Reuse objects instead of creating new ones"""
    
    def __init__(self, factory, max_size=100):
        self.factory = factory
        self.pool = []
        self.max_size = max_size
    
    def acquire(self):
        if self.pool:
            return self.pool.pop()
        return self.factory()
    
    def release(self, obj):
        if len(self.pool) < self.max_size:
            self.pool.append(obj)


# Global rate limiter instance
rate_limiter = RateLimiter()


# Convenience decorators
def rate_limit(seconds=5):
    """Rate limit decorator"""
    return rate_limiter(seconds)


def gui_thread_safe(method):
    """Decorator to make methods GUI thread-safe"""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'root') and hasattr(self, '_gui_safe'):
            self._gui_safe.schedule_update(method, self, *args, **kwargs)
        else:
            return method(self, *args, **kwargs)
    return wrapper


if __name__ == "__main__": 
    # Test rate limiter
    @rate_limit(seconds=2)
    def test_func():
        print(f"Called at {time()}")
    
    # Should print only twice
    for i in range(10):
        test_func()
        time.sleep(0.5)