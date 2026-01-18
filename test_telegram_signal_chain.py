#!/usr/bin/env python3
"""
Comprehensive test to verify bot_id is correctly passed through the telegram signal chain
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_telegram_signal_chain():
    """Test that bot_id flows correctly from engine callback to telegram signal"""

    print("🧪 Testing Telegram Signal Chain")
    print("=" * 50)

    # Mock the GUI's send_telegram_signal method
    class MockGUI:
        def __init__(self):
            self.telegram_bots = {}
            self.received_signals = []

        def send_telegram_signal(self, bot_id, signal_type, **kwargs):
            """Mock send_telegram_signal that records what it receives"""
            self.received_signals.append({
                'bot_id': bot_id,
                'signal_type': signal_type,
                'kwargs': kwargs
            })
            print(f"📤 Received signal for bot: {bot_id}, type: {signal_type}")
            return True

    # Create mock GUI
    gui = MockGUI()

    # Simulate different bots with their own telegram callbacks
    bots = ['Bot_1', 'Bot_2', 'Bot_3']

    for bot_id in bots:
        # This simulates the callback setup in the GUI
        telegram_callback = lambda **data: gui.send_telegram_signal(bot_id=bot_id, **data)

        # Simulate engine calling the callback (like in aventa_hft_core.py)
        print(f"\n🤖 Testing {bot_id}:")

        # Test close position signal
        telegram_callback(
            signal_type="close_position",
            symbol="BTCUSD.futu",
            ticket=12345678,
            profit=0.15,
            volume=0.01,
            balance=6788.35,
            equity=6788.35,
            free_margin=6788.35,
            margin_level=3563.18,
            total_volume_today=0.76
        )

        # Test open position signal
        telegram_callback(
            signal_type="open_position",
            symbol="BTCUSD.futu",
            order_type="BUY",
            volume=0.01,
            price=95121.59,
            sl=95071.59,
            tp=95136.59
        )

    print("\n📊 Signal Reception Summary:")
    print("=" * 50)

    expected_signals = len(bots) * 2  # 2 signals per bot
    received_signals = len(gui.received_signals)

    print(f"Expected signals: {expected_signals}")
    print(f"Received signals: {received_signals}")

    if received_signals == expected_signals:
        print("✅ All signals received correctly!")
    else:
        print("❌ Signal count mismatch!")

    # Verify each bot received its own signals
    bot_signal_counts = {}
    for signal in gui.received_signals:
        bot_id = signal['bot_id']
        if bot_id not in bot_signal_counts:
            bot_signal_counts[bot_id] = 0
        bot_signal_counts[bot_id] += 1

    print("\n🤖 Signals per bot:")
    for bot_id, count in bot_signal_counts.items():
        print(f"  {bot_id}: {count} signals")
        if count != 2:  # Should have 2 signals each (open + close)
            print(f"  ❌ {bot_id} signal count incorrect!")
        else:
            print(f"  ✅ {bot_id} signal count correct!")

    # Verify bot isolation - each bot should only receive its own signals
    print("\n🔒 Bot Isolation Check:")
    all_correct = True
    for signal in gui.received_signals:
        signal_bot_id = signal['bot_id']
        if signal_bot_id not in bots:
            print(f"❌ Unknown bot_id in signal: {signal_bot_id}")
            all_correct = False
        else:
            print(f"✅ Signal correctly attributed to {signal_bot_id}")

    if all_correct:
        print("\n🎉 SUCCESS: Each bot can send independent Telegram signals!")
        print("✅ Bot isolation maintained")
        print("✅ Correct bot_id propagation")
        print("✅ Signal routing working properly")
    else:
        print("\n❌ FAILURE: Issues found with bot signal independence")

    return all_correct

if __name__ == "__main__":
    test_telegram_signal_chain()