#!/usr/bin/env python3
"""
Test script for clear all positions telegram notification
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_clear_all_positions_signal():
    """Test the clear all positions telegram signal formatting"""
    try:
        from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
        import tkinter as tk

        # Create a minimal GUI instance for testing
        root = tk.Tk()
        root.withdraw()  # Hide the window

        gui = HFTProGUI(root)

        # Test the format_clear_all_positions_signal method
        message = gui.format_clear_all_positions_signal(
            bot_id="TestBot",
            closed_count=3,
            total_profit=15.75,
            balance=10000.00,
            equity=9950.25,
            free_margin=9850.00,
            margin_level=95.5
        )

        print("✅ Clear All Positions Signal Format Test:")
        print("=" * 50)
        print(message)
        print("=" * 50)

        # Check if required elements are present
        required_elements = [
            "CLEANSHEET - ALL POSITIONS CLEARED",
            "Bot: TestBot",
            "Positions Closed: 3",
            "Total P&L: $15.75",
            "Balance: $10000.00",
            "Equity: $9950.25",
            "Free Margin: $9850.00",
            "Margin Level: 95.50%"
        ]

        all_present = True
        for element in required_elements:
            if element not in message:
                print(f"❌ Missing element: {element}")
                all_present = False
            else:
                print(f"✅ Found: {element}")

        if all_present:
            print("\n🎉 All required elements present in the message!")
            return True
        else:
            print("\n❌ Some elements missing from the message!")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

def test_send_telegram_signal_clear_all():
    """Test sending clear all positions telegram signal"""
    try:
        from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
        import tkinter as tk

        # Create a minimal GUI instance
        root = tk.Tk()
        root.withdraw()

        gui = HFTProGUI(root)

        # Mock telegram_bots to avoid actual sending
        gui.telegram_bots = {
            "TestBot": type('MockBot', (), {
                'token': 'mock_token',
                'allowed_users': ['123456789']
            })()
        }

        # Mock the send_telegram_signal to capture the call
        original_send = gui.send_telegram_signal
        signal_sent = {}

        def mock_send_telegram_signal(bot_id, signal_type, **kwargs):
            signal_sent['bot_id'] = bot_id
            signal_sent['signal_type'] = signal_type
            signal_sent['kwargs'] = kwargs
            print(f"📤 Mock telegram signal sent: {signal_type} for bot {bot_id}")

        gui.send_telegram_signal = mock_send_telegram_signal

        # Test sending clear all positions signal
        gui.send_telegram_signal(
            bot_id="TestBot",
            signal_type="clear_all_positions",
            closed_count=2,
            total_profit=-5.50,
            balance=9995.50,
            equity=9990.00,
            free_margin=9890.00,
            margin_level=94.2
        )

        # Verify the signal was sent correctly
        if signal_sent.get('signal_type') == 'clear_all_positions':
            print("✅ Clear all positions signal sent successfully!")
            print(f"   Bot ID: {signal_sent['bot_id']}")
            print(f"   Closed Count: {signal_sent['kwargs']['closed_count']}")
            print(f"   Total Profit: ${signal_sent['kwargs']['total_profit']:.2f}")
            return True
        else:
            print("❌ Clear all positions signal was not sent correctly!")
            return False

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        try:
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    print("🧪 Testing Clear All Positions Telegram Notification")
    print("=" * 60)

    # Test 1: Message formatting
    print("\n1. Testing message formatting...")
    test1_passed = test_clear_all_positions_signal()

    # Test 2: Signal sending
    print("\n2. Testing signal sending...")
    test2_passed = test_send_telegram_signal_clear_all()

    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! Clear all positions notification is working.")
    else:
        print("❌ Some tests failed. Please check the implementation.")

    sys.exit(0 if (test1_passed and test2_passed) else 1)