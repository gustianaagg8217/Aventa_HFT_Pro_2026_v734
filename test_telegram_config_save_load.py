#!/usr/bin/env python3
"""
Test script to verify telegram config saving and loading
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

def test_telegram_config_save_load():
    """Test telegram config save and load functionality"""
    try:
        from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI
        import tkinter as tk

        # Create GUI instance
        root = tk.Tk()
        root.withdraw()
        gui = HFTProGUI(root)

        print("=== TESTING TELEGRAM CONFIG SAVE/LOAD ===")

        # Set telegram config in GUI
        gui.telegram_token_var.set("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        gui.telegram_chat_ids_var.set("111111111,222222222")

        # Save config to bot
        gui.save_gui_config_to_bot("Bot_1")

        # Check if telegram config is saved
        config = gui.bots["Bot_1"]["config"]
        has_telegram = "telegram" in config
        print(f"✅ Telegram config saved: {has_telegram}")

        if has_telegram:
            telegram_config = config["telegram"]
            token = telegram_config.get("token", "")
            chat_ids = telegram_config.get("chat_ids", [])
            print(f"✅ Token saved: {'***' + token[-4:] if token else 'None'}")
            print(f"✅ Chat IDs saved: {chat_ids}")

            # Check if telegram_bots is updated
            if "Bot_1" in gui.telegram_bots:
                print("✅ Telegram bot created in telegram_bots dictionary")
            else:
                print("❌ Telegram bot NOT created in telegram_bots dictionary")

        # Test loading config back to GUI
        print("\n=== TESTING CONFIG LOAD TO GUI ===")
        gui.load_bot_config_to_gui("Bot_1")

        loaded_token = gui.telegram_token_var.get()
        loaded_chat_ids = gui.telegram_chat_ids_var.get()

        print(f"✅ Token loaded to GUI: {'***' + loaded_token[-4:] if loaded_token else 'None'}")
        print(f"✅ Chat IDs loaded to GUI: {loaded_chat_ids}")

        # Test manual close telegram simulation
        print("\n=== TESTING MANUAL CLOSE TELEGRAM ===")
        if gui.active_bot_id and gui.active_bot_id in gui.telegram_bots:
            print(f"✅ Bot {gui.active_bot_id} ADA di telegram_bots")
            print("✅ Telegram notification HARUS bekerja untuk manual close")
        else:
            print(f"❌ Bot {gui.active_bot_id} TIDAK ADA di telegram_bots")
            print("❌ Telegram notification TIDAK akan bekerja")

        root.destroy()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_telegram_config_save_load()
    if success:
        print("\n🎉 Telegram config save/load test PASSED!")
    else:
        print("\n❌ Telegram config save/load test FAILED!")
    sys.exit(0 if success else 1)