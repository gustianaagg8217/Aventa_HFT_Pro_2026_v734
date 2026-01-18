"""
Aventa HFT Pro 2026 - Telegram Monitoring Bot
Real-time trading alerts and remote control
"""

import asyncio
import MetaTrader5 as mt5
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import json
import logging
from datetime import datetime
from typing import Dict
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aventa_hft_core import UltraLowLatencyEngine
from risk_manager import RiskManager

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram bot for HFT monitoring and control"""
    
    def __init__(self, token: str, allowed_users: list):
        self.token = token
        self.allowed_users = allowed_users
        
        # Trading components
        self.engine = None
        self.risk_manager = None
        self.is_trading = False
        
        # Statistics
        self.start_time = datetime.now()
        
        # Create application
        self.app = Application.builder().token(token).build()
        
        # Register handlers
        self.register_handlers()
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in self.allowed_users
    
    def register_handlers(self):
        """Register command handlers"""
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("status", self.cmd_status))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        self.app.add_handler(CommandHandler("performance", self.cmd_performance))
        self.app.add_handler(CommandHandler("risk", self.cmd_risk))
        self.app.add_handler(CommandHandler("positions", self.cmd_positions))
        self.app.add_handler(CommandHandler("start_trading", self.cmd_start_trading))
        self.app.add_handler(CommandHandler("stop_trading", self.cmd_stop_trading))
        self.app.add_handler(CommandHandler("close_all", self.cmd_close_all))
        self.app.add_handler(CommandHandler("config", self.cmd_config))
        self.app.add_handler(CommandHandler("edit", self.cmd_edit_config))
        self.app.add_handler(CommandHandler("set_symbol", self.cmd_set_symbol))
        self.app.add_handler(CommandHandler("set_volume", self.cmd_set_volume))
        self.app.add_handler(CommandHandler("set_magic", self.cmd_set_magic))
        self.app.add_handler(CommandHandler("set_risk", self.cmd_set_risk))
        self.app.add_handler(CommandHandler("set_signal", self.cmd_set_signal))
        self.app.add_handler(CommandHandler("set_spread", self.cmd_set_spread))
        self.app.add_handler(CommandHandler("set_volatility", self.cmd_set_volatility))
        self.app.add_handler(CommandHandler("set_filling", self.cmd_set_filling))
        self.app.add_handler(CommandHandler("set_sl_mult", self.cmd_set_sl_multiplier))
        self.app.add_handler(CommandHandler("set_rr", self.cmd_set_risk_reward))
        self.app.add_handler(CommandHandler("set_tp_mode", self.cmd_set_tp_mode))
        self.app.add_handler(CommandHandler("set_tp_dollar", self.cmd_set_tp_dollar))
        self.app.add_handler(CommandHandler("set_max_loss", self.cmd_set_max_loss))
        self.app.add_handler(CommandHandler("set_profit_target", self.cmd_set_profit_target))
        self.app.add_handler(CommandHandler("set_ml", self.cmd_set_ml))
        self.app.add_handler(CommandHandler("load_preset", self.cmd_load_preset))
        self.app.add_handler(CommandHandler("save_config", self.cmd_save_config))
        self.app.add_handler(CommandHandler("help", self.cmd_help))
        
        # Callback handlers
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command"""
        user_id = update.effective_user.id
        
        if not self.is_authorized(user_id):
            await update.message.reply_text("❌ Unauthorized access")
            logger.warning(f"Unauthorized access attempt from user {user_id}")
            return
        
        welcome_message = """
🚀 *Aventa HFT Pro 2026*
━━━━━━━━━━━━━━━━━━━━

Welcome to the Ultra Low Latency Trading System!

*Quick Commands:*
/status - System status & account
/config - View configuration
/edit - Edit configuration
/positions - Current positions

*Control:*
/start\_trading - Start trading engine
/stop\_trading - Stop trading engine
/close\_all - Close all positions

*Settings:*
/set\_volume <val> - Adjust volume
/set\_signal <val> - Adjust signal strength
/load\_preset <name> - Load GOLD/EURUSD

/help - Full command list

Use the buttons below for quick actions 👇
        """
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("📈 Stats", callback_data="stats"),
            ],
            [
                InlineKeyboardButton("▶️ Start Trading", callback_data="start_trading"),
                InlineKeyboardButton("⏹️ Stop Trading", callback_data="stop_trading"),
            ],
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get system status"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        status_msg = "🤖 *System Status*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        # Trading status
        if self.is_trading:
            status_msg += "✅ Trading: *ACTIVE*\n"
        else:
            status_msg += "⏸️ Trading: *STOPPED*\n"
        
        # MT5 connection
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                status_msg += f"✅ MT5: *Connected*\n"
                status_msg += f"💰 Balance: *${account_info.balance:.2f}*\n"
                status_msg += f"📊 Equity: *${account_info.equity:.2f}*\n"
                status_msg += f"💵 Profit: *${account_info.profit:.2f}*\n"
            mt5.shutdown()
        else:
            status_msg += "❌ MT5: *Disconnected*\n"
        
        # Uptime
        uptime = datetime.now() - self.start_time
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        status_msg += f"\n⏱️ Uptime: *{hours}h {minutes}m*\n"
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get trading statistics (live from MT5 history)"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return

        if not mt5.initialize():
            await update.message.reply_text("❌ Failed to connect to MT5")
            return

        from datetime import datetime, time as dtime

        now = datetime.now()
        day_start = datetime.combine(now.date(), dtime.min)
        deals = mt5.history_deals_get(day_start, now)
        mt5.shutdown()

        total_trades = 0
        wins = 0
        losses = 0
        total_profit = 0.0
        total_loss = 0.0
        net_profit = 0.0
        profit_factor = 0.0
        daily_pnl = 0.0

        if deals:
            for d in deals:
                if d.entry == mt5.DEAL_ENTRY_IN:
                    total_trades += 1
                if d.profit > 0:
                    wins += 1
                    total_profit += d.profit
                elif d.profit < 0:
                    losses += 1
                    total_loss += abs(d.profit)
                daily_pnl += d.profit
            net_profit = total_profit - total_loss
            profit_factor = (total_profit / total_loss) if total_loss > 0 else 0.0
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0.0

        stats_msg = "📊 *Trading Statistics (Today)*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        stats_msg += f"📈 Total Trades: *{total_trades}*\n"
        stats_msg += f"✅ Wins: *{wins}*\n"
        stats_msg += f"❌ Losses: *{losses}*\n"
        stats_msg += f"🎯 Win Rate: *{win_rate:.1f}%*\n"
        stats_msg += f"\n"
        stats_msg += f"💰 Total Profit: *${total_profit:.2f}*\n"
        stats_msg += f"💸 Total Loss: *${total_loss:.2f}*\n"
        stats_msg += f"💵 Net Profit: *${net_profit:.2f}*\n"
        stats_msg += f"📊 Profit Factor: *{profit_factor:.2f}*\n"
        stats_msg += f"\n"
        stats_msg += f"📅 Today's PnL: *${daily_pnl:.2f}*\n"

        await update.message.reply_text(stats_msg, parse_mode='Markdown')
    
    async def cmd_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get performance metrics"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if not self.engine:
            await update.message.reply_text("⚠️ Engine not running")
            return
        
        stats = self.engine.get_performance_stats()
        
        perf_msg = "⚡ *Performance Metrics*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        perf_msg += f"🚀 Tick Latency (avg): *{stats['tick_latency_avg_us']:.1f} μs*\n"
        perf_msg += f"📊 Tick Latency (max): *{stats['tick_latency_max_us']:.1f} μs*\n"
        perf_msg += f"📊 Tick Latency (min): *{stats['tick_latency_min_us']:.1f} μs*\n"
        perf_msg += f"\n"
        perf_msg += f"⚡ Execution Time (avg): *{stats['execution_time_avg_ms']:.2f} ms*\n"
        perf_msg += f"📊 Execution Time (max): *{stats['execution_time_max_ms']:.2f} ms*\n"
        perf_msg += f"\n"
        perf_msg += f"📈 Ticks Processed: *{stats['ticks_processed']:,}*\n"
        perf_msg += f"📊 Orderflow Samples: *{stats['orderflow_samples']:,}*\n"
        perf_msg += f"\n"
        perf_msg += f"📍 Current Position: *{stats['current_position'] or 'None'}*\n"
        
        if stats['current_position']:
            perf_msg += f"📊 Position Volume: *{stats['position_volume']}*\n"
        
        await update.message.reply_text(perf_msg, parse_mode='Markdown')
    
    async def cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get risk management status"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return

        snapshot = self.get_runtime_risk_snapshot()
        if not snapshot:
            await update.message.reply_text("❌ Failed to fetch MT5 risk data")
            return

        risk_msg = "🛡️ *Risk Management (Live)*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        risk_msg += f"💰 Balance: *${snapshot['balance']:.2f}*\n"
        risk_msg += f"📊 Equity: *${snapshot['equity']:.2f}*\n"
        risk_msg += f"📉 Floating P/L: *${snapshot['floating']:.2f}*\n"
        risk_msg += f"📦 Open Positions: *{snapshot['positions']}*\n"

        await update.message.reply_text(risk_msg, parse_mode="Markdown")

    def get_runtime_risk_snapshot(self):
        if not mt5.initialize():
            return None

        info = mt5.account_info()
        positions = mt5.positions_get()

        equity = info.equity if info else 0.0
        balance = info.balance if info else 0.0
        floating = sum(p.profit for p in positions) if positions else 0.0
        pos_count = len(positions) if positions else 0

        mt5.shutdown()

        return {
            "balance": balance,
            "equity": equity,
            "floating": floating,
            "positions": pos_count
        }

    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get current positions"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if not mt5.initialize():
            await update.message.reply_text("❌ Failed to connect to MT5")
            return
        
        positions = mt5.positions_get()
        
        if positions is None or len(positions) == 0:
            await update.message.reply_text("📭 No open positions")
            mt5.shutdown()
            return
        
        msg = f"📊 *Open Positions* ({len(positions)})\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for pos in positions:
            pos_type = "🟢 BUY" if pos.type == mt5.ORDER_TYPE_BUY else "🔴 SELL"
            msg += f"{pos_type} *{pos.symbol}*\n"
            msg += f"Volume: {pos.volume}\n"
            msg += f"Price: {pos.price_open:.5f}\n"
            msg += f"Current: {pos.price_current:.5f}\n"
            msg += f"Profit: *${pos.profit:.2f}*\n"
            msg += f"SL: {pos.sl:.5f} | TP: {pos.tp:.5f}\n"
            msg += f"\n"
        
        mt5.shutdown()
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_start_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start trading engine"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if self.is_trading:
            await update.message.reply_text("⚠️ Trading is already active")
            return
        
        await update.message.reply_text("🚀 Starting trading engine...")
        
        # Load configuration
        try:
            with open('hft_pro_config.json', 'r') as f:
                config = json.load(f)
        except:
            config = {
                'magic_number': 2026001,
                'default_volume': 0.01,
                'min_signal_strength': 0.6,
            }
        
        # Initialize components
        symbol = config.get('symbol', 'EURUSD')
        
        self.risk_manager = RiskManager(config.get('limits', {}))
        
        # Create ML predictor if enabled
        ml_predictor = None
        if config.get('use_ml', False):
            from ml_predictor import MLPredictor
            ml_predictor = MLPredictor(symbol, config)
        
        self.engine = UltraLowLatencyEngine(symbol, config, self.risk_manager, ml_predictor)
        
        if self.engine.start():
            self.is_trading = True
            await update.message.reply_text(
                f"✅ *Trading Started!*\n\n"
                f"Symbol: {symbol}\n"
                f"Volume: {config.get('default_volume', 0.01)}\n"
                f"Status: Active 🟢",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text("❌ Failed to start trading engine")
    
    async def cmd_stop_trading(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stop trading engine"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if not self.is_trading:
            await update.message.reply_text("⚠️ Trading is not active")
            return
        
        await update.message.reply_text("⏹️ Stopping trading engine...")
        
        if self.engine:
            self.engine.stop()
        
        self.is_trading = False
        
        await update.message.reply_text("✅ Trading stopped")
    
    async def cmd_close_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Close all positions"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if not mt5.initialize():
            await update.message.reply_text("❌ Failed to connect to MT5")
            return
        
        positions = mt5.positions_get()
        
        if positions is None or len(positions) == 0:
            await update.message.reply_text("📭 No positions to close")
            mt5.shutdown()
            return
        
        closed = 0
        for pos in positions:
            close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(pos.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": price,
                "deviation": 20,
                "magic": pos.magic,
                "comment": "Closed via Telegram",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed += 1
        
        mt5.shutdown()
        
        await update.message.reply_text(f"✅ Closed {closed}/{len(positions)} positions")
    
    async def cmd_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current configuration"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        # Load current config
        try:
            with open('hft_config_insta_golg_ls.json', 'r') as f:
                config = json.load(f)
        except:
            await update.message.reply_text("⚠️ No configuration file found")
            return
        
        config_msg = "⚙️ *Current Configuration*\n━━━━━━━━━━━━━━━━━━━━\n\n"
        
        config_msg += f"📊 Symbol: *{config.get('symbol', 'N/A')}*\n"
        config_msg += f"💰 Default Volume: *{config.get('default_volume', 'N/A')}*\n"
        config_msg += f"🔢 Magic Number: *{config.get('magic_number', 'N/A')}*\n"
        config_msg += f"📈 Risk per Trade: *{config.get('risk_per_trade', 'N/A')}%*\n"
        config_msg += f"⚡ Min Signal Strength: *{config.get('min_signal_strength', 'N/A')}*\n"
        config_msg += f"📊 Max Spread: *{config.get('max_spread', 'N/A')}*\n"
        config_msg += f"📉 Max Volatility: *{config.get('max_volatility', 'N/A')}*\n"
        config_msg += f"🎯 SL Multiplier: *{config.get('sl_multiplier', 'N/A')}*\n"
        config_msg += f"🎯 Risk:Reward: *{config.get('risk_reward_ratio', 'N/A')}*\n"
        config_msg += f"💵 TP Mode: *{config.get('tp_mode', 'N/A')}*\n"
        config_msg += f"💰 TP Dollar: *${config.get('tp_dollar_amount', 'N/A')}*\n"
        config_msg += f"🔴 Max Floating Loss: *${config.get('max_floating_loss', 'N/A')}*\n"
        config_msg += f"🟢 Take Profit Target: *${config.get('max_floating_profit', 'N/A')}*\n"
        config_msg += f"🤖 Use ML: *{config.get('use_ml', False)}*\n"
        config_msg += f"\nUse /edit to open interactive edit menu"
        
        await update.message.reply_text(config_msg, parse_mode='Markdown')
    
    async def cmd_edit_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show interactive configuration editor"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        edit_msg = """⚙️ *Configuration Editor*
━━━━━━━━━━━━━━━━━━━━

Select parameter to edit:

*Basic Settings:*
/set\_symbol <value> - Trading symbol
/set\_volume <value> - Default volume
/set\_magic <value> - Magic number
/set\_risk <value> - Risk per trade %

*Signal Settings:*
/set\_signal <value> - Min signal strength (0.3-0.8)
/set\_spread <value> - Max spread
/set\_volatility <value> - Max volatility

*Risk Management:*
/set\_sl\_mult <value> - SL multiplier (ATR)
/set\_rr <value> - Risk:Reward ratio
/set\_tp\_mode <mode> - TP mode (RiskReward/FixedDollar)
/set\_tp\_dollar <value> - TP dollar amount
/set\_max\_loss <value> - Max floating loss $
/set\_profit\_target <value> - Take profit target $

*Advanced:*
/set\_filling <mode> - Filling mode (FOK/IOC/RETURN)
/set\_ml <on/off> - Enable/disable ML

Use buttons below for quick access 👇"""
        
        keyboard = [
            [
                InlineKeyboardButton("📊 Symbol", callback_data="edit_symbol"),
                InlineKeyboardButton("💰 Volume", callback_data="edit_volume"),
            ],
            [
                InlineKeyboardButton("⚡ Signal", callback_data="edit_signal"),
                InlineKeyboardButton("📈 Spread", callback_data="edit_spread"),
            ],
            [
                InlineKeyboardButton("🎯 SL Mult", callback_data="edit_sl"),
                InlineKeyboardButton("🎯 R:R", callback_data="edit_rr"),
            ],
            [
                InlineKeyboardButton("💵 TP Mode", callback_data="edit_tp_mode"),
                InlineKeyboardButton("💰 TP $", callback_data="edit_tp_dollar"),
            ],
            [
                InlineKeyboardButton("🔴 Max Loss", callback_data="edit_max_loss"),
                InlineKeyboardButton("🟢 Profit Target", callback_data="edit_profit_target"),
            ],
            [
                InlineKeyboardButton("🤖 Toggle ML", callback_data="toggle_ml"),
                InlineKeyboardButton("✅ View Config", callback_data="config"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(edit_msg, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_set_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set trading symbol: /set_symbol GOLD.ls"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_symbol <symbol>\\nExample: /set\\_symbol GOLD.ls", parse_mode='Markdown')
            return
        
        try:
            symbol = context.args[0]
            
            # Update config
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['symbol'] = symbol
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Symbol updated to *{symbol}*", parse_mode='Markdown')
            logger.info(f"Symbol updated to {symbol} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_volume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set default volume: /set_volume 0.01"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_volume <volume>\\nExample: /set\\_volume 0.01", parse_mode='Markdown')
            return
        
        try:
            volume = float(context.args[0])
            if volume <= 0:
                raise ValueError("Volume must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['default_volume'] = volume
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Volume updated to *{volume}*", parse_mode='Markdown')
            logger.info(f"Volume updated to {volume} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_magic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set magic number: /set_magic 2026001"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_magic <number>\\nExample: /set\\_magic 2026001", parse_mode='Markdown')
            return
        
        try:
            magic = int(context.args[0])
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['magic_number'] = magic
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Magic number updated to *{magic}*", parse_mode='Markdown')
            logger.info(f"Magic number updated to {magic} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set risk per trade: /set_risk 1.0"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_risk <percentage>\\nExample: /set\\_risk 1.0", parse_mode='Markdown')
            return
        
        try:
            risk = float(context.args[0])
            if not 0.1 <= risk <= 10.0:
                raise ValueError("Risk must be between 0.1 and 10.0")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['risk_per_trade'] = risk
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Risk per trade updated to *{risk}%*", parse_mode='Markdown')
            logger.info(f"Risk per trade updated to {risk}% by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_signal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set min signal strength: /set_signal 0.6"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_signal <strength>\\nExample: /set\\_signal 0.6\\n(0.3-0.5 = more trades | 0.6-0.8 = fewer, safer)", parse_mode='Markdown')
            return
        
        try:
            signal = float(context.args[0])
            if not 0.1 <= signal <= 1.0:
                raise ValueError("Signal strength must be between 0.1 and 1.0")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['min_signal_strength'] = signal
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Min signal strength updated to *{signal}*", parse_mode='Markdown')
            logger.info(f"Signal strength updated to {signal} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_spread(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set max spread: /set_spread 0.05"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_spread <max\\_spread>\\nExample: /set\\_spread 0.05\\n(GOLD: 0.02-0.05 | EURUSD: 0.0002-0.001)", parse_mode='Markdown')
            return
        
        try:
            spread = float(context.args[0])
            if spread <= 0:
                raise ValueError("Spread must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['max_spread'] = spread
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Max spread updated to *{spread}*", parse_mode='Markdown')
            logger.info(f"Max spread updated to {spread} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_volatility(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set max volatility: /set_volatility 0.005"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_volatility <max\\_volatility>\\nExample: /set\\_volatility 0.005", parse_mode='Markdown')
            return
        
        try:
            volatility = float(context.args[0])
            if volatility <= 0:
                raise ValueError("Volatility must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['max_volatility'] = volatility
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Max volatility updated to *{volatility}*", parse_mode='Markdown')
            logger.info(f"Max volatility updated to {volatility} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_filling(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set filling mode: /set_filling FOK"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_filling <mode>\\nModes: FOK, IOC, RETURN\\nExample: /set\\_filling FOK", parse_mode='Markdown')
            return
        
        try:
            filling = context.args[0].upper()
            if filling not in ['FOK', 'IOC', 'RETURN']:
                raise ValueError("Filling mode must be FOK, IOC, or RETURN")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['filling_mode'] = filling
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Filling mode updated to *{filling}*", parse_mode='Markdown')
            logger.info(f"Filling mode updated to {filling} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_sl_multiplier(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set SL multiplier: /set_sl_mult 2.0"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_sl\\_mult <multiplier>\\nExample: /set\\_sl\\_mult 2.0\\n(SL = ATR × this value)", parse_mode='Markdown')
            return
        
        try:
            sl_mult = float(context.args[0])
            if sl_mult <= 0:
                raise ValueError("SL multiplier must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['sl_multiplier'] = sl_mult
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ SL multiplier updated to *{sl_mult}*", parse_mode='Markdown')
            logger.info(f"SL multiplier updated to {sl_mult} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_risk_reward(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set risk reward ratio: /set_rr 2.0"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_rr <ratio>\\nExample: /set\\_rr 2.0\\n(TP = SL × this value)", parse_mode='Markdown')
            return
        
        try:
            rr = float(context.args[0])
            if rr <= 0:
                raise ValueError("Risk:Reward ratio must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['risk_reward_ratio'] = rr
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Risk:Reward ratio updated to *{rr}*", parse_mode='Markdown')
            logger.info(f"Risk:Reward ratio updated to {rr} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_tp_mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set TP mode: /set_tp_mode RiskReward"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_tp\\_mode <mode>\\nModes: RiskReward, FixedDollar\\nExample: /set\\_tp\\_mode RiskReward", parse_mode='Markdown')
            return
        
        try:
            tp_mode = context.args[0]
            if tp_mode not in ['RiskReward', 'FixedDollar']:
                raise ValueError("TP mode must be RiskReward or FixedDollar")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['tp_mode'] = tp_mode
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ TP mode updated to *{tp_mode}*", parse_mode='Markdown')
            logger.info(f"TP mode updated to {tp_mode} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_tp_dollar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set TP dollar amount: /set_tp_dollar 0.5"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_tp\\_dollar <amount>\\nExample: /set\\_tp\\_dollar 0.5", parse_mode='Markdown')
            return
        
        try:
            tp_dollar = float(context.args[0])
            if tp_dollar <= 0:
                raise ValueError("TP dollar amount must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['tp_dollar_amount'] = tp_dollar
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ TP dollar amount updated to *${tp_dollar}*", parse_mode='Markdown')
            logger.info(f"TP dollar amount updated to ${tp_dollar} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_max_loss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set max floating loss: /set_max_loss 500"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_max\\_loss <amount>\\nExample: /set\\_max\\_loss 500", parse_mode='Markdown')
            return
        
        try:
            max_loss = float(context.args[0])
            if max_loss <= 0:
                raise ValueError("Max floating loss must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['max_floating_loss'] = max_loss
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Max floating loss updated to *${max_loss}*", parse_mode='Markdown')
            logger.info(f"Max floating loss updated to ${max_loss} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_profit_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set take profit target: /set_profit_target 1000"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_profit\\_target <amount>\\nExample: /set\\_profit\\_target 1000", parse_mode='Markdown')
            return
        
        try:
            profit_target = float(context.args[0])
            if profit_target <= 0:
                raise ValueError("Take profit target must be positive")
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['max_floating_profit'] = profit_target
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Take profit target updated to *${profit_target}*", parse_mode='Markdown')
            logger.info(f"Take profit target updated to ${profit_target} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_set_ml(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle ML: /set_ml on or /set_ml off"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /set\\_ml <on|off>\\nExample: /set\\_ml on", parse_mode='Markdown')
            return
        
        try:
            ml_status = context.args[0].lower()
            if ml_status not in ['on', 'off']:
                raise ValueError("ML status must be 'on' or 'off'")
            
            use_ml = (ml_status == 'on')
            
            try:
                with open('hft_config_insta_golg_ls.json', 'r') as f:
                    config = json.load(f)
            except:
                config = {}
            
            config['use_ml'] = use_ml
            
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            status_emoji = "🟢" if use_ml else "🔴"
            await update.message.reply_text(f"{status_emoji} ML *{'enabled' if use_ml else 'disabled'}*", parse_mode='Markdown')
            logger.info(f"ML {'enabled' if use_ml else 'disabled'} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
    
    async def cmd_load_preset(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Load preset config: /load_preset GOLD"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text(
                "Usage: /load\\_preset <symbol>\\n\\nAvailable presets:\\n" +
                "• GOLD\\n• EURUSD\\n• XAUUSD\\n\\nExample: /load\\_preset GOLD",
                parse_mode='Markdown'
            )
            return
        
        preset = context.args[0].upper()
        filename = f"config_{preset}.json"
        
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            
            # Save as current config
            with open('hft_config_insta_golg_ls.json', 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(
                f"✅ *{preset} Configuration Loaded!*\\n\\n" +
                f"Symbol: {config.get('symbol', 'N/A')}\\n" +
                f"Volume: {config.get('default_volume', 'N/A')}\\n" +
                f"Min Signal: {config.get('min_signal_strength', 'N/A')}\\n" +
                f"Max Spread: {config.get('max_spread', 'N/A')}",
                parse_mode='Markdown'
            )
            logger.info(f"Preset {preset} loaded by user {update.effective_user.id}")
        except FileNotFoundError:
            await update.message.reply_text(f"❌ Preset file *{filename}* not found", parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text(f"❌ Error loading preset: {str(e)}")
    
    async def cmd_save_config(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save current config as preset: /save_config MYPRESET"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        if len(context.args) != 1:
            await update.message.reply_text("Usage: /save\\_config <name>\\nExample: /save\\_config MYPRESET", parse_mode='Markdown')
            return
        
        preset_name = context.args[0].upper()
        filename = f"config_{preset_name}.json"
        
        try:
            # Load current config
            with open('hft_config_insta_golg_ls.json', 'r') as f:
                config = json.load(f)
            
            # Save as preset
            with open(filename, 'w') as f:
                json.dump(config, f, indent=4)
            
            await update.message.reply_text(f"✅ Configuration saved as *{filename}*", parse_mode='Markdown')
            logger.info(f"Config saved as {filename} by user {update.effective_user.id}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error saving config: {str(e)}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help"""
        if not self.is_authorized(update.effective_user.id):
            await update.message.reply_text("❌ Unauthorized")
            return
        
        help_msg = """
📚 *Command Reference*
━━━━━━━━━━━━━━━━━━━━

*Monitoring:*
/status - System status & account info
/stats - Trading statistics  
/performance - Performance metrics
/risk - Risk management status
/positions - Current positions
/config - View configuration

*Control:*
/start\_trading - Start trading engine
/stop\_trading - Stop trading engine
/close\_all - Close all positions

*Configuration:*
/edit - Interactive config editor
/set\_symbol <val> - Set trading symbol
/set\_volume <val> - Set default volume
/set\_magic <val> - Set magic number
/set\_risk <val> - Set risk per trade %
/set\_signal <val> - Set min signal strength
/set\_spread <val> - Set max spread
/set\_volatility <val> - Set max volatility
/set\_filling <mode> - Set filling mode
/set\_sl\_mult <val> - Set SL multiplier
/set\_rr <val> - Set Risk:Reward ratio
/set\_tp\_mode <mode> - Set TP mode
/set\_tp\_dollar <val> - Set TP dollar amount
/set\_max\_loss <val> - Set max floating loss
/set\_profit\_target <val> - Set profit target
/set\_ml <on|off> - Toggle ML predictions

*Presets:*
/load\_preset <name> - Load preset (GOLD/EURUSD/XAUUSD)
/save\_config <name> - Save current as preset

*General:*
/help - Show this help
        """
        await update.message.reply_text(help_msg, parse_mode='Markdown')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if not self.is_authorized(query.from_user.id):
            await query.edit_message_text("❌ Unauthorized")
            return
        
        # Handle different button actions
        if data.startswith('edit_'):
            await query.edit_message_text("⚙️ Edit functionality not implemented yet")
        elif data == 'back_to_main':
            await query.edit_message_text("🏠 Back to main menu")
        elif data == 'confirm_start':
            await query.edit_message_text("▶️ Starting trading...")
        elif data == 'confirm_stop':
            await query.edit_message_text("⏹️ Stopping trading...")
        elif data == 'confirm_close_all':
            await query.edit_message_text("🔒 Closing all positions...")
        else:
            await query.edit_message_text("❓ Unknown action")
