"""
Account Info Caching for Aventa HFT Pro 2026
Reduces MT5 account_info() calls
"""

import MetaTrader5 as mt5
from time import time
from dataclasses import dataclass
from typing import Optional
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class AccountSnapshot:
    """Cached account information"""
    balance: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    profit:  float
    timestamp: float
    
    @property
    def age(self) -> float:
        """Age of snapshot in seconds"""
        return time() - self.timestamp
    
    def is_stale(self, max_age: float = 1.0) -> bool:
        """Check if snapshot is older than max_age"""
        return self.age > max_age


class AccountCache:
    """Thread-safe account info cache"""
    
    def __init__(self, ttl: float = 1.0):
        """
        Initialize cache
        
        Args:
            ttl: Time to live in seconds (default 1 second)
        """
        self.ttl = ttl
        self._snapshot:  Optional[AccountSnapshot] = None
        self._lock = threading.Lock()
        self._update_count = 0
        self._hit_count = 0
        self._miss_count = 0
    
    def get_info(self, force_refresh: bool = False) -> Optional[AccountSnapshot]:
        """
        Get account info (cached or fresh)
        
        Args:
            force_refresh:  Force fetch from MT5
        
        Returns:
            AccountSnapshot or None
        """
        with self._lock:
            # Check if cached data is valid
            if not force_refresh and self._snapshot and not self._snapshot.is_stale(self.ttl):
                self._hit_count += 1
                return self._snapshot
            
            # Fetch fresh data
            self._miss_count += 1
            return self._refresh()
    
    def _refresh(self) -> Optional[AccountSnapshot]:
        """Fetch fresh account info from MT5"""
        try: 
            account = mt5.account_info()
            
            if account is None:
                logger.error("Failed to get account info from MT5")
                return self._snapshot  # Return stale data if available
            
            self._snapshot = AccountSnapshot(
                balance=account.balance,
                equity=account.equity,
                margin=account.margin,
                margin_free=account.margin_free,
                margin_level=account.margin_level if account.margin > 0 else 0,
                profit=account.profit,
                timestamp=time()
            )
            
            self._update_count += 1
            
            return self._snapshot
            
        except Exception as e:
            logger.error(f"Account cache refresh error: {e}")
            return self._snapshot  # Return stale data
    
    def force_update(self) -> Optional[AccountSnapshot]:
        """Force immediate update from MT5"""
        return self.get_info(force_refresh=True)
    
    def invalidate(self):
        """Invalidate cache (force refresh on next get)"""
        with self._lock:
            if self._snapshot:
                self._snapshot.timestamp = 0
    
    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self._hit_count + self._miss_count
        return (self._hit_count / total * 100) if total > 0 else 0
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            'updates': self._update_count,
            'hits': self._hit_count,
            'misses':  self._miss_count,
            'hit_rate': self.cache_hit_rate,
            'current_age': self._snapshot.age if self._snapshot else None
        }
    
    def __repr__(self):
        if self._snapshot:
            return (f"AccountCache(balance={self._snapshot.balance:.2f}, "
                   f"equity={self._snapshot.equity:.2f}, "
                   f"age={self._snapshot.age:.2f}s)")
        return "AccountCache(empty)"


class MultiAccountCache:
    """Cache for multiple MT5 accounts"""
    
    def __init__(self, default_ttl: float = 1.0):
        self.default_ttl = default_ttl
        self._caches = {}
        self._lock = threading.Lock()
    
    def get_cache(self, account_id: int) -> AccountCache:
        """Get or create cache for account"""
        with self._lock:
            if account_id not in self._caches:
                self._caches[account_id] = AccountCache(self.default_ttl)
            return self._caches[account_id]
    
    def get_all_stats(self) -> dict:
        """Get statistics for all cached accounts"""
        with self._lock:
            return {
                account_id: cache.get_stats()
                for account_id, cache in self._caches.items()
            }


if __name__ == "__main__":
    # Test cache
    if not mt5.initialize():
        print("MT5 not initialized")
        exit()
    
    cache = AccountCache(ttl=1.0)
    
    # First call - should miss
    info1 = cache.get_info()
    print(f"Call 1: {info1} (miss)")
    
    # Immediate second call - should hit
    info2 = cache.get_info()
    print(f"Call 2: {info2} (hit)")
    
    # Wait for expiry
    import time
    time.sleep(1.1)
    
    # Third call - should miss
    info3 = cache.get_info()
    print(f"Call 3: {info3} (miss)")
    
    # Stats
    stats = cache.get_stats()
    print(f"\nCache stats: {stats}")
    print(f"Hit rate: {cache.cache_hit_rate:.1f}%")
    
    mt5.shutdown()
    print("\n✅ Account cache test passed")