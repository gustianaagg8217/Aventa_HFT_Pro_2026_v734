"""
Unit tests for optimization modules
"""

import pytest
import time
from datetime import datetime
from config_manager import ConfigManager
from trade_database import TradeDatabase
from account_cache import AccountCache
from thread_safety import rate_limit, RateLimiter


class TestConfigManager:
    """Test configuration isolation"""
    
    def test_config_isolation(self):
        """Verify configs are truly isolated"""
        manager = ConfigManager()
        
        config1 = copy.deepcopy(manager.DEFAULT_CONFIG)
        config1['bot_id'] = "Bot_1"
        config2 = copy.deepcopy(manager.DEFAULT_CONFIG)
        config2['bot_id'] = "Bot_2"
        
        # Modify config1
        config1['symbol'] = 'EURUSD'
        config1['nested'] = {'key': 'value1'}
        
        # Verify config2 unchanged
        assert config2['symbol'] == 'GOLD.ls'
        assert 'nested' not in config2
    
    def test_unique_magic_numbers(self):
        """Verify each bot gets unique magic number"""
        manager = ConfigManager()
        
        magics = set()
        for i in range(10):
            config = copy.deepcopy(manager.DEFAULT_CONFIG)
            config['bot_id'] = f"Bot_{i}"
            magics.add(config['magic_number'])
        
        assert len(magics) == 10, "Magic numbers not unique"
    
    def test_save_load_roundtrip(self):
        """Test save and load preserves data"""
        manager = ConfigManager()
        
        config = copy.deepcopy(manager.DEFAULT_CONFIG)
        config['bot_id'] = "TestBot"
        config['custom_field'] = 'test_value'
        
        # Save
        filepath = manager.save_config(config, filename='test_config.json')
        
        # Load
        loaded = manager.load_config('test_config.json')
        
        assert loaded['custom_field'] == 'test_value'
        assert loaded['symbol'] == config['symbol']


class TestTradeDatabase:
    """Test trade persistence"""
    
    @pytest.fixture
    def db(self, tmp_path):
        """Create temporary database"""
        db_path = tmp_path / "test.db"
        return TradeDatabase(str(db_path))
    
    def test_record_and_retrieve(self, db):
        """Test basic record/retrieve"""
        trade = {
            'timestamp': datetime.now().timestamp(),
            'symbol':  'GOLD.ls',
            'trade_type': 'BUY',
            'volume': 0.01,
            'open_price': 2600.0,
            'close_price': 2601.0,
            'profit':  1.0,
            'duration':  60.0,
            'reason': 'Test',
            'magic_number': 123
        }
        
        db.record_trade('Bot_1', trade)
        
        trades = db.get_trades(bot_id='Bot_1')
        assert len(trades) == 1
        assert trades[0]['profit'] == 1.0
    
    def test_daily_stats(self, db):
        """Test statistics calculation"""
        # Record winning trade
        db.record_trade('Bot_1', {
            'timestamp': datetime.now().timestamp(),
            'symbol': 'GOLD.ls',
            'trade_type': 'BUY',
            'volume': 0.01,
            'open_price': 2600.0,
            'close_price': 2601.0,
            'profit': 1.0,
            'duration': 60.0,
            'reason': 'Win',
            'magic_number':  123
        })
        
        # Record losing trade
        db.record_trade('Bot_1', {
            'timestamp': datetime.now().timestamp(),
            'symbol': 'GOLD.ls',
            'trade_type': 'SELL',
            'volume': 0.01,
            'open_price': 2601.0,
            'close_price':  2600.5,
            'profit': -0.5,
            'duration':  30.0,
            'reason':  'Loss',
            'magic_number': 123
        })
        
        stats = db.get_daily_stats('Bot_1')
        
        assert stats['total_trades'] == 2
        assert stats['wins'] == 1
        assert stats['losses'] == 1
        assert stats['win_rate'] == 50.0


class TestAccountCache:
    """Test account caching"""
    
    def test_cache_hit(self):
        """Test cache hit on repeated calls"""
        cache = AccountCache(ttl=1.0)
        
        # Mock MT5 (in real test, would use unittest.mock)
        # For now, just test cache logic
        
        assert cache._hit_count == 0
        assert cache._miss_count == 0
    
    def test_cache_expiry(self):
        """Test cache expires after TTL"""
        cache = AccountCache(ttl=0.1)  # 100ms TTL
        
        # Would test with mocked MT5
        # Verify cache refreshes after 100ms


class TestRateLimiter: 
    """Test rate limiting"""
    
    def test_rate_limit_decorator(self):
        """Test rate limiting works"""
        call_count = [0]
        
        @rate_limit(seconds=1)
        def test_func():
            call_count[0] += 1
        
        # Should allow first call
        test_func()
        assert call_count[0] == 1
        
        # Should block subsequent calls within 1 second
        for _ in range(10):
            test_func()
            time.sleep(0.1)
        
        # Should only have called once
        assert call_count[0] == 1
        
        # Wait for rate limit to expire
        time.sleep(1.1)
        
        # Should allow another call
        test_func()
        assert call_count[0] == 2


if __name__ == "__main__": 
    pytest.main([__file__, "-v"])