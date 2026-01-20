"""
Telegram Bot Runner
Runs Telegram bots in background asyncio loop
"""

import asyncio
import threading
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TelegramBotRunner:
    """Manages running multiple telegram bots asynchronously"""
    
    def __init__(self):
        self.bots: Dict[str, dict] = {}  # bot_id -> {'bot': TelegramBot, 'task': Task}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.running = False
    
    def start(self):
        """Start the async event loop in a background thread"""
        if self.running:
            logger.warning("Bot runner already started")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info("Telegram Bot Runner: Event loop started in background thread")
    
    def stop(self):
        """Stop all bots and the event loop"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop all bots
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._stop_all_bots(), self.loop)
        
        # Wait for thread
        if self.thread:
            self.thread.join(timeout=5.0)
        
        logger.info("Telegram Bot Runner: Stopped")
    
    def add_bot(self, bot_id: str, telegram_bot):
        """Add and start a telegram bot
        
        Args:
            bot_id: Unique identifier for this bot
            telegram_bot: TelegramBot instance
        """
        if not self.running:
            logger.warning("Bot runner not started, starting now...")
            self.start()
        
        if bot_id in self.bots:
            logger.warning(f"Bot {bot_id} already registered, stopping old instance...")
            self.remove_bot(bot_id)
        
        # Schedule bot start in event loop
        future = asyncio.run_coroutine_threadsafe(
            self._start_bot(bot_id, telegram_bot),
            self.loop
        )
        
        try:
            future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to start bot {bot_id}: {e}")
            return False
        
        logger.info(f"Bot {bot_id} added and started")
        return True
    
    def remove_bot(self, bot_id: str):
        """Remove and stop a telegram bot"""
        if bot_id not in self.bots:
            return
        
        # Schedule bot stop in event loop
        future = asyncio.run_coroutine_threadsafe(
            self._stop_bot(bot_id),
            self.loop
        )
        
        try:
            future.result(timeout=5.0)
        except Exception as e:
            logger.error(f"Failed to stop bot {bot_id}: {e}")
        
        logger.info(f"Bot {bot_id} removed")
    
    async def _start_bot(self, bot_id: str, telegram_bot):
        """Start a bot polling (async)"""
        try:
            self.bots[bot_id] = {
                'bot': telegram_bot,
                'task': None
            }
            
            # Start bot with polling
            logger.info(f"Starting polling for bot {bot_id}")
            await telegram_bot.app.initialize()
            await telegram_bot.app.start()
            logger.info(f"Bot {bot_id} initialized and started, listening for updates...")
            
            # Start polling
            await telegram_bot.app.updater.start_polling(
                allowed_updates=['message', 'callback_query'],
                drop_pending_updates=True
            )
            logger.info(f"Bot {bot_id} polling started successfully")
        
        except Exception as e:
            logger.error(f"Error in bot polling for {bot_id}: {e}")
            import traceback
            traceback.print_exc()
            if bot_id in self.bots:
                del self.bots[bot_id]
    
    async def _stop_bot(self, bot_id: str):
        """Stop a bot polling (async)"""
        if bot_id not in self.bots:
            return
        
        bot_info = self.bots[bot_id]
        telegram_bot = bot_info['bot']
        
        try:
            logger.info(f"Stopping bot {bot_id}")
            await telegram_bot.app.stop()
            del self.bots[bot_id]
        except Exception as e:
            logger.error(f"Error stopping bot {bot_id}: {e}")
    
    async def _stop_all_bots(self):
        """Stop all bots"""
        bot_ids = list(self.bots.keys())
        for bot_id in bot_ids:
            await self._stop_bot(bot_id)
    
    def _run_loop(self):
        """Run event loop in background thread"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Event loop error: {e}")
        finally:
            self.loop.close()
            logger.info("Event loop closed")


# Global singleton
_runner: Optional[TelegramBotRunner] = None


def get_bot_runner() -> TelegramBotRunner:
    """Get or create the global bot runner instance"""
    global _runner
    if _runner is None:
        _runner = TelegramBotRunner()
    return _runner
