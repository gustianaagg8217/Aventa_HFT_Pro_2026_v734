"""
Telegram Bot Manual Starter
Run this in separate terminal to start bot polling
"""

import json
import os
import time
import sys

def main():
    print("="*70)
    print("TELEGRAM BOT MANUAL STARTER")
    print("="*70)
    
    # Load config
    config_file = "configs/telegram_hft_config.json"
    print(f"\n1. Loading config from: {config_file}")
    
    if not os.path.exists(config_file):
        print(f"   ERROR: Config file not found!")
        print(f"   Please save Telegram config in GUI first")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"   ERROR loading config: {e}")
        return False
    
    if 'telegram' not in config:
        print("   ERROR: No Telegram config in file!")
        print("   Please save Telegram config in GUI first")
        return False
    
    token = config['telegram'].get('token', '')
    chat_ids = config['telegram'].get('chat_ids', [])
    
    if not token:
        print("   ERROR: No bot token!")
        return False
    
    if not chat_ids:
        print("   ERROR: No chat IDs!")
        return False
    
    print(f"   ✓ Config loaded")
    print(f"     Token: {token[:20]}...")
    print(f"     Chat IDs: {chat_ids}")
    
    # Create bot
    print(f"\n2. Creating TelegramBot instance...")
    try:
        from telegram_bot import TelegramBot
        bot = TelegramBot(token, chat_ids)
        print(f"   ✓ Bot created successfully")
        print(f"     Allowed users: {bot.allowed_users}")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Get runner
    print(f"\n3. Creating bot runner...")
    try:
        from telegram_bot_runner import get_bot_runner
        runner = get_bot_runner()
        print(f"   ✓ Runner created")
    except Exception as e:
        print(f"   ERROR: {e}")
        return False
    
    # Start runner
    print(f"\n4. Starting event loop...")
    runner.start()
    time.sleep(1)
    
    if runner.loop and runner.loop.is_running():
        print(f"   ✓ Event loop is RUNNING")
    else:
        print(f"   ✗ Event loop failed to start")
        return False
    
    # Add bot
    print(f"\n5. Adding bot to runner...")
    try:
        runner.add_bot("Trading Bot Account", bot)
        time.sleep(2)
        
        if "Trading Bot Account" in runner.bots:
            print(f"   ✓ Bot is polling Telegram updates")
        else:
            print(f"   ✗ Bot not found in runner")
            return False
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Success
    print(f"\n" + "="*70)
    print("✓ TELEGRAM BOT IS RUNNING")
    print("="*70)
    print(f"\nBot Status:")
    print(f"  - Bot Name: Trading Bot Account")
    print(f"  - Event Loop: ACTIVE")
    print(f"  - Polling: ACTIVE")
    print(f"  - Chat ID: {chat_ids[0]}")
    print(f"\nYou can now:")
    print(f"  1. Open GUI Launcher: python Aventa_HFT_Pro_2026_v7_3_3.py")
    print(f"  2. Send Telegram commands:")
    print(f"     /bots                    - List all bots")
    print(f"     /start_bot Trading Bot Account - Start bot")
    print(f"     /stop_bot Trading Bot Account  - Stop bot")
    print(f"\nBot will respond to your commands!")
    print(f"\nPress Ctrl+C to stop the bot")
    print("="*70 + "\n")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nShutting down bot...")
        runner.stop()
        print("✓ Bot stopped")
        print("Goodbye!")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
