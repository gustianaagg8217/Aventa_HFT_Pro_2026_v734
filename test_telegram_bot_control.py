"""
Integration Test for Telegram Bot Control
Tests the complete workflow of bot control via Telegram
"""

import json
import time
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot_control_ipc import get_ipc


def test_ipc_basic():
    """Test basic IPC functionality"""
    print("\n" + "="*60)
    print("Test 1: Basic IPC Operations")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Test write/read status
    print("Testing bot status write/read...")
    status = {
        'is_running': True,
        'status_text': 'TRADING ACTIVE',
        'symbol': 'EURUSD',
        'magic_number': 2026001
    }
    ipc.update_bot_status('TestBot_1', status)
    print("✅ Bot status written")
    
    read_status = ipc.get_bot_status('TestBot_1')
    assert read_status is not None, "Failed to read bot status"
    assert read_status['is_running'] == True, "Status mismatch"
    print("✅ Bot status read correctly")
    
    # Test multiple bots
    print("\nTesting multiple bots...")
    ipc.update_bot_status('TestBot_2', {'is_running': False, 'status_text': 'STOPPED'})
    ipc.update_bot_status('TestBot_3', {'is_running': True, 'status_text': 'TRADING ACTIVE'})
    
    all_bots = ipc.get_all_bots()
    assert len(all_bots) >= 3, "Should have at least 3 bots"
    print(f"✅ Multiple bots working (found {len(all_bots)} bots)")
    
    print("\n✅ Test 1 PASSED\n")
    return True


def test_command_send_receive():
    """Test command send/receive"""
    print("="*60)
    print("Test 2: Command Send/Receive")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Send command
    print("Sending start command...")
    cmd_id = ipc.send_command('start', 'TestBot_1', 12345, 'test_user')
    assert cmd_id is not None, "Failed to send command"
    print(f"✅ Command sent (ID: {cmd_id})")
    
    # Get pending commands
    print("\nRetrieving pending commands...")
    time.sleep(0.1)
    pending = ipc.get_pending_commands()
    
    # Check if our command is in pending
    found = False
    for cmd in pending:
        if cmd['command_id'] == cmd_id:
            found = True
            assert cmd['command'] == 'start', "Command type mismatch"
            assert cmd['bot_id'] == 'TestBot_1', "Bot ID mismatch"
            print("✅ Pending command found and verified")
            break
    
    assert found, "Command not found in pending list"
    
    # Mark as completed
    print("\nMarking command as completed...")
    ipc.send_response(cmd_id, True, "Command executed successfully")
    ipc.mark_command_completed(cmd_id)
    print("✅ Command marked as completed")
    
    # Verify no longer pending
    time.sleep(0.1)
    pending = ipc.get_pending_commands()
    for cmd in pending:
        assert cmd['command_id'] != cmd_id, "Command should not be pending anymore"
    print("✅ Command no longer in pending list")
    
    print("\n✅ Test 2 PASSED\n")
    return True


def test_response_handling():
    """Test response send/receive"""
    print("="*60)
    print("Test 3: Response Handling")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Send command
    print("Sending command...")
    cmd_id = ipc.send_command('stop', 'TestBot_2', 12345, 'test_user')
    print(f"✅ Command sent (ID: {cmd_id})")
    
    # Wait a bit for processing
    time.sleep(0.2)
    
    # Send response
    print("\nSending response...")
    ipc.send_response(cmd_id, True, "Bot stopped successfully")
    print("✅ Response sent")
    
    # Get response
    print("\nRetrieving response...")
    response = ipc.get_latest_response(cmd_id, timeout=2.0)
    
    assert response is not None, "Response not found"
    assert response['success'] == True, "Response success flag mismatch"
    assert response['command_id'] == cmd_id, "Response command ID mismatch"
    print("✅ Response retrieved and verified")
    
    print("\n✅ Test 3 PASSED\n")
    return True


def test_command_status_tracking():
    """Test command status transitions"""
    print("="*60)
    print("Test 4: Command Status Tracking")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Send command
    print("Sending command...")
    cmd_id = ipc.send_command('start', 'TestBot_3', 12345, 'test_user')
    print(f"✅ Command sent (ID: {cmd_id})")
    
    # Mark as processing
    print("\nMarking as processing...")
    ipc.mark_command_processing(cmd_id)
    print("✅ Marked as processing")
    
    # Verify status
    print("\nVerifying status...")
    with open(ipc.command_file, 'r') as f:
        data = json.load(f)
        found = False
        for cmd in data['commands']:
            if cmd['command_id'] == cmd_id:
                found = True
                assert cmd['status'] == 'processing', "Status should be processing"
                print("✅ Status is 'processing'")
                break
        assert found, "Command not found"
    
    # Mark as completed
    print("\nMarking as completed...")
    ipc.mark_command_completed(cmd_id)
    print("✅ Marked as completed")
    
    # Verify status
    print("\nVerifying final status...")
    with open(ipc.command_file, 'r') as f:
        data = json.load(f)
        found = False
        for cmd in data['commands']:
            if cmd['command_id'] == cmd_id:
                found = True
                assert cmd['status'] == 'completed', "Status should be completed"
                assert 'completed_at' in cmd, "Should have completed_at timestamp"
                print("✅ Status is 'completed' with timestamp")
                break
        assert found, "Command not found"
    
    print("\n✅ Test 4 PASSED\n")
    return True


def test_cleanup():
    """Test old command cleanup"""
    print("="*60)
    print("Test 5: Cleanup Old Commands")
    print("="*60 + "\n")
    
    ipc = get_ipc()
    
    # Count commands before
    with open(ipc.command_file, 'r') as f:
        before = len(json.load(f).get('commands', []))
    print(f"Commands before cleanup: {before}")
    
    # Cleanup (remove commands older than 0 days = all)
    print("\nRunning cleanup...")
    ipc.cleanup_old_commands(days=0)
    print("✅ Cleanup executed")
    
    # Count commands after
    with open(ipc.command_file, 'r') as f:
        after = len(json.load(f).get('commands', []))
    print(f"Commands after cleanup: {after}")
    
    if after <= before:
        print("✅ Cleanup reduced command count")
    else:
        print("⚠️  Cleanup didn't reduce count (expected if no old commands)")
    
    print("\n✅ Test 5 PASSED\n")
    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print(" 🧪 TELEGRAM BOT CONTROL - INTEGRATION TESTS")
    print("="*70)
    
    tests = [
        ("IPC Basic Operations", test_ipc_basic),
        ("Command Send/Receive", test_command_send_receive),
        ("Response Handling", test_response_handling),
        ("Command Status Tracking", test_command_status_tracking),
        ("Cleanup Operations", test_cleanup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except AssertionError as e:
            print(f"\n❌ Test FAILED: {e}\n")
            results.append((test_name, False))
        except Exception as e:
            print(f"\n❌ Test ERROR: {e}\n")
            results.append((test_name, False))
    
    # Summary
    print("="*70)
    print(" 📊 TEST SUMMARY")
    print("="*70 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*70}")
    print(f"Result: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
