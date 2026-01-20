#!/usr/bin/env python3
"""
Example: Using Telegram Bot Control from Python Script
Demonstrates programmatic control of bots via IPC
"""

import sys
import os
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_control_ipc import get_ipc


def example_1_list_bots():
    """Example 1: List all bots and their status"""
    print("\n" + "="*60)
    print("Example 1: List All Bots")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    bots = ipc.get_all_bots()
    
    print("Current Bot Status:\n")
    for bot_id, status in bots.items():
        is_running = status.get('is_running', False)
        emoji = "🟢" if is_running else "🔴"
        status_text = "RUNNING" if is_running else "STOPPED"
        
        print(f"{emoji} {bot_id}")
        print(f"   Status: {status_text}")
        print(f"   Symbol: {status.get('symbol', 'N/A')}")
        print(f"   Magic: {status.get('magic_number', 'N/A')}")
        print(f"   Updated: {status.get('updated_at', 'N/A')}")
        print()


def example_2_send_start_command():
    """Example 2: Send start command programmatically"""
    print("\n" + "="*60)
    print("Example 2: Send Start Command")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Check if bot exists
    bot_id = "Bot_1"
    bot_status = ipc.get_bot_status(bot_id)
    
    if bot_status is None:
        print(f"❌ Bot {bot_id} not found")
        return
    
    if bot_status.get('is_running', False):
        print(f"⚠️  Bot {bot_id} is already running")
        return
    
    # Send start command
    print(f"Sending start command for {bot_id}...")
    cmd_id = ipc.send_command('start', bot_id, 123456789, 'script_user')
    print(f"✅ Command sent (ID: {cmd_id})\n")
    
    # Wait for response
    print("Waiting for response (max 5 seconds)...")
    response = ipc.get_latest_response(cmd_id, timeout=5.0)
    
    if response:
        if response.get('success'):
            print(f"✅ Success: {response.get('message')}\n")
        else:
            print(f"❌ Failed: {response.get('message')}\n")
    else:
        print("⏱️  Timeout: No response received\n")


def example_3_send_stop_command():
    """Example 3: Send stop command programmatically"""
    print("\n" + "="*60)
    print("Example 3: Send Stop Command")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Check if bot exists
    bot_id = "Bot_1"
    bot_status = ipc.get_bot_status(bot_id)
    
    if bot_status is None:
        print(f"❌ Bot {bot_id} not found")
        return
    
    if not bot_status.get('is_running', False):
        print(f"⚠️  Bot {bot_id} is already stopped")
        return
    
    # Send stop command
    print(f"Sending stop command for {bot_id}...")
    cmd_id = ipc.send_command('stop', bot_id, 123456789, 'script_user')
    print(f"✅ Command sent (ID: {cmd_id})\n")
    
    # Wait for response
    print("Waiting for response (max 5 seconds)...")
    response = ipc.get_latest_response(cmd_id, timeout=5.0)
    
    if response:
        if response.get('success'):
            print(f"✅ Success: {response.get('message')}\n")
        else:
            print(f"❌ Failed: {response.get('message')}\n")
    else:
        print("⏱️  Timeout: No response received\n")


def example_4_monitor_status():
    """Example 4: Monitor bot status changes"""
    print("\n" + "="*60)
    print("Example 4: Monitor Bot Status Changes")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    print("Monitoring bot status (30 seconds)...\n")
    
    previous_status = {}
    start_time = time.time()
    
    while time.time() - start_time < 30:
        bots = ipc.get_all_bots()
        
        # Check for changes
        for bot_id, current in bots.items():
            previous = previous_status.get(bot_id, {})
            
            if previous.get('is_running') != current.get('is_running'):
                emoji = "🟢" if current.get('is_running') else "🔴"
                status = "STARTED" if current.get('is_running') else "STOPPED"
                print(f"[{time.strftime('%H:%M:%S')}] {emoji} Bot {bot_id} {status}")
        
        previous_status = bots
        time.sleep(1)
    
    print("\nMonitoring complete.\n")


def example_5_batch_control():
    """Example 5: Control multiple bots"""
    print("\n" + "="*60)
    print("Example 5: Batch Bot Control")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    bots = ipc.get_all_bots()
    
    if not bots:
        print("❌ No bots found")
        return
    
    running_bots = [bot_id for bot_id, status in bots.items() 
                    if status.get('is_running', False)]
    
    print(f"Found {len(running_bots)} running bot(s):\n")
    
    # Stop all running bots
    for bot_id in running_bots:
        print(f"Stopping {bot_id}...")
        cmd_id = ipc.send_command('stop', bot_id, 123456789, 'batch_script')
        
        response = ipc.get_latest_response(cmd_id, timeout=3.0)
        if response and response.get('success'):
            print(f"✅ {bot_id} stopped\n")
        else:
            print(f"❌ {bot_id} failed\n")
    
    print("Batch control complete.\n")


def example_6_check_pending_commands():
    """Example 6: Check pending commands"""
    print("\n" + "="*60)
    print("Example 6: Check Pending Commands")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    pending = ipc.get_pending_commands()
    
    if not pending:
        print("No pending commands\n")
        return
    
    print(f"Pending commands ({len(pending)}):\n")
    
    for cmd in pending:
        print(f"ID: {cmd['command_id'][:8]}...")
        print(f"Command: {cmd['command']}")
        print(f"Bot: {cmd['bot_id']}")
        print(f"User: @{cmd.get('username', 'unknown')}")
        print(f"Time: {cmd['timestamp']}")
        print()


def example_7_simulate_telegram_request():
    """Example 7: Simulate Telegram API request"""
    print("\n" + "="*60)
    print("Example 7: Simulate Telegram Request")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Simulate user sending /start_bot Bot_1 via Telegram
    user_id = 123456789
    username = "example_user"
    bot_id = "Bot_1"
    
    print(f"Simulating: User @{username} sends /start_bot {bot_id}\n")
    
    # 1. Telegram validates user
    print("1. Validating user authorization...")
    allowed_users = [123456789]  # Example whitelist
    
    if user_id not in allowed_users:
        print("❌ Unauthorized\n")
        return
    
    print("✅ User authorized\n")
    
    # 2. Telegram checks bot exists
    print("2. Checking if bot exists...")
    bot_status = ipc.get_bot_status(bot_id)
    
    if bot_status is None:
        print(f"❌ Bot {bot_id} not found\n")
        return
    
    print(f"✅ Bot found (Status: {'RUNNING' if bot_status.get('is_running') else 'STOPPED'})\n")
    
    # 3. Send command to GUI
    print("3. Sending command to GUI...")
    cmd_id = ipc.send_command('start', bot_id, user_id, username)
    print(f"✅ Command sent\n")
    
    # 4. Wait for response
    print("4. Waiting for GUI response...")
    response = ipc.get_latest_response(cmd_id, timeout=5.0)
    
    if response:
        print("✅ Response received\n")
        
        # 5. Send to user
        print("5. Sending response to user...")
        if response.get('success'):
            print(f"Message to @{username}:")
            print(f"✅ Bot Started!")
            print(f"🟢 Status: TRADING ACTIVE\n")
        else:
            print(f"Message to @{username}:")
            print(f"❌ Failed to start bot")
            print(f"Error: {response.get('message')}\n")
    else:
        print("⏱️  Response timeout\n")


def example_8_export_bot_data():
    """Example 8: Export bot data to JSON"""
    print("\n" + "="*60)
    print("Example 8: Export Bot Data")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    bots = ipc.get_all_bots()
    
    # Create export data
    export_data = {
        'timestamp': time.time(),
        'bots': bots,
        'summary': {
            'total': len(bots),
            'running': sum(1 for b in bots.values() if b.get('is_running')),
            'stopped': sum(1 for b in bots.values() if not b.get('is_running'))
        }
    }
    
    # Save to file
    filename = 'bot_export.json'
    with open(filename, 'w') as f:
        json.dump(export_data, f, indent=4)
    
    print(f"✅ Exported to {filename}\n")
    print(f"Summary:")
    print(f"  Total bots: {export_data['summary']['total']}")
    print(f"  Running: {export_data['summary']['running']}")
    print(f"  Stopped: {export_data['summary']['stopped']}\n")


def main():
    """Run all examples"""
    print("\n" + "="*70)
    print(" 📚 TELEGRAM BOT CONTROL - USAGE EXAMPLES")
    print("="*70)
    
    examples = [
        ("List All Bots", example_1_list_bots),
        ("Send Start Command", example_2_send_start_command),
        ("Send Stop Command", example_3_send_stop_command),
        ("Monitor Status Changes", example_4_monitor_status),
        ("Batch Bot Control", example_5_batch_control),
        ("Check Pending Commands", example_6_check_pending_commands),
        ("Simulate Telegram Request", example_7_simulate_telegram_request),
        ("Export Bot Data", example_8_export_bot_data),
    ]
    
    print("\nAvailable Examples:\n")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    print("\nRun with: python examples_telegram_bot_control.py <number>")
    print("Example:  python examples_telegram_bot_control.py 1\n")
    
    if len(sys.argv) > 1:
        try:
            example_num = int(sys.argv[1]) - 1
            if 0 <= example_num < len(examples):
                name, func = examples[example_num]
                func()
            else:
                print(f"❌ Invalid example number: {example_num + 1}")
        except ValueError:
            print(f"❌ Invalid input: {sys.argv[1]}")
    else:
        print("Choose an example number above and run the command.\n")


if __name__ == "__main__":
    main()
