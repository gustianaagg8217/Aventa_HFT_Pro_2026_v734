#!/usr/bin/env python3
"""
Diagnostic test for telegram close position detection issues
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def diagnostic_telegram_close():
    """Diagnose telegram close position issues"""
    print('🔍 DIAGNOSTIC: Close Position Telegram Detection')
    print('=' * 60)

    try:
        from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
        import tkinter as tk

        # Create GUI instance
        root = tk.Tk()
        root.withdraw()
        gui = HFTProGUI(root)

        print('✅ GUI initialized successfully')

        # Check telegram configuration
        print('\n📋 TELEGRAM CONFIGURATION CHECK:')
        print(f'Active bot: {gui.active_bot_id}')
        print(f'Telegram bots count: {len(gui.telegram_bots)}')

        if gui.active_bot_id and gui.active_bot_id in gui.bots:
            bot_config = gui.bots[gui.active_bot_id]['config']
            has_telegram = 'telegram' in bot_config
            print(f'Bot has telegram config: {has_telegram}')

            if has_telegram:
                telegram_config = bot_config['telegram']
                token = telegram_config.get('token', '')
                chat_ids = telegram_config.get('chat_ids', [])
                token_status = "Yes" if token else "No"
                chat_status = "Yes" if chat_ids else "No"
                print(f'Token configured: {token_status}')
                print(f'Chat IDs configured: {chat_status} ({len(chat_ids)} IDs)')

                if token and chat_ids:
                    in_telegram_bots = gui.active_bot_id in gui.telegram_bots
                    print(f'Bot in telegram_bots: {in_telegram_bots}')
                else:
                    print('❌ Telegram config incomplete - token or chat_ids missing')
            else:
                print('❌ No telegram config found in bot configuration')
        else:
            print('❌ No active bot or bot not found')

        # Test MT5 connection
        print('\n🔗 MT5 CONNECTION CHECK:')
        try:
            import MetaTrader5 as mt5
            mt5_connected = mt5.initialize()
            print(f'MT5 initialized: {mt5_connected}')

            if mt5_connected:
                account_info = mt5.account_info()
                if account_info:
                    print(f'Account info available: Yes (Balance: ${account_info.balance:.2f})')
                else:
                    print('Account info available: No')
            else:
                print('❌ MT5 connection failed')
        except Exception as e:
            print(f'❌ MT5 error: {e}')

        # Test telegram signal sending
        print('\n📤 TELEGRAM SIGNAL TEST:')
        if gui.active_bot_id and gui.active_bot_id in gui.telegram_bots:
            try:
                # Mock telegram bot for testing
                gui.telegram_bots[gui.active_bot_id] = type('MockBot', (), {
                    'token': 'test_token',
                    'allowed_users': ['123456789']
                })()

                # Test send signal
                signal_sent = {'called': False}

                original_send = gui.send_telegram_signal
                def mock_send(**kwargs):
                    signal_sent['called'] = True
                    signal_sent['kwargs'] = kwargs
                    print(f'📤 Signal sent: {kwargs.get("signal_type", "unknown")}')

                gui.send_telegram_signal = mock_send

                # Simulate close position signal
                gui.send_telegram_signal(
                    bot_id=gui.active_bot_id,
                    signal_type='close_position',
                    symbol='XAUUSD',
                    ticket='12345678',
                    profit=15.50,
                    volume=0.01,
                    balance=10000.00,
                    equity=9950.25,
                    free_margin=9850.00,
                    margin_level=95.5
                )

                if signal_sent['called']:
                    print('✅ Telegram signal method called successfully')
                else:
                    print('❌ Telegram signal method not called')

            except Exception as e:
                print(f'❌ Telegram signal test error: {e}')
        else:
            print('❌ Bot not in telegram_bots - cannot send signals')

        root.destroy()

        print('\n🎯 DIAGNOSIS SUMMARY:')
        print('=' * 60)

        issues = []

        if not (gui.active_bot_id and gui.active_bot_id in gui.bots):
            issues.append('❌ No active bot configured')

        if gui.active_bot_id and gui.active_bot_id in gui.bots:
            bot_config = gui.bots[gui.active_bot_id]['config']
            if 'telegram' not in bot_config:
                issues.append('❌ Telegram config missing from bot')
            else:
                telegram_config = bot_config['telegram']
                if not telegram_config.get('token'):
                    issues.append('❌ Telegram token not configured')
                if not telegram_config.get('chat_ids'):
                    issues.append('❌ Telegram chat IDs not configured')

        if gui.active_bot_id and gui.active_bot_id not in gui.telegram_bots:
            issues.append('❌ Bot not initialized in telegram_bots dictionary')

        try:
            import MetaTrader5 as mt5
            if not mt5.initialize():
                issues.append('❌ MT5 connection failed')
        except:
            issues.append('❌ MT5 import/connection error')

        if issues:
            print('ISSUES FOUND:')
            for issue in issues:
                print(f'  {issue}')
            print('\n🔧 SOLUTIONS:')
            print('  1. Configure Telegram in Telegram tab (Token + Chat IDs)')
            print('  2. Save configuration with "💾 Save Config"')
            print('  3. Ensure MT5 is running and connected')
            print('  4. Restart the application if needed')
        else:
            print('✅ No issues detected - telegram should work')
            print('If still not working, check:')
            print('  - Telegram bot token validity')
            print('  - Chat IDs are correct')
            print('  - Internet connection')
            print('  - Telegram bot permissions')

    except Exception as e:
        print(f'❌ Diagnostic error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    diagnostic_telegram_close()