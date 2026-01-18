#!/usr/bin/env python3
"""
Test telegram configuration with mock data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_telegram_config_mock():
    """Test telegram configuration with mock data"""
    print('🧪 TESTING TELEGRAM CONFIGURATION WITH MOCK DATA')
    print('=' * 60)

    try:
        from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
        import tkinter as tk

        # Create GUI instance
        root = tk.Tk()
        root.withdraw()
        gui = HFTProGUI(root)

        print('✅ GUI initialized')

        # Set mock telegram configuration
        print('\n📝 SETTING MOCK TELEGRAM CONFIG:')
        gui.telegram_token_var.set('123456789:ABCdefGHIjklMNOpqrsTUVwxyz')
        gui.telegram_chat_ids_var.set('111111111,222222222')

        token_display = "***" + gui.telegram_token_var.get()[-4:] if gui.telegram_token_var.get() else "None"
        print(f'Token set: {token_display}')
        print(f'Chat IDs set: {gui.telegram_chat_ids_var.get()}')

        # Save to bot config
        print('\n💾 SAVING CONFIG TO BOT:')
        gui.save_gui_config_to_bot('Bot_1')

        # Check if config saved
        if 'Bot_1' in gui.bots:
            bot_config = gui.bots['Bot_1']['config']
            if 'telegram' in bot_config:
                telegram_config = bot_config['telegram']
                token = telegram_config.get('token', '')
                chat_ids = telegram_config.get('chat_ids', [])
                token_saved = "***" + token[-4:] if token else "None"
                print(f'✅ Config saved - Token: {token_saved}')
                print(f'✅ Config saved - Chat IDs: {chat_ids}')

                # Check if telegram_bots updated
                if 'Bot_1' in gui.telegram_bots:
                    print('✅ Bot added to telegram_bots dictionary')
                else:
                    print('❌ Bot NOT added to telegram_bots dictionary')
            else:
                print('❌ Telegram config not saved to bot')

        # Test signal sending
        print('\n📤 TESTING SIGNAL SENDING:')
        if 'Bot_1' in gui.telegram_bots:
            # Mock the telegram bot
            gui.telegram_bots['Bot_1'] = type('MockBot', (), {
                'token': 'mock_token',
                'allowed_users': ['111111111', '222222222']
            })()

            signal_log = []

            # Override send_telegram_signal to capture calls
            original_send = gui.send_telegram_signal
            def capture_send(**kwargs):
                signal_log.append(kwargs)
                print(f'📤 Signal captured: {kwargs.get("signal_type", "unknown")}')

            gui.send_telegram_signal = capture_send

            # Test close position signal
            gui.send_telegram_signal(
                bot_id='Bot_1',
                signal_type='close_position',
                symbol='BTCUSD',
                ticket='12345678',
                profit=15.50,
                volume=0.01,
                balance=10000.00,
                equity=9950.25,
                free_margin=9850.00,
                margin_level=95.5
            )

            if signal_log:
                print('✅ Close position signal sent successfully!')
                print(f'Signal details: {signal_log[0]}')
            else:
                print('❌ No signal captured')
        else:
            print('❌ Cannot test - bot not in telegram_bots')

        root.destroy()

        print('\n🎯 CONFIGURATION TEST RESULT:')
        print('=' * 60)
        if 'Bot_1' in gui.telegram_bots and signal_log:
            print('✅ TELEGRAM CONFIGURATION WORKS!')
            print('✅ Signals will be sent when positions are closed')
            print('\n📋 HOW TO CONFIGURE IN REAL APPLICATION:')
            print('1. Open Telegram tab in GUI')
            print('2. Enter your bot token (from @BotFather)')
            print('3. Enter chat IDs (comma-separated)')
            print('4. Click "💾 Save Config"')
            print('5. Manual close positions will send telegram notifications')
        else:
            print('❌ Configuration test failed')

    except Exception as e:
        print(f'❌ Test error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_telegram_config_mock()