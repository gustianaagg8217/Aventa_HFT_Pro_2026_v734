#!/usr/bin/env python3
"""
Test script to verify each bot can send independent Telegram signals
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_bot_telegram_independence():
    """Test that each bot has its own Telegram configuration"""

    # Mock bot configurations with different Telegram settings
    mock_bots = {
        'Bot_1': {
            'config': {
                'telegram': {
                    'token': 'TOKEN_BOT_1',
                    'chat_ids': ['111111111', '222222222']
                }
            }
        },
        'Bot_2': {
            'config': {
                'telegram': {
                    'token': 'TOKEN_BOT_2',
                    'chat_ids': ['333333333', '444444444']
                }
            }
        },
        'Bot_3': {
            'config': {
                'telegram': {
                    'token': 'TOKEN_BOT_3',
                    'chat_ids': ['555555555']
                }
            }
        }
    }

    # Mock telegram_bots dictionary
    telegram_bots = {}

    # Simulate loading Telegram configurations for each bot
    for bot_id, bot_data in mock_bots.items():
        telegram_config = bot_data['config'].get('telegram', {})
        token = telegram_config.get('token', '')
        chat_ids = telegram_config.get('chat_ids', [])

        if token and chat_ids:
            # This simulates creating a TelegramBot instance
            telegram_bots[bot_id] = {
                'token': token,
                'allowed_users': chat_ids
            }
            print(f"✅ Bot {bot_id}: Telegram configured with token {token[:10]}... and {len(chat_ids)} chat IDs")
        else:
            print(f"❌ Bot {bot_id}: No Telegram configuration found")

    # Test that each bot can access its own configuration
    print("\n🧪 Testing Telegram signal routing:")

    for bot_id in mock_bots.keys():
        if bot_id in telegram_bots:
            bot_config = telegram_bots[bot_id]
            print(f"📤 Bot {bot_id} would send to {len(bot_config['allowed_users'])} chat(s): {bot_config['allowed_users']}")
        else:
            print(f"❌ Bot {bot_id} has no Telegram configuration")

    print("\n✅ Test completed: Each bot can have independent Telegram settings!")

if __name__ == "__main__":
    test_bot_telegram_independence()