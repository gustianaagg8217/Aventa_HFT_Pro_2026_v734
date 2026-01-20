"""
Quick test: Check if bot can be created and runner started
"""

import json
import os
import sys
import asyncio

print("TEST: Bot Creation and Runner Start\n")

# 1. Load config
config_file = "configs/telegram_hft_config.json"
print(f"1. Loading config: {config_file}")

with open(config_file, 'r') as f:
    config = json.load(f)

token = config['telegram'].get('token', '')
chat_ids = config['telegram'].get('chat_ids', [])
print(f"   Token OK: {len(token) > 0}")
print(f"   Chat IDs: {chat_ids}")

# 2. Create bot
print(f"\n2. Creating TelegramBot...")
from telegram_bot import TelegramBot

bot = TelegramBot(token, chat_ids)
print(f"   SUCCESS!")
print(f"   Bot allowed_users: {bot.allowed_users}")
print(f"   Bot handlers: {len(bot.app.handlers)}")

# 3. Test runner (don't actually start polling, just test instantiation)
print(f"\n3. Testing TelegramBotRunner...")
from telegram_bot_runner import get_bot_runner

runner = get_bot_runner()
print(f"   Runner created: {runner is not None}")

# 4. Start runner
print(f"\n4. Starting runner...")
runner.start()
print(f"   Runner running: {runner.running}")

import time
time.sleep(2)  # Wait for loop to start

if runner.loop and runner.loop.is_running():
    print(f"   Event loop is RUNNING! ✓")
else:
    print(f"   Event loop NOT running ✗")

print(f"\n5. Adding bot to runner...")
try:
    runner.add_bot("Trading Bot Account", bot)
    time.sleep(2)
    print(f"   Bot added!")
    print(f"   Active bots: {list(runner.bots.keys())}")
    if "Trading Bot Account" in runner.bots:
        print(f"   ✓ Bot is in runner!")
    else:
        print(f"   ✗ Bot NOT in runner")
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "="*60)
print("TEST COMPLETED")
print("If you see 'Bot is in runner!' above, then bot is ready!")
print("="*60)

# Stop runner
runner.stop()
