"""
Manual Test: Start Telegram Bot dengan runner
"""

import json
import os
import time
import asyncio
from telegram_bot import TelegramBot
from telegram_bot_runner import get_bot_runner

def test_manual_start():
    print("=" * 60)
    print("MANUAL TEST: START TELEGRAM BOT")
    print("=" * 60)
    
    # 1. Load config
    config_file = "configs/telegram_hft_config.json"
    print(f"\n1. Loading config from: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"   ERROR: Config file not found!")
        return
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    if 'telegram' not in config:
        print("   ERROR: No telegram config in file!")
        return
    
    token = config['telegram'].get('token', '')
    chat_ids = config['telegram'].get('chat_ids', [])
    
    print(f"   Token: {token[:30]}...")
    print(f"   Chat IDs: {chat_ids}")
    
    # 2. Create bot instance
    print("\n2. Creating TelegramBot instance...")
    try:
        bot = TelegramBot(token, chat_ids)
        print(f"   SUCCESS! Bot created")
        print(f"   Allowed users: {bot.allowed_users}")
    except Exception as e:
        print(f"   ERROR: {e}")
        return
    
    # 3. Get bot runner
    print("\n3. Getting bot runner...")
    runner = get_bot_runner()
    print(f"   Runner created")
    
    # 4. Start runner
    print("\n4. Starting runner...")
    runner.start()
    print(f"   Runner started")
    print(f"   Running: {runner.running}")
    print(f"   Loop: {runner.loop}")
    
    # Wait for loop to start
    time.sleep(1)
    print(f"   Loop running: {runner.loop.is_running() if runner.loop else 'N/A'}")
    
    # 5. Add bot to runner
    print("\n5. Adding bot to runner...")
    try:
        result = runner.add_bot("Trading Bot Account", bot)
        print(f"   Bot added: {result}")
    except Exception as e:
        print(f"   ERROR adding bot: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Check status
    print("\n6. Checking status...")
    print(f"   Active bots in runner: {list(runner.bots.keys())}")
    print(f"   Bot status: {runner.bots.get('Trading Bot Account', 'NOT FOUND')}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - Bot should be polling now")
    print("Keep this script running to keep bot active")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping bot runner...")
        runner.stop()
        print("Done!")

if __name__ == "__main__":
    test_manual_start()
