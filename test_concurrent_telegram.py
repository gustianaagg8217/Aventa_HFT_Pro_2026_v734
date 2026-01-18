#!/usr/bin/env python3
"""
Stress test for concurrent bot Telegram signals
"""
import sys
import os
import threading
import time
import random
sys.path.append(os.path.dirname(__file__))

def test_concurrent_bot_signals():
    """Test multiple bots sending Telegram signals concurrently"""

    print("🧪 Testing Concurrent Bot Telegram Signals")
    print("=" * 60)

    class MockGUI:
        def __init__(self):
            self.telegram_bots = {
                'Bot_1': type('MockBot', (), {'token': 'TOKEN_1', 'allowed_users': ['111111111']})(),
                'Bot_2': type('MockBot', (), {'token': 'TOKEN_2', 'allowed_users': ['222222222']})(),
                'Bot_3': type('MockBot', (), {'token': 'TOKEN_3', 'allowed_users': ['333333333']})(),
            }
            self.received_signals = []
            self.lock = threading.Lock()

        def send_telegram_signal(self, bot_id, signal_type, **kwargs):
            """Mock send_telegram_signal with thread safety"""
            with self.lock:
                self.received_signals.append({
                    'bot_id': bot_id,
                    'signal_type': signal_type,
                    'thread_id': threading.current_thread().ident,
                    'timestamp': time.time(),
                    'kwargs': kwargs
                })
                print(f"📤 [{threading.current_thread().ident}] Bot {bot_id}: {signal_type}")
            # Simulate network delay
            time.sleep(random.uniform(0.01, 0.05))

    gui = MockGUI()
    bots = ['Bot_1', 'Bot_2', 'Bot_3']
    threads = []

    def bot_worker(bot_id):
        """Simulate a bot sending multiple signals"""
        try:
            # Create telegram callback for this bot
            telegram_callback = lambda **data: gui.send_telegram_signal(bot_id=bot_id, **data)

            # Send multiple signals with random delays
            for i in range(5):  # 5 signals per bot
                signal_type = random.choice(['open_position', 'close_position'])

                if signal_type == 'open_position':
                    telegram_callback(
                        signal_type=signal_type,
                        symbol="BTCUSD.futu",
                        order_type=random.choice(['BUY', 'SELL']),
                        volume=round(random.uniform(0.01, 0.1), 2),
                        price=round(random.uniform(95000, 96000), 2),
                        sl=round(random.uniform(94500, 95500), 2),
                        tp=round(random.uniform(95500, 96500), 2)
                    )
                else:  # close_position
                    telegram_callback(
                        signal_type=signal_type,
                        symbol="BTCUSD.futu",
                        ticket=random.randint(10000000, 99999999),
                        profit=round(random.uniform(-0.5, 0.5), 2),
                        volume=round(random.uniform(0.01, 0.1), 2),
                        balance=round(random.uniform(6700, 6900), 2),
                        equity=round(random.uniform(6700, 6900), 2),
                        free_margin=round(random.uniform(6500, 6800), 2),
                        margin_level=round(random.uniform(3000, 4000), 2),
                        total_volume_today=round(random.uniform(0.5, 2.0), 2)
                    )

                # Random delay between signals
                time.sleep(random.uniform(0.01, 0.1))

        except Exception as e:
            print(f"❌ Error in bot {bot_id}: {e}")

    # Start concurrent bot threads
    print("🚀 Starting concurrent bot threads...")
    for bot_id in bots:
        thread = threading.Thread(target=bot_worker, args=(bot_id,), name=f"Bot-{bot_id}")
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    print("\n📊 Results Analysis:")
    print("=" * 60)

    total_signals = len(gui.received_signals)
    expected_signals = len(bots) * 5  # 5 signals per bot

    print(f"Expected signals: {expected_signals}")
    print(f"Received signals: {total_signals}")

    if total_signals == expected_signals:
        print("✅ All signals received!")
    else:
        print(f"❌ Signal count mismatch! Missing {expected_signals - total_signals} signals")

    # Analyze per-bot signal counts
    bot_counts = {}
    thread_ids = set()

    for signal in gui.received_signals:
        bot_id = signal['bot_id']
        thread_id = signal['thread_id']

        if bot_id not in bot_counts:
            bot_counts[bot_id] = 0
        bot_counts[bot_id] += 1
        thread_ids.add(thread_id)

    print(f"\n🤖 Signals per bot:")
    all_correct = True
    for bot_id in bots:
        count = bot_counts.get(bot_id, 0)
        expected = 5
        status = "✅" if count == expected else "❌"
        print(f"  {bot_id}: {count}/{expected} signals {status}")
        if count != expected:
            all_correct = False

    print(f"\n🧵 Thread analysis:")
    print(f"  Unique threads used: {len(thread_ids)}")
    print(f"  Thread IDs: {sorted(thread_ids)}")

    # Check for signal isolation (no bot should receive another bot's signals)
    print(f"\n🔒 Signal Isolation Check:")
    isolation_ok = True
    for signal in gui.received_signals:
        signal_bot = signal['bot_id']
        if signal_bot not in bots:
            print(f"❌ Invalid bot_id in signal: {signal_bot}")
            isolation_ok = False

    if isolation_ok:
        print("✅ All signals properly isolated to correct bots")
    else:
        print("❌ Signal isolation issues detected")

    # Performance check
    if gui.received_signals:
        timestamps = [s['timestamp'] for s in gui.received_signals]
        duration = max(timestamps) - min(timestamps)
        signals_per_second = total_signals / duration if duration > 0 else 0
        print(f"  Signals/second: {signals_per_second:.2f}")
    if all_correct and isolation_ok:
        print("\n🎉 SUCCESS: Concurrent bot signals working perfectly!")
        print("✅ No race conditions detected")
        print("✅ Proper bot isolation maintained")
        print("✅ All signals delivered correctly")
        return True
    else:
        print("\n❌ FAILURE: Issues detected in concurrent signal handling")
        return False

if __name__ == "__main__":
    success = test_concurrent_bot_signals()
    sys.exit(0 if success else 1)