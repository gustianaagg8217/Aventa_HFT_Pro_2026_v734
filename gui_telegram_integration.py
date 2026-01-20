"""
GUI-IPC Integration Module
Handles communication between GUI Launcher and Telegram Bot via IPC
"""

import threading
import time
from typing import Callable, Optional, Dict
import logging
from bot_control_ipc import get_ipc

logger = logging.getLogger(__name__)


class GUITelegramIntegration:
    """Manages telegram bot control commands received in GUI"""
    
    def __init__(self, gui_instance=None):
        """Initialize GUI-Telegram integration
        
        Args:
            gui_instance: Reference to HFTProGUI instance
        """
        self.gui = gui_instance
        self.ipc = get_ipc()
        self.running = False
        self.command_thread = None
        self.update_interval = 0.5  # Check for commands every 500ms
    
    def start_command_listener(self):
        """Start listening for Telegram commands"""
        if self.running:
            return
        
        self.running = True
        self.command_thread = threading.Thread(target=self._command_loop, daemon=True)
        self.command_thread.start()
        logger.info("GUI Telegram Integration: Command listener started")
    
    def stop_command_listener(self):
        """Stop listening for Telegram commands"""
        self.running = False
        if self.command_thread:
            self.command_thread.join(timeout=2.0)
        logger.info("GUI Telegram Integration: Command listener stopped")
    
    def _command_loop(self):
        """Main command processing loop"""
        while self.running:
            try:
                # Get pending commands from Telegram
                commands = self.ipc.get_pending_commands()
                
                for cmd in commands:
                    try:
                        self._process_command(cmd)
                    except Exception as e:
                        logger.error(f"Error processing command {cmd.get('command_id')}: {e}")
                        self.ipc.mark_command_failed(
                            cmd.get('command_id'),
                            str(e)
                        )
                
                time.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Command loop error: {e}")
                time.sleep(1.0)
    
    def _process_command(self, cmd: Dict):
        """Process a single Telegram command
        
        Args:
            cmd: Command dictionary with keys:
                - command_id: Unique command ID
                - command: 'start' or 'stop'
                - bot_id: Bot to control
                - user_id: Telegram user ID
                - username: Telegram username
        """
        command_id = cmd.get('command_id')
        command = cmd.get('command')
        bot_id = cmd.get('bot_id')
        user_id = cmd.get('user_id')
        username = cmd.get('username', 'Unknown')
        
        logger.info(f"Processing command: {command} for bot {bot_id} by user {username}")
        
        # Mark as processing
        self.ipc.mark_command_processing(command_id)
        
        try:
            if not self.gui:
                raise RuntimeError("GUI instance not available")
            
            if command == 'start':
                success, message = self._handle_start_bot(bot_id, user_id, username)
            elif command == 'stop':
                success, message = self._handle_stop_bot(bot_id, user_id, username)
            else:
                success = False
                message = f"Unknown command: {command}"
            
            # Send response back to Telegram
            self.ipc.send_response(command_id, success, message)
            
            if success:
                self.ipc.mark_command_completed(command_id)
                logger.info(f"Command {command_id} completed successfully")
            else:
                self.ipc.mark_command_failed(command_id, message)
                logger.warning(f"Command {command_id} failed: {message}")
        
        except Exception as e:
            error_msg = f"Exception: {str(e)}"
            self.ipc.send_response(command_id, False, error_msg)
            self.ipc.mark_command_failed(command_id, error_msg)
            logger.error(f"Command {command_id} exception: {e}")
    
    def _handle_start_bot(self, bot_id: str, user_id: int, username: str) -> tuple:
        """Handle start bot command
        
        Returns:
            (success: bool, message: str)
        """
        try:
            # Check if bot exists
            if bot_id not in self.gui.bots:
                return False, f"Bot {bot_id} not found"
            
            bot = self.gui.bots[bot_id]
            
            # Check if already running
            if bot.get('is_running', False):
                return False, f"Bot {bot_id} is already running"
            
            # Set active bot
            self.gui.active_bot_id = bot_id
            
            # Call GUI start_trading method
            # This needs to be thread-safe, so we schedule it on the GUI thread
            if hasattr(self.gui, 'root'):
                self.gui.root.after(0, lambda: self.gui.start_trading())
                
                # Wait a bit for GUI to process
                time.sleep(0.5)
                
                # Check if started successfully
                if bot.get('is_running', False):
                    # Update bot status in IPC
                    self._update_bot_status_in_ipc(bot_id)
                    return True, f"Bot {bot_id} started successfully"
                else:
                    return False, f"Failed to start bot {bot_id}"
            else:
                return False, "GUI instance not properly initialized"
        
        except Exception as e:
            logger.error(f"Error handling start bot: {e}")
            return False, f"Error: {str(e)}"
    
    def _handle_stop_bot(self, bot_id: str, user_id: int, username: str) -> tuple:
        """Handle stop bot command
        
        Returns:
            (success: bool, message: str)
        """
        try:
            # Check if bot exists
            if bot_id not in self.gui.bots:
                return False, f"Bot {bot_id} not found"
            
            bot = self.gui.bots[bot_id]
            
            # Check if already stopped
            if not bot.get('is_running', False):
                return False, f"Bot {bot_id} is already stopped"
            
            # Set active bot
            self.gui.active_bot_id = bot_id
            
            # Call GUI stop_trading method
            # This needs to be thread-safe, so we schedule it on the GUI thread
            if hasattr(self.gui, 'root'):
                self.gui.root.after(0, lambda: self.gui.stop_trading())
                
                # Wait a bit for GUI to process
                time.sleep(0.5)
                
                # Check if stopped successfully
                if not bot.get('is_running', False):
                    # Update bot status in IPC
                    self._update_bot_status_in_ipc(bot_id)
                    return True, f"Bot {bot_id} stopped successfully"
                else:
                    return False, f"Failed to stop bot {bot_id}"
            else:
                return False, "GUI instance not properly initialized"
        
        except Exception as e:
            logger.error(f"Error handling stop bot: {e}")
            return False, f"Error: {str(e)}"
    
    def update_bot_status(self, bot_id: str, is_running: bool, additional_info: Dict = None):
        """Update bot status in IPC (called by GUI)
        
        Args:
            bot_id: Bot identifier
            is_running: Whether bot is running
            additional_info: Additional status info (symbol, magic number, etc.)
        """
        try:
            status = {
                'is_running': is_running,
                'status_text': 'TRADING ACTIVE' if is_running else 'STOPPED'
            }
            
            if additional_info:
                status.update(additional_info)
            
            self.ipc.update_bot_status(bot_id, status)
        except Exception as e:
            logger.error(f"Error updating bot status: {e}")
    
    def _update_bot_status_in_ipc(self, bot_id: str):
        """Update bot status in IPC from GUI data"""
        try:
            if bot_id not in self.gui.bots:
                return
            
            bot = self.gui.bots[bot_id]
            config = bot.get('config', {})
            
            status = {
                'is_running': bot.get('is_running', False),
                'status_text': 'TRADING ACTIVE' if bot.get('is_running') else 'STOPPED',
                'symbol': config.get('symbol', 'N/A'),
                'magic_number': config.get('magic_number', 'N/A'),
                'volume': config.get('default_volume', 'N/A')
            }
            
            self.ipc.update_bot_status(bot_id, status)
        except Exception as e:
            logger.error(f"Error updating bot status in IPC: {e}")
    
    def update_all_bots_status(self):
        """Update status for all bots in IPC (called by GUI periodically)"""
        try:
            for bot_id in self.gui.bots.keys():
                self._update_bot_status_in_ipc(bot_id)
        except Exception as e:
            logger.error(f"Error updating all bots status: {e}")


# Global integration instance
_integration_instance = None


def get_gui_telegram_integration(gui_instance=None) -> GUITelegramIntegration:
    """Get or create global integration instance"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = GUITelegramIntegration(gui_instance)
    elif gui_instance is not None and _integration_instance.gui is None:
        _integration_instance.gui = gui_instance
    
    return _integration_instance
