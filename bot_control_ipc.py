"""
IPC (Inter-Process Communication) Module for Telegram-GUI Communication
Allows Telegram bot to control bot start/stop and receive status updates
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import threading
import time

class BotControlIPC:
    """Inter-process communication for bot control between Telegram and GUI"""
    
    def __init__(self, ipc_dir: str = ".ipc"):
        """Initialize IPC communication
        
        Args:
            ipc_dir: Directory for IPC files
        """
        self.ipc_dir = Path(ipc_dir)
        self.ipc_dir.mkdir(exist_ok=True)
        
        # Status file paths
        self.status_file = self.ipc_dir / "bot_status.json"
        self.command_file = self.ipc_dir / "bot_commands.json"
        self.response_file = self.ipc_dir / "bot_responses.json"
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        # Initialize files
        self._init_files()
    
    def _init_files(self):
        """Initialize IPC files"""
        try:
            if not self.status_file.exists():
                self.write_status({
                    'bots': {},
                    'updated_at': datetime.now().isoformat()
                })
            
            if not self.command_file.exists():
                with open(self.command_file, 'w') as f:
                    json.dump({'commands': [], 'updated_at': datetime.now().isoformat()}, f)
            
            if not self.response_file.exists():
                with open(self.response_file, 'w') as f:
                    json.dump({'responses': []}, f)
        except Exception as e:
            print(f"IPC initialization error: {e}")
    
    def write_status(self, status_data: Dict):
        """Write bot status to IPC file
        
        Args:
            status_data: Bot status dictionary
        """
        with self.lock:
            try:
                status_data['updated_at'] = datetime.now().isoformat()
                with open(self.status_file, 'w') as f:
                    json.dump(status_data, f, indent=4)
            except Exception as e:
                print(f"Error writing status: {e}")
    
    def read_status(self) -> Dict:
        """Read bot status from IPC file
        
        Returns:
            Bot status dictionary
        """
        with self.lock:
            try:
                if self.status_file.exists():
                    with open(self.status_file, 'r') as f:
                        return json.load(f)
            except Exception as e:
                print(f"Error reading status: {e}")
        return {'bots': {}, 'updated_at': datetime.now().isoformat()}
    
    def update_bot_status(self, bot_id: str, status: Dict):
        """Update status for a specific bot
        
        Args:
            bot_id: Bot identifier
            status: Status dictionary with keys: is_running, status_text, etc.
        """
        with self.lock:
            try:
                current = self.read_status()
                if 'bots' not in current:
                    current['bots'] = {}
                
                current['bots'][bot_id] = {
                    **status,
                    'updated_at': datetime.now().isoformat()
                }
                self.write_status(current)
            except Exception as e:
                print(f"Error updating bot status: {e}")
    
    def get_bot_status(self, bot_id: str) -> Optional[Dict]:
        """Get status for a specific bot
        
        Args:
            bot_id: Bot identifier
            
        Returns:
            Bot status dictionary or None
        """
        with self.lock:
            try:
                status = self.read_status()
                return status.get('bots', {}).get(bot_id)
            except Exception as e:
                print(f"Error getting bot status: {e}")
        return None
    
    def get_all_bots(self) -> Dict:
        """Get status for all bots
        
        Returns:
            Dictionary of all bots and their status
        """
        with self.lock:
            try:
                status = self.read_status()
                return status.get('bots', {})
            except Exception as e:
                print(f"Error getting all bots: {e}")
        return {}
    
    def send_command(self, command: str, bot_id: str, user_id: int, username: str = "Unknown") -> str:
        """Send command to GUI (start/stop bot)
        
        Args:
            command: 'start' or 'stop'
            bot_id: Bot identifier to control
            user_id: Telegram user ID
            username: Telegram username
            
        Returns:
            Command ID for tracking
        """
        with self.lock:
            try:
                import uuid
                command_id = str(uuid.uuid4())
                
                cmd_data = {
                    'command_id': command_id,
                    'command': command,
                    'bot_id': bot_id,
                    'user_id': user_id,
                    'username': username,
                    'timestamp': datetime.now().isoformat(),
                    'status': 'pending'
                }
                
                try:
                    with open(self.command_file, 'r') as f:
                        commands = json.load(f)
                except:
                    commands = {'commands': []}
                
                commands['commands'].append(cmd_data)
                commands['updated_at'] = datetime.now().isoformat()
                
                with open(self.command_file, 'w') as f:
                    json.dump(commands, f, indent=4)
                
                return command_id
            except Exception as e:
                print(f"Error sending command: {e}")
                return None
    
    def get_pending_commands(self) -> List[Dict]:
        """Get pending commands from Telegram
        
        Returns:
            List of pending commands
        """
        with self.lock:
            try:
                if not self.command_file.exists():
                    return []
                
                with open(self.command_file, 'r') as f:
                    data = json.load(f)
                
                # Filter pending commands (from last 5 seconds)
                now = datetime.now()
                pending = []
                
                for cmd in data.get('commands', []):
                    if cmd.get('status') == 'pending':
                        cmd_time = datetime.fromisoformat(cmd.get('timestamp', now.isoformat()))
                        if (now - cmd_time).total_seconds() < 5:  # Only recent pending
                            pending.append(cmd)
                
                return pending
            except Exception as e:
                print(f"Error getting pending commands: {e}")
        return []
    
    def mark_command_processing(self, command_id: str):
        """Mark command as being processed
        
        Args:
            command_id: Command ID to mark
        """
        self._update_command_status(command_id, 'processing')
    
    def mark_command_completed(self, command_id: str):
        """Mark command as completed
        
        Args:
            command_id: Command ID to mark
        """
        self._update_command_status(command_id, 'completed')
    
    def mark_command_failed(self, command_id: str, error: str = ""):
        """Mark command as failed
        
        Args:
            command_id: Command ID to mark
            error: Error message
        """
        self._update_command_status(command_id, 'failed', error)
    
    def _update_command_status(self, command_id: str, status: str, error: str = ""):
        """Update command status
        
        Args:
            command_id: Command ID
            status: New status
            error: Error message if any
        """
        with self.lock:
            try:
                with open(self.command_file, 'r') as f:
                    data = json.load(f)
                
                for cmd in data.get('commands', []):
                    if cmd.get('command_id') == command_id:
                        cmd['status'] = status
                        cmd['completed_at'] = datetime.now().isoformat()
                        if error:
                            cmd['error'] = error
                        break
                
                data['updated_at'] = datetime.now().isoformat()
                with open(self.command_file, 'w') as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error updating command status: {e}")
    
    def send_response(self, command_id: str, success: bool, message: str):
        """Send response to Telegram
        
        Args:
            command_id: Command ID being responded to
            success: Whether command was successful
            message: Response message
        """
        with self.lock:
            try:
                response_data = {
                    'command_id': command_id,
                    'success': success,
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }
                
                try:
                    with open(self.response_file, 'r') as f:
                        responses = json.load(f)
                except:
                    responses = {'responses': []}
                
                responses['responses'].append(response_data)
                # Keep only last 50 responses
                responses['responses'] = responses['responses'][-50:]
                
                with open(self.response_file, 'w') as f:
                    json.dump(responses, f, indent=4)
            except Exception as e:
                print(f"Error sending response: {e}")
    
    def get_latest_response(self, command_id: str, timeout: float = 5.0) -> Optional[Dict]:
        """Get response for a command (with polling)
        
        Args:
            command_id: Command ID to wait for
            timeout: Timeout in seconds
            
        Returns:
            Response dictionary or None if timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            with self.lock:
                try:
                    if not self.response_file.exists():
                        time.sleep(0.1)
                        continue
                    
                    with open(self.response_file, 'r') as f:
                        data = json.load(f)
                    
                    for resp in reversed(data.get('responses', [])):
                        if resp.get('command_id') == command_id:
                            return resp
                except Exception as e:
                    print(f"Error getting response: {e}")
            
            time.sleep(0.1)
        
        return None
    
    def cleanup_old_commands(self, days: int = 1):
        """Clean up old command files
        
        Args:
            days: Delete commands older than this many days
        """
        with self.lock:
            try:
                cutoff_time = datetime.now().timestamp() - (days * 86400)
                
                # Clean up command file
                if self.command_file.exists():
                    with open(self.command_file, 'r') as f:
                        data = json.load(f)
                    
                    recent = []
                    for cmd in data.get('commands', []):
                        try:
                            cmd_time = datetime.fromisoformat(cmd.get('timestamp')).timestamp()
                            if cmd_time > cutoff_time:
                                recent.append(cmd)
                        except:
                            recent.append(cmd)
                    
                    data['commands'] = recent
                    with open(self.command_file, 'w') as f:
                        json.dump(data, f, indent=4)
                
                # Clean up response file
                if self.response_file.exists():
                    with open(self.response_file, 'r') as f:
                        data = json.load(f)
                    
                    recent = []
                    for resp in data.get('responses', []):
                        try:
                            resp_time = datetime.fromisoformat(resp.get('timestamp')).timestamp()
                            if resp_time > cutoff_time:
                                recent.append(resp)
                        except:
                            recent.append(resp)
                    
                    data['responses'] = recent
                    with open(self.response_file, 'w') as f:
                        json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error cleaning up commands: {e}")


# Global IPC instance
_ipc_instance = None

def get_ipc() -> BotControlIPC:
    """Get global IPC instance"""
    global _ipc_instance
    if _ipc_instance is None:
        _ipc_instance = BotControlIPC()
    return _ipc_instance
