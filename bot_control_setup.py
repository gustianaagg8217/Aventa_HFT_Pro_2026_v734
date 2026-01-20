"""
Bot Control Setup Helper
Quick setup script untuk mengaktifkan Telegram bot control
"""

import json
import os
from pathlib import Path


def setup_telegram_control():
    """Initialize bot control system"""
    
    print("\n" + "="*60)
    print("🤖 Aventa HFT Pro - Bot Control Setup")
    print("="*60 + "\n")
    
    # Create .ipc directory
    ipc_dir = Path(".ipc")
    ipc_dir.mkdir(exist_ok=True)
    print("✅ Created .ipc directory for IPC communication\n")
    
    # Initialize bot_status.json
    bot_status_file = ipc_dir / "bot_status.json"
    if not bot_status_file.exists():
        initial_status = {
            "bots": {},
            "updated_at": "2026-01-20T00:00:00.000000"
        }
        with open(bot_status_file, 'w') as f:
            json.dump(initial_status, f, indent=4)
        print("✅ Initialized bot_status.json\n")
    else:
        print("✓ bot_status.json already exists\n")
    
    # Initialize bot_commands.json
    bot_commands_file = ipc_dir / "bot_commands.json"
    if not bot_commands_file.exists():
        initial_commands = {
            "commands": [],
            "updated_at": "2026-01-20T00:00:00.000000"
        }
        with open(bot_commands_file, 'w') as f:
            json.dump(initial_commands, f, indent=4)
        print("✅ Initialized bot_commands.json\n")
    else:
        print("✓ bot_commands.json already exists\n")
    
    # Initialize bot_responses.json
    bot_responses_file = ipc_dir / "bot_responses.json"
    if not bot_responses_file.exists():
        initial_responses = {
            "responses": []
        }
        with open(bot_responses_file, 'w') as f:
            json.dump(initial_responses, f, indent=4)
        print("✅ Initialized bot_responses.json\n")
    else:
        print("✓ bot_responses.json already exists\n")
    
    print("="*60)
    print("✅ Bot Control System Ready!")
    print("="*60 + "\n")
    
    print("📋 Configuration Summary:\n")
    print("Token        : 8531073542:AAENQ-O9fnaHpFCvBB11xxa9vWq5aT22hLA")
    print("Bot Name     : Aventa HFT Pro 2026 v733")
    print("IPC Location : .ipc/")
    print()
    
    print("📱 Available Telegram Commands:\n")
    print("  /bots                - List all bots and their status")
    print("  /start_bot <bot_id>  - Start specific bot")
    print("  /stop_bot <bot_id>   - Stop specific bot")
    print("  /status              - System status")
    print("  /help                - Show all commands")
    print()
    
    print("🚀 Next Steps:\n")
    print("  1. Run the GUI Launcher (Aventa_HFT_Pro_2026_v7_3_3.py)")
    print("  2. Configure Telegram in the GUI (Tab: 📱 Telegram Service)")
    print("  3. Add your user ID to allowed_users in telegram_bot.py")
    print("  4. Send commands from Telegram:")
    print("     /bots")
    print("     /start_bot Bot_1")
    print()
    
    print("📖 Documentation:\n")
    print("  See TELEGRAM_CONTROL_GUIDE.md for detailed usage guide")
    print()
    
    print("="*60 + "\n")


def verify_setup():
    """Verify bot control setup"""
    
    print("\n" + "="*60)
    print("🔍 Verifying Bot Control Setup")
    print("="*60 + "\n")
    
    all_ok = True
    
    # Check .ipc directory
    ipc_dir = Path(".ipc")
    if ipc_dir.exists():
        print("✅ .ipc directory exists")
    else:
        print("❌ .ipc directory NOT found")
        all_ok = False
    
    # Check bot_control_ipc.py
    if os.path.exists("bot_control_ipc.py"):
        print("✅ bot_control_ipc.py exists")
    else:
        print("❌ bot_control_ipc.py NOT found")
        all_ok = False
    
    # Check gui_telegram_integration.py
    if os.path.exists("gui_telegram_integration.py"):
        print("✅ gui_telegram_integration.py exists")
    else:
        print("❌ gui_telegram_integration.py NOT found")
        all_ok = False
    
    # Check bot_status.json
    bot_status_file = ipc_dir / "bot_status.json"
    if bot_status_file.exists():
        print("✅ bot_status.json exists")
        try:
            with open(bot_status_file, 'r') as f:
                data = json.load(f)
                print(f"   └─ Bots configured: {len(data.get('bots', {}))}")
        except:
            print("   ⚠️  bot_status.json is corrupted")
            all_ok = False
    else:
        print("❌ bot_status.json NOT found")
        all_ok = False
    
    # Check bot_commands.json
    bot_commands_file = ipc_dir / "bot_commands.json"
    if bot_commands_file.exists():
        print("✅ bot_commands.json exists")
    else:
        print("❌ bot_commands.json NOT found")
        all_ok = False
    
    # Check telegram_bot.py imports
    try:
        with open("telegram_bot.py", 'r') as f:
            content = f.read()
            if "from bot_control_ipc import" in content:
                print("✅ telegram_bot.py has IPC integration")
            else:
                print("❌ telegram_bot.py missing IPC integration")
                all_ok = False
    except:
        print("❌ Cannot read telegram_bot.py")
        all_ok = False
    
    # Check GUI file imports
    try:
        with open("Aventa_HFT_Pro_2026_v7_3_3.py", 'r') as f:
            content = f.read()
            if "from gui_telegram_integration import" in content:
                print("✅ Aventa_HFT_Pro_2026_v7_3_3.py has GUI integration")
            else:
                print("❌ Aventa_HFT_Pro_2026_v7_3_3.py missing GUI integration")
                all_ok = False
    except:
        print("❌ Cannot read Aventa_HFT_Pro_2026_v7_3_3.py")
        all_ok = False
    
    print()
    if all_ok:
        print("✅ All checks passed! Bot control system is ready to use.")
    else:
        print("❌ Some checks failed. Please run setup_telegram_control() first.")
    
    print("="*60 + "\n")
    
    return all_ok


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        verify_setup()
    else:
        setup_telegram_control()
        verify_setup()
