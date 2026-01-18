#!/usr/bin/env python3
"""
Test script to verify open position signal includes account information
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_open_position_signal_format():
    """Test that open position signal includes account information"""
    print("🧪 Testing Open Position Signal Format with Account Info")
    print("=" * 60)

    # Import the GUI class to test the format method
    from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
    import tkinter as tk

    # Create a minimal GUI instance for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window

    gui = HFTProGUI(root)

    # Test with account information
    message = gui.format_open_position_signal(
        bot_id='VANTAGE STD VIP',
        symbol='BTCUSD',
        order_type='SELL',
        volume=0.01,
        price=95162.97,
        sl=95387.92454,
        tp=95147.97,
        balance=6780.98,
        equity=6780.71,
        free_margin=6399.97,
        margin_level=1780.93
    )

    print("Formatted open position message:")
    print("=" * 60)
    print(message)
    print("=" * 60)

    # Test with None values (should show N/A)
    message_na = gui.format_open_position_signal(
        bot_id='VANTAGE STD VIP',
        symbol='BTCUSD',
        order_type='SELL',
        volume=0.01,
        price=95162.97,
        sl=95387.92454,
        tp=95147.97,
        balance=None,
        equity=None,
        free_margin=None,
        margin_level=None
    )

    print("\nWith None values (should show N/A):")
    print("=" * 60)
    print(message_na)
    print("=" * 60)

    root.destroy()

    # Verify the message contains account information
    required_fields = [
        "💳 **Account Summary:**",
        "💵 Balance: $6780.98",
        "📊 Equity: $6780.71",
        "🆓 Free Margin: $6399.97",
        "📊 Margin Level: 1780.93%"
    ]

    success = True
    for field in required_fields:
        if field not in message:
            print(f"❌ Missing field: {field}")
            success = False
        else:
            print(f"✅ Found field: {field}")

    # Check N/A handling
    na_fields = [
        "💵 Balance: N/A",
        "📊 Equity: N/A",
        "🆓 Free Margin: N/A",
        "📊 Margin Level: N/A"
    ]

    for field in na_fields:
        if field not in message_na:
            print(f"❌ Missing N/A field: {field}")
            success = False
        else:
            print(f"✅ Found N/A field: {field}")

    if success:
        print("\n🎉 SUCCESS: Open position signal now includes account information!")
        return True
    else:
        print("\n❌ FAILED: Some account information fields are missing")
        return False

if __name__ == "__main__":
    test_open_position_signal_format()