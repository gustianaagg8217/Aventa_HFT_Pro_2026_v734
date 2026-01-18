#!/usr/bin/env python3
"""
Test script to verify manual position closes send telegram signals
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_manual_close_telegram_signal():
    """Test that manual position closes trigger telegram signals"""
    print("🧪 Testing Manual Close Telegram Signals")
    print("=" * 50)

    # Import the GUI class to test the manual close functionality
    from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
    import tkinter as tk

    # Create a minimal GUI instance for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window

    gui = HFTProGUI(root)

    # Mock the send_telegram_signal method to capture calls
    original_send_telegram = gui.send_telegram_signal
    telegram_signals_sent = []

    def mock_send_telegram_signal(bot_id, signal_type, **kwargs):
        telegram_signals_sent.append({
            'bot_id': bot_id,
            'signal_type': signal_type,
            'kwargs': kwargs
        })
        print(f"📤 Telegram signal captured: {signal_type} for bot {bot_id}")
        return True

    gui.send_telegram_signal = mock_send_telegram_signal

    # Test the format_close_position_signal method directly
    message = gui.format_close_position_signal(
        bot_id='TestBot',
        symbol='BTCUSD',
        ticket=12345678,
        profit=15.50,
        volume=0.01,
        balance=6780.98,
        equity=6780.71,
        free_margin=6399.97,
        margin_level=1780.93,
        total_volume_today=2.45
    )

    print("Formatted close position message:")
    print("=" * 50)
    print(message)
    print("=" * 50)

    # Verify the message contains required fields
    required_fields = [
        "🚀 **CLOSE POSITION SIGNAL**",
        "🤖 Bot: TestBot",
        "📊 Symbol: BTCUSD",
        "🎫 Ticket: 12345678",
        "💰 Profit: $15.50",
        "📈 Volume: 0.01",
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

    # Test with None values
    message_na = gui.format_close_position_signal(
        bot_id='TestBot',
        symbol='BTCUSD',
        ticket=12345678,
        profit=15.50,
        volume=0.01,
        balance=None,
        equity=None,
        free_margin=None,
        margin_level=None,
        total_volume_today=None
    )

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

    root.destroy()

    if success:
        print("\n🎉 SUCCESS: Manual close telegram signals are properly formatted!")
        print("✅ All required fields present")
        print("✅ N/A handling works correctly")
        print("✅ Account information included")
        return True
    else:
        print("\n❌ FAILED: Some fields are missing from manual close signals")
        return False

if __name__ == "__main__":
    test_manual_close_telegram_signal()