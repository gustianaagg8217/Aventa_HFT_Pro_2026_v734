#!/usr/bin/env python3
"""
Test script for max_daily_volume functionality
Tests that daily volume limits are properly enforced and reset
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from risk_manager import RiskManager
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class MockTrade:
    """Mock trade record for testing"""
    timestamp: datetime
    symbol: str
    trade_type: str
    volume: float
    open_price: float
    close_price: float
    profit: float
    duration: float
    reason: str

def test_max_daily_volume():
    """Test max daily volume limit functionality"""
    print("🧪 Testing Max Daily Volume functionality...")

    # Test configuration
    config = {
        'max_daily_loss': 100.0,
        'max_daily_trades': 10,
        'max_daily_volume': 5.0,  # Max 5 lots per day
        'max_position_size': 1.0,
        'max_positions': 3,
        'max_drawdown_pct': 10.0,
        'db_path': 'test_trades.db',
        '_bot_id': 'test_bot'
    }

    # Create risk manager
    rm = RiskManager(config)

    print(f"✅ Initial daily_volume: {rm.daily_volume}")
    print(f"✅ Max daily volume limit: {rm.max_daily_volume}")

    # Test 1: Check limits before any trades
    allowed, reason = rm.check_risk_limits()
    assert allowed == True, f"Should be allowed initially: {reason}"
    print("✅ Test 1 passed: Trading allowed with no trades")

    # Test 2: Record some trades and check volume accumulation
    trades = [
        MockTrade(datetime.now(), 'BTCUSD', 'BUY', 1.0, 50000, 50100, 100, 60, 'test'),
        MockTrade(datetime.now(), 'BTCUSD', 'SELL', 1.5, 50100, 50050, -75, 45, 'test'),
        MockTrade(datetime.now(), 'BTCUSD', 'BUY', 0.5, 50050, 50150, 50, 30, 'test'),
    ]

    total_volume = 0
    for trade in trades:
        rm.record_trade(trade)
        total_volume += trade.volume

    print(f"✅ Recorded {len(trades)} trades with total volume: {total_volume}")
    print(f"✅ Risk manager daily_volume: {rm.daily_volume}")

    assert abs(rm.daily_volume - total_volume) < 0.001, f"Volume mismatch: {rm.daily_volume} vs {total_volume}"

    # Test 3: Check that trading is still allowed (below limit)
    allowed, reason = rm.check_risk_limits()
    assert allowed == True, f"Should still be allowed: {reason}"
    print("✅ Test 3 passed: Trading still allowed below volume limit")

    # Test 4: Add one more trade that exceeds the limit
    final_trade = MockTrade(datetime.now(), 'BTCUSD', 'BUY', 2.0, 50150, 50250, 100, 60, 'test')
    rm.record_trade(final_trade)
    total_volume += final_trade.volume

    print(f"✅ After final trade - total volume: {total_volume}")
    print(f"✅ Risk manager daily_volume: {rm.daily_volume}")

    # Test 5: Check that trading is now blocked
    allowed, reason = rm.check_risk_limits()
    assert allowed == False, f"Should be blocked: {reason}"
    assert "volume limit" in reason.lower(), f"Reason should mention volume: {reason}"
    print("✅ Test 5 passed: Trading blocked when volume limit exceeded")

    # Test 6: Simulate day reset
    print("\n🕐 Simulating day reset...")
    rm.last_reset_date = datetime.now().date() - timedelta(days=1)  # Force reset
    rm.reset_daily_stats()

    print(f"✅ After reset - daily_volume: {rm.daily_volume}")

    # Test 7: Check that trading is allowed again after reset
    allowed, reason = rm.check_risk_limits()
    assert allowed == True, f"Should be allowed after reset: {reason}"
    print("✅ Test 7 passed: Trading allowed again after daily reset")

    print("\n🎉 All max_daily_volume tests passed!")

if __name__ == "__main__":
    test_max_daily_volume()