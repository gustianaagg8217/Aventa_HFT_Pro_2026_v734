#!/usr/bin/env python3
"""
Test MT5 account info fetching
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    import MetaTrader5 as mt5
    print("✓ MetaTrader5 imported successfully")

    # Try to initialize MT5
    if not mt5.initialize():
        print("✗ MT5 initialization failed")
        sys.exit(1)

    print("✓ MT5 initialized successfully")

    # Try to get account info
    account_info = mt5.account_info()
    if account_info is None:
        print("✗ account_info() returned None")
        print(f"Last error: {mt5.last_error()}")
        sys.exit(1)

    print("✓ Account info retrieved successfully")
    print(f"Balance: ${account_info.balance:.2f}")
    print(f"Equity: ${account_info.equity:.2f}")
    print(f"Free Margin: ${account_info.margin_free:.2f}")
    print(f"Margin: ${account_info.margin:.2f}")

    margin_level = (account_info.equity / account_info.margin) * 100 if account_info.margin > 0 else 0
    print(f"Margin Level: {margin_level:.2f}%")

    # Shutdown MT5
    mt5.shutdown()
    print("✓ MT5 shutdown successfully")

except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)