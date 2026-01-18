#!/usr/bin/env python3
"""
Test script to check telegram bot configuration status
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def check_telegram_status():
    """Check telegram bot configuration status"""
    try:
        from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
        import tkinter as tk

        # Create GUI instance
        root = tk.Tk()
        root.withdraw()
        gui = HFTProGUI(root)

        print('=== TELEGRAM BOTS STATUS ===')
        print(f'telegram_bots dictionary: {gui.telegram_bots}')
        print(f'Jumlah bot di telegram_bots: {len(gui.telegram_bots)}')

        print('\n=== BOTS STATUS ===')
        print(f'Jumlah bot di self.bots: {len(gui.bots)}')
        for bot_id in gui.bots:
            print(f'Bot: {bot_id}')
            config = gui.bots[bot_id]['config']
            has_telegram = 'telegram' in config
            print(f'  Has telegram config: {has_telegram}')
            if has_telegram:
                telegram_config = config['telegram']
                token = telegram_config.get('token', '')
                chat_ids = telegram_config.get('chat_ids', [])
                token_display = "***" + token[-4:] if token else "None"
                print(f'  Token: {token_display}')
                print(f'  Chat IDs: {chat_ids}')

        print('\n=== ACTIVE BOT ===')
        print(f'Active bot ID: {gui.active_bot_id}')

        # Test manual close telegram simulation
        print('\n=== TESTING MANUAL CLOSE TELEGRAM ===')
        if gui.active_bot_id and gui.active_bot_id in gui.telegram_bots:
            print(f'✅ Bot {gui.active_bot_id} ADA di telegram_bots')
            print('✅ Telegram notification HARUS bekerja')
        else:
            print(f'❌ Bot {gui.active_bot_id} TIDAK ADA di telegram_bots')
            print('❌ Telegram notification TIDAK akan bekerja')
            print('Solusi: Pastikan telegram token dan chat IDs sudah dikonfigurasi di Telegram tab')

        root.destroy()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    check_telegram_status()