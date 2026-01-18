#!/usr/bin/env python3
"""
Simple test to check telegram config in session file
"""

import json
import os

def check_session_telegram_config():
    """Check if telegram config is saved in session file"""
    session_file = 'hft_session.json'
    if os.path.exists(session_file):
        with open(session_file, 'r') as f:
            data = json.load(f)

        bots = data.get('bots', {})
        print(f'Found {len(bots)} bots in session')

        for bot_id, bot_data in bots.items():
            config = bot_data.get('config', {})
            telegram = config.get('telegram', {})
            if telegram:
                token = telegram.get('token', '')
                chat_ids = telegram.get('chat_ids', [])
                token_display = "***" + token[-4:] if token else "None"
                print(f'Bot {bot_id}: Token={token_display} ChatIDs={chat_ids}')
            else:
                print(f'Bot {bot_id}: No telegram config')
    else:
        print('No session file found')

if __name__ == "__main__":
    check_session_telegram_config()