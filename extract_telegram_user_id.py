"""
Extract User ID from Telegram Message
Run this to get YOUR actual User ID from Telegram
"""

import json
import time
from telegram_bot import TelegramBot

def extract_user_id():
    """Listen for first message and extract user ID"""
    
    print("="*70)
    print("USER ID EXTRACTOR")
    print("="*70)
    print("\nWaiting for your Telegram message...")
    print("\nTo get your User ID:")
    print("  1. Send ANY message to the Telegram bot (e.g., 'hello' or '/start')")
    print("  2. This script will capture and display your User ID")
    print("  3. Then use that ID in the GUI")
    print("\nScript will exit after 2 minutes if no message received")
    print("\n" + "="*70)
    
    # Load config
    config_file = "configs/telegram_hft_config.json"
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    token = config['telegram'].get('token', '')
    chat_ids = config['telegram'].get('chat_ids', [])
    
    # Create bot - but allow ALL users temporarily
    print("\nCreating bot in DEBUG mode (accepting all users)...")
    bot = TelegramBot(token, chat_ids)
    
    # Override is_authorized to capture any user
    original_is_authorized = bot.is_authorized
    user_found = {'id': None}
    
    def capture_user_id(user_id):
        user_found['id'] = user_id
        return True
    
    bot.is_authorized = capture_user_id
    
    # Monkey-patch handler to print user ID
    original_status = bot.cmd_status
    
    async def debug_status(update, context):
        if user_found['id'] is None:
            print(f"\n{'='*70}")
            print(f"✓ FOUND YOUR USER ID: {update.effective_user.id}")
            print(f"{'='*70}")
            print(f"\nYour Telegram ID: {update.effective_user.id}")
            print(f"Username: {update.effective_user.username or 'N/A'}")
            print(f"First name: {update.effective_user.first_name or 'N/A'}")
            user_found['id'] = update.effective_user.id
            
            await update.message.reply_text(
                f"✓ Your User ID is: **{update.effective_user.id}**\n\n"
                f"Use this ID in the GUI (not the old one)!",
                parse_mode='Markdown'
            )
        else:
            await original_status(update, context)
    
    bot.cmd_status = debug_status
    
    # Start bot polling
    print("Starting bot (monitoring for incoming messages)...")
    from telegram_bot_runner import get_bot_runner
    
    runner = get_bot_runner()
    runner.start()
    runner.add_bot("Debug", bot)
    
    print("Waiting for your Telegram message (2 minute timeout)...")
    
    # Wait for user message
    start_time = time.time()
    timeout = 120  # 2 minutes
    
    while (time.time() - start_time) < timeout:
        if user_found['id'] is not None:
            print(f"\n{'='*70}")
            print("UPDATE YOUR GUI:")
            print(f"{'='*70}")
            print(f"\nChange Chat IDs field to: {user_found['id']}")
            print(f"\nThen click 'Save Configuration'")
            print(f"Bot will now recognize your commands!")
            print(f"\n{'='*70}\n")
            
            time.sleep(5)
            runner.stop()
            return user_found['id']
        
        time.sleep(0.5)
    
    # Timeout
    print(f"\nTimeout! No message received in 2 minutes")
    runner.stop()
    return None

if __name__ == "__main__":
    user_id = extract_user_id()
    if user_id:
        print(f"✓ User ID captured: {user_id}")
    else:
        print(f"✗ Failed to get User ID")
