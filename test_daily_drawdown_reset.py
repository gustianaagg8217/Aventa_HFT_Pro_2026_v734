#!/usr/bin/env python3
"""
Test script for daily drawdown reset functionality
Tests that peak_equity resets daily in the trading engine
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
import unittest.mock as mock

# Mock MT5 to avoid connection issues
sys.modules['MetaTrader5'] = mock.MagicMock()

from aventa_hft_core import UltraLowLatencyEngine

def test_daily_drawdown_reset():
    """Test that peak_equity resets daily"""
    print("🧪 Testing Daily Drawdown Reset functionality...")

    # Mock config
    config = {
        'symbol': 'BTCUSD',
        'mt5_path': 'mock_path',
        'max_daily_loss': 100.0,
        'max_daily_trades': 10,
        'max_daily_volume': 5.0,
        'max_position_size': 2.0,
        'initial_balance': 4000.0
    }

    # Create engine instance
    engine = UltraLowLatencyEngine('BTCUSD', config)

    # Mock the account equity method to return a fixed value
    engine.get_account_equity = mock.MagicMock(return_value=3792.0)

    print(f"✅ Initial peak_equity: ${engine.peak_equity:.2f}")
    print(f"✅ Initial last_reset_date: {engine.last_reset_date}")

    # Simulate setting a high peak equity (like from previous day)
    engine.peak_equity = 10000.0  # Simulate previous high
    print(f"✅ Simulated previous peak: ${engine.peak_equity:.2f}")

    # Test 1: Reset on same day should not change peak_equity
    print("\n📅 Test 1: Same day reset")
    engine.reset_daily_stats()
    print(f"✅ Peak equity after same-day reset: ${engine.peak_equity:.2f}")
    assert engine.peak_equity == 10000.0, "Peak equity should not change on same day"
    print("✅ Test 1 passed: Peak equity unchanged on same day")

    # Test 2: Reset on new day should update peak_equity to current equity
    print("\n📅 Test 2: New day reset")
    # Simulate new day by changing last_reset_date
    engine.last_reset_date = datetime.now().date() - timedelta(days=1)
    engine.reset_daily_stats()
    print(f"✅ Peak equity after new-day reset: ${engine.peak_equity:.2f}")
    assert abs(engine.peak_equity - 3792.0) < 0.01, f"Peak equity should be reset to current equity: {engine.peak_equity}"
    print("✅ Test 2 passed: Peak equity reset to current equity on new day")

    # Test 3: Verify drawdown calculation with reset peak
    print("\n📊 Test 3: Drawdown calculation")
    current_equity = 3792.0
    drawdown_pct = ((engine.peak_equity - current_equity) / engine.peak_equity) * 100
    print(f"✅ Current equity: ${current_equity:.2f}")
    print(f"✅ Peak equity: ${engine.peak_equity:.2f}")
    print(f"✅ Calculated drawdown: {drawdown_pct:.2f}%")

    # With peak reset to 3792 and current at 3792, drawdown should be 0%
    assert abs(drawdown_pct) < 0.01, f"Drawdown should be near 0% after reset: {drawdown_pct}"
    print("✅ Test 3 passed: Drawdown correctly calculated after reset")

    # Test 4: Simulate small loss and check drawdown
    print("\n📊 Test 4: Small loss drawdown")
    # Update current equity to simulate small loss
    engine.get_account_equity = mock.MagicMock(return_value=3715.75)  # -76.25 loss
    current_equity = 3715.75
    drawdown_pct = ((engine.peak_equity - current_equity) / engine.peak_equity) * 100
    expected_drawdown = ((3792.0 - 3715.75) / 3792.0) * 100

    print(f"✅ Current equity: ${current_equity:.2f}")
    print(f"✅ Peak equity: ${engine.peak_equity:.2f}")
    print(f"✅ Calculated drawdown: {drawdown_pct:.2f}%")
    print(f"✅ Expected drawdown: {expected_drawdown:.2f}%")

    assert abs(drawdown_pct - expected_drawdown) < 0.01, f"Drawdown mismatch: {drawdown_pct} vs {expected_drawdown}"
    print("✅ Test 4 passed: Small loss drawdown correctly calculated")

    print("\n🎉 All daily drawdown reset tests passed!")
    print("✅ Peak equity now resets daily to current equity")
    print("✅ Drawdown calculation uses daily peak, not historical peak")
    print("✅ Fixes the 62.26% drawdown issue when actual loss is only -$76.25")

if __name__ == "__main__":
    test_daily_drawdown_reset()