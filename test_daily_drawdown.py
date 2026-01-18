#!/usr/bin/env python3
"""
Test script to verify daily drawdown calculation
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from risk_manager import RiskManager
from datetime import datetime

def test_daily_drawdown():
    """Test that drawdown is calculated correctly for the current day"""

    print("🧪 Testing Daily Drawdown Calculation")
    print("=" * 50)

    # Create a mock config
    config = {
        'max_daily_loss': 100.0,
        'max_daily_trades': 100,
        'max_drawdown_pct': 10.0,  # 10% max drawdown
        'risk_per_trade': 1.0
    }

    # Create risk manager
    rm = RiskManager(config)

    print("📊 Simulating Daily Trading Activity:")
    print("-" * 40)

    # Simulate account balance progression during the day
    # Start with $10,000
    account_balances = [
        10000.0,  # Start of day
        10150.0,  # +$150 (peak)
        10050.0,  # -$100 from peak
        10200.0,  # +$200 (new peak)
        10100.0,  # -$100 from peak
        9900.0    # -$300 from peak (should trigger drawdown)
    ]

    expected_drawdowns = [
        0.0,      # At start (becomes peak)
        0.0,      # At new peak ($10,150)
        0.99,     # (10150-10050)/10150 * 100 ≈ 0.99%
        0.0,      # At new peak ($10,200)
        0.98,     # (10200-10100)/10200 * 100 ≈ 0.98%
        2.94      # (10200-9900)/10200 * 100 ≈ 2.94%
    ]

    for i, balance in enumerate(account_balances):
        # Get risk metrics (this updates drawdown)
        metrics = rm.get_risk_metrics(balance)

        expected = expected_drawdowns[i] if i < len(expected_drawdowns) else 0.0

        print(f"Balance: ${balance:.2f} -> Drawdown: {metrics.max_drawdown:.2f}%")
        if abs(metrics.max_drawdown - expected) > 0.1:  # Allow 0.1% tolerance for floating point
            print(f"  ❌ Expected: {expected:.2f}%, Got: {metrics.max_drawdown:.2f}%")
            return False
        else:
            print("  ✅ Correct")
    print("\n🔄 Testing Daily Reset:")
    print("-" * 30)

    # Simulate next day - reset should happen
    # Force reset by changing the date
    rm.last_reset_date = datetime(2025, 1, 17).date()  # Yesterday

    # Call reset_daily_stats (this should reset peak_balance)
    rm.reset_daily_stats()

    # Check that peak_balance was reset
    print(f"Peak balance after reset: ${rm.peak_balance:.2f}")
    print(f"Current drawdown after reset: {rm.current_drawdown:.2f}%")

    if rm.peak_balance == 0.0 and rm.current_drawdown == 0.0:
        print("✅ Daily reset working correctly")
    else:
        print("❌ Daily reset failed")
        return False

    # Test new day with different balance
    new_balance = 10500.0  # New day starts with different balance
    metrics = rm.get_risk_metrics(new_balance)

    print("\n📈 New day simulation:")
    print(f"Account balance: ${new_balance:.2f}")
    print(f"Drawdown: {metrics.max_drawdown:.2f}%")
    if metrics.max_drawdown == 0.0:
        print("✅ New day drawdown calculation correct")
    else:
        print("❌ New day drawdown calculation incorrect")
        return False

    print("\n🎉 SUCCESS: Daily drawdown calculation working correctly!")
    print("✅ Drawdown resets daily")
    print("✅ Based on actual account balance")
    print("✅ Not accumulated from account opening")

    return True

if __name__ == "__main__":
    success = test_daily_drawdown()
    sys.exit(0 if success else 1)