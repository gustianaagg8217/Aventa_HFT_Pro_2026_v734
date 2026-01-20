"""
Debug script untuk check Telegram Bot status
"""

import json
import os
from telegram_bot_runner import get_bot_runner
from bot_control_ipc import get_ipc

def check_bot_status():
    print("=" * 60)
    print("TELEGRAM BOT DEBUG CHECK")
    print("=" * 60)
    
    # Check 1: IPC Status
    print("\n1. Checking IPC Files...")
    ipc = get_ipc()
    bots = ipc.get_all_bots()
    print(f"   Bots in IPC: {list(bots.keys())}")
    for bot_id, status in bots.items():
        print(f"   - {bot_id}: {status}")
    
    # Check 2: Config File
    print("\n2. Checking Config File...")
    config_file = "configs/telegram_hft_config.json"
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        if 'telegram' in config:
            print(f"   Telegram Token: {config['telegram'].get('token', 'NOT SET')[:20]}...")
            print(f"   Chat IDs: {config['telegram'].get('chat_ids', [])}")
        else:
            print("   NO TELEGRAM CONFIG FOUND!")
    else:
        print(f"   Config file not found: {config_file}")
    
    # Check 3: Bot Runner Status
    print("\n3. Checking Bot Runner...")
    runner = get_bot_runner()
    print(f"   Runner running: {runner.running}")
    print(f"   Event loop: {runner.loop}")
    print(f"   Active bots: {list(runner.bots.keys())}")
    
    # Check 4: Try to manually load telegram config
    print("\n4. Checking Telegram Module...")
    try:
        from telegram_bot import TelegramBot
        
        # Load config
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            if 'telegram' in config:
                token = config['telegram'].get('token', '')
                chat_ids = config['telegram'].get('chat_ids', [])
                
                print(f"   Creating TelegramBot...")
                print(f"   Token length: {len(token)}")
                print(f"   Chat IDs: {chat_ids}")
                
                bot = TelegramBot(token, chat_ids)
                print(f"   Bot created successfully!")
                print(f"   Bot allowed_users: {bot.allowed_users}")
                print(f"   Bot app: {bot.app}")
            else:
                print("   NO TELEGRAM CONFIG IN FILE!")
        else:
            print("   Config file missing!")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("END DEBUG CHECK")
    print("=" * 60)

if __name__ == "__main__":
    check_bot_status()
