import sys, os, ctypes
import time
from config_manager import ConfigManager
from thread_safety import ThreadSafeGUI, ThreadSafeCallback
from trade_database import TradeDatabase
from telegram_bot import TelegramBot
from gui_telegram_integration import get_gui_telegram_integration

# License System - Will be validated at startup
try:
    from license_check import enforce_license_on_startup
    from license_manager import LicenseManager
    from license_validator import validate_license_or_exit
    LICENSE_SYSTEM_AVAILABLE = True
except ImportError:
    # If license modules not available, will fail at startup
    LICENSE_SYSTEM_AVAILABLE = False
    validate_license_or_exit = None

def anti_debug():
    try:
        if ctypes.windll.kernel32.IsDebuggerPresent():
            os._exit(0)
    except Exception as e:
        print(f"Error:  {e}")

    try:
        if any(x in sys.argv[0].lower() for x in ["x64dbg", "olly", "ida", "ghidra"]):
            os._exit(0)
    except Exception as e:
        print(f"Error: {e}")

# anti_debug()
"""
Aventa HFT Pro 2026 - Modern GUI Launcher
Professional trading interface with real-time monitoring
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
import json
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import sys
import os
from collections import deque
import numpy as np
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Suppress Pylance warnings for lazy-loaded modules
if False: 
    import matplotlib.pyplot
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    import matplotlib.dates as mdates

# Translation dictionaries
TRANSLATIONS = {
    'EN': {
        'title': '🚀 AVENTA HFT PRO 2026 v7.3.6',
        'tab_control': '⚙️ Control Panel',
        'tab_performance': '📊 Performance',
        'tab_risk': '🛡️ Risk Management',
        'tab_ml': '🤖 ML Models',
        'tab_strategy': '🧪 Strategy Tester',
        'tab_logs': '📝 Logs',
        'tab_telegram': '📱 Telegram Service',
        'status_ready': 'Status: Ready',
        'status_trading': 'Status:  TRADING ACTIVE',
        'status_stopped': 'Status:  Stopped',
    },
    'ID': {
        'title': '🚀 AVENTA HFT PRO 2026 v7.3.6',
        'tab_control': '⚙️ Panel Kontrol',
        'tab_performance': '📊 Performa',
        'tab_risk': '🛡️ Manajemen Risiko',
        'tab_ml': '🤖 Model ML',
        'tab_strategy':  '🧪 Penguji Strategi',
        'tab_logs': '📝 Log',
        'tab_telegram': '📱 Layanan Telegram',
        'status_ready':  'Status:  Siap',
        'status_trading': 'Status: TRADING AKTIF',
        'status_stopped': 'Status: Dihentikan',
    }
}


class TextWidgetLogger:
    """Custom logging handler that redirects output to GUI Text widget"""
    def __init__(self, gui_instance):
        self.gui = gui_instance
        
    def write(self, message):
        """Write message to GUI logs (with filtering for repetitive system messages)"""
        if message.strip():
            try:
                # Filter out repetitive system/performance messages
                if self._should_filter_message(message):
                    return
                
                # Determine log level based on message content
                level = "INFO"
                if "ERROR" in message.upper() or "FAILED" in message.upper():
                    level = "ERROR"
                elif "WARNING" in message.upper() or "WARN" in message.upper():
                    level = "WARNING"
                elif "SUCCESS" in message.upper() or "✓" in message or "✅" in message:
                    level = "SUCCESS"
                    
                self.gui.log_message(message.strip(), level)
            except:
                pass
    
    def _should_filter_message(self, message):
        """Check if message should be filtered out (repetitive system updates)"""
        msg_lower = message.lower()
        
        # Filter out repetitive performance/system update messages
        filter_keywords = [
            "network update:",
            "disk update:",
            "cpu usage:",
            "memory usage:",
            "gpu usage:",
            "kb/s",
            "mb/s",
            "gb/s",
        ]
        
        for keyword in filter_keywords:
            if keyword in msg_lower:
                return True
        
        return False
    
    def flush(self):
        """Flush method for compatibility"""
        pass


class Tooltip:
    """Create a tooltip for a given widget"""
    def __init__(self, widget, text="", delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        
        # Bind events
        self.widget.bind("<Enter>", self.enter, add=True)
        self.widget.bind("<Leave>", self.leave, add=True)
        self.widget.bind("<ButtonPress>", self.leave, add=True)
    
    def enter(self, event=None):
        """Show tooltip on mouse enter"""
        self.schedule()
    
    def leave(self, event=None):
        """Hide tooltip on mouse leave or click"""
        self.unschedule()
        self.hidetip()
    
    def schedule(self):
        """Schedule tooltip to appear"""
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)
    
    def unschedule(self):
        """Cancel scheduled tooltip"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def showtip(self):
        """Show the tooltip"""
        if self.tipwindow or not self.text:
            return
        
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Style the tooltip
        label = tk.Label(tw, text=self.text, background="#FFE4B5", 
                        relief=tk.SOLID, borderwidth=1, font=("Arial", 9),
                        padx=5, pady=3)
        label.pack(ipadx=1)
    
    def hidetip(self):
        """Hide the tooltip"""
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


class HFTProGUI:
        def start_all_bots(self):
            """Start trading for all bots"""
            try:
                for bot_id in self.bots:
                    self.active_bot_id = bot_id
                    self.start_trading()
                self.log_message("\u2713 All bots started", "SUCCESS")
            except Exception as e:
                self.log_message(f"Start all bots error: {e}", "ERROR") 
        def stop_all_bots(self):
            """Stop trading for all bots"""
            try:
                for bot_id in self.bots:
                    if self.bots[bot_id]['is_running']:
                        self.active_bot_id = bot_id
                        self.stop_trading()
                self.log_message("\u2713 All bots stopped", "SUCCESS")
            except Exception as e:
                self.log_message(f"Stop all bots error: {e}", "ERROR")

        def save_session(self):
            """Save current session (bot list & configs)"""
            try:
                # ✅ FIX:  Save current active bot's GUI state first
                if self.active_bot_id and self.active_bot_id in self.bots:
                    self.save_gui_config_to_bot(self.active_bot_id)
                
                import copy
                session_data = {
                    'active_bot_id': self.active_bot_id,
                    'bots': {}
                }
                # Save each bot's config (not runtime objects)
                for bot_id, bot_data in self.bots.items():
                    session_data['bots'][bot_id] = {
                        'config': copy.deepcopy(bot_data['config'])  # ✅ Deep copy
                    }
                with open('hft_session.json', 'w') as f:
                    json.dump(session_data, f, indent=4)
                self.log_message("✓ Session saved", "SUCCESS")
            except Exception as e:
                self.log_message(f"Save session error: {e}", "ERROR")

        def load_session(self):
            """Load previous session"""
            try:
                if not os.path.exists('hft_session.json'):
                    return False
                
                import copy
                with open('hft_session.json', 'r') as f:
                    session_data = json.load(f)
                
                # ✅ Load data into memory first (safe to do in thread)
                loaded_bots = {}
                for bot_id, bot_data in session_data.get('bots', {}).items():
                    loaded_bots[bot_id] = {
                        'config': copy.deepcopy(bot_data['config']),
                        'engine': None,
                        'risk_manager': None,
                        'ml_predictor': None,
                        'is_running': False,
                        'update_thread': None
                    }
                
                active_bot = session_data.get('active_bot_id')
                
                # ✅ Now schedule the GUI updates to main thread
                def apply_session_to_gui():
                    self.bots.clear()
                    self.bot_listbox.delete(0, tk.END)
                    
                    # Add bots to listbox
                    for bot_id in loaded_bots.keys():
                        self.bots[bot_id] = loaded_bots[bot_id]
                        self.bot_listbox.insert(tk.END, bot_id)
                    
                    # Restore active bot
                    if active_bot and active_bot in self.bots:
                        idx = list(self.bots.keys()).index(active_bot)
                        self.bot_listbox.selection_clear(0, tk.END)
                        self.bot_listbox.selection_set(idx)
                        self.active_bot_id = active_bot
                        self.load_bot_config_to_gui(active_bot)
                    
                    # Restore telegram bots for bots that have telegram config
                    for bot_id, bot_data in self.bots.items():
                        config = bot_data['config']
                        if 'telegram' in config:
                            telegram_config = config['telegram']
                            token = telegram_config.get('token', '')
                            chat_ids = telegram_config.get('chat_ids', [])
                            if token and chat_ids:
                                self.telegram_bots[bot_id] = TelegramBot(token, chat_ids)
                                self.log_message(f"✓ Telegram bot restored for {bot_id}", "INFO")
                    
                    self.log_message("✓ Session restored", "SUCCESS")
                    
                    # Update Telegram bot selector if it exists
                    try:
                        if hasattr(self, 'telegram_bot_selector'):
                            self.update_telegram_bot_selector()
                    except:
                        pass
                
                self.root.after(0, apply_session_to_gui)
                return True
            except Exception as e: 
                self.log_message(f"Load session error: {e}", "WARNING")
                return False

        def on_closing(self):
            """Handle window close event"""
            try:
                # Stop Telegram integration
                if hasattr(self, 'telegram_integration'):
                    self.telegram_integration.stop_command_listener()
                
                # Save session before closing
                self.save_session()
                # Stop all running bots
                for bot_id, bot_data in self.bots.items():
                    if bot_data['is_running'] and bot_data['engine']:
                        bot_data['engine'].stop()
                self.root.destroy()
            except Exception as e:
                print(f"Close error: {e}")
                self.root.destroy()

        def export_session(self):
            """Export session to file"""
            try:
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Export Session"
                )
                if filename:
                    session_data = {
                        'active_bot_id': self.active_bot_id,
                        'bots': {}
                    }
                    for bot_id, bot_data in self.bots.items():
                        session_data['bots'][bot_id] = {'config': bot_data['config']}
                    with open(filename, 'w') as f:
                        json.dump(session_data, f, indent=4)
                    self.log_message(f"\u2713 Session exported to:  {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Export session error: {e}", "ERROR")

        def import_session(self):
            """Import session from file"""
            try:
                filename = filedialog.askopenfilename(
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Import Session"
                )
                if filename:
                    with open(filename, 'r') as f:
                        session_data = json.load(f)
                    # Clear current bots
                    self.bots.clear()
                    self.bot_listbox.delete(0, tk.END)
                    # Restore bots
                    for bot_id, bot_data in session_data.get('bots', {}).items():
                        self.bots[bot_id] = {
                            'config': bot_data['config'],
                            'engine': None,
                            'risk_manager': None,
                            'ml_predictor': None,
                            'is_running': False,
                            'update_thread': None
                        }
                        self.bot_listbox.insert(tk.END, bot_id)
                    # Restore active bot
                    active_bot = session_data.get('active_bot_id')
                    if active_bot and active_bot in self.bots:
                        idx = list(self.bots.keys()).index(active_bot)
                        self.bot_listbox.selection_clear(0, tk.END)
                        self.bot_listbox.selection_set(idx)
                        self.active_bot_id = active_bot
                        self.load_bot_config_to_gui(active_bot)
                    self.log_message(f"\u2713 Session imported from: {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Import session error: {e}", "ERROR")

        def __init__(self, root):
            self.root = root

            # ✅ NEW:  Initialize managers
            self.config_manager = ConfigManager()
            self.gui_safe = ThreadSafeGUI(root)
            self.trade_db = TradeDatabase()

            self.root.title("Aventa HFT Pro 2026 - Ultra Low Latency Trading System")
            self.root.geometry("1400x900")
            self.root.configure(bg='#0a0e27')
            
            # Language setting
            self.current_language = tk.StringVar(value='EN')
            
            # Style configuration
            self.style = ttk.Style()
            self.style.theme_use('clam')
            self.configure_styles()
            
            # Multi-bot support
            self.bots = {}
            self.active_bot_id = None
            
            # Telegram bot instances
            self.telegram_bots = {}
            
            # Initialize GUI-Telegram Integration
            self.telegram_integration = get_gui_telegram_integration(self)
            
            # For backward compatibility
            self.engine = None
            self.risk_manager = None
            self.ml_predictor = None
            self.config = {}
            
            # Lazy loading flags
            self.core_modules_loaded = False
            self.matplotlib_loaded = False
            
            # State
            self.is_running = False
            self.update_thread = None
            
            # Performance tracking
            self.chart_data = {
                'timestamps': deque(maxlen=300),
                'equity':  deque(maxlen=300),
                'balance': deque(maxlen=300),
            }
            
            # Performance display variables
            self.perf_vars = {
                'trades_today': tk.StringVar(value="0"),
                'wins': tk.StringVar(value="0"),
                'losses': tk.StringVar(value="0"),
                'win_rate': tk.StringVar(value="0.00%"),
                'daily_pnl': tk.StringVar(value="$0.00"),
                'signals': tk.StringVar(value="0"),
                'position': tk.StringVar(value="None"),
                'position_vol': tk.StringVar(value="0.00"),
                'total_lot_today': tk.StringVar(value="0.00"),
                'balance': tk.StringVar(value="$0.00"),
                'equity': tk.StringVar(value="$0.00"),
                'floating': tk.StringVar(value="$0.00"),
                'latency_avg': tk.StringVar(value="0.00ms"),
                'latency_max': tk.StringVar(value="0.00ms"),
                'ticks': tk.StringVar(value="0"),
                'exec_avg': tk.StringVar(value="0.00ms"),
                'exec_max': tk.StringVar(value="0.00ms"),
            }
            
            # Chart references
            self.figure = None
            self.canvas = None
            self.ax = None
            
            # Initialize config variables
            self.init_config_variables()

            # Initialize PC Performance variables
            self._prev_net_counters = None
            self._prev_net_time = None
            
            # Create GUI
            self.create_gui()
            
            # Setup logging to GUI (redirect stdout/stderr to logs tab)
            self.root.after(100, self.setup_logging)
            
            # Start performance update loop
            self.root.after(1000, self.update_performance_display)
            
            # Load configuration asynchronously
            self.root.after(100, self.async_init)

            # Add protocol handler to save session on close
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


        def update_button_states(self):
            """Update button states"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if bot['is_running']:
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                else:
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
            except Exception as e:
                self.log_message(f"Update button states error: {e}", "ERROR")

        def on_language_changed(self, event=None):
            """Handle language change"""
            try:
                self.log_message("Language changed", "INFO")
            except Exception as e:
                self.log_message(f"Language change error: {e}", "ERROR")

        def async_init(self):
            """Async initialization"""
            def init_thread():
                try:
                    session_loaded = [False]
                    def try_load():
                        session_loaded[0] = self.load_session()
                    self.root.after(0, try_load)
                    time.sleep(0.1)

                    if not session_loaded[0]:
                        self.root.after(0, lambda: self.add_bot(default=True))
                        if os.path.exists("config_GOLD.ls.json"):
                            with open("config_GOLD.ls.json", 'r') as f:
                                config = json.load(f)
                            self.root.after(0, lambda: self.apply_config(config))
                            self.root.after(0, lambda: self.log_message("✓ Auto-loaded GOLD config", "SUCCESS"))

                    # Start Telegram command listener
                    self.telegram_integration.start_command_listener()
                    self.root.after(0, lambda: self.log_message("✓ Telegram integration ready", "SUCCESS"))
                    
                    self.root.after(0, lambda: self.log_message("System ready. Configure and click START TRADING.", "INFO"))
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"Init warning: {str(e)}", "WARNING"))

            threading.Thread(target=init_thread, daemon=True).start()

        def log_message(self, message, level="INFO"):
            """Add log message with timestamp"""
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                formatted_msg = f"[{timestamp}] [{level}] {message}\n"
                
                if hasattr(self, 'log_text'):
                    self.log_text.insert(tk.END, formatted_msg, level)
                    self.log_text.see(tk.END)
                    
                # Also log to ML training logs if on ML tab
                if hasattr(self, 'ml_log_text') and level in ["SUCCESS", "ERROR", "WARNING"]:
                    self.ml_log_text.insert(tk.END, formatted_msg, level)
                    self.ml_log_text.see(tk.END)
                    
                # Don't print to console, only to GUI logs
            except Exception as e:
                pass

        def setup_logging(self):
            """Setup logging to redirect stdout/stderr to GUI logs tab"""
            try:
                # Create custom logger
                logger_stream = TextWidgetLogger(self)
                
                # Redirect stdout and stderr to GUI
                sys.stdout = logger_stream
                sys.stderr = logger_stream
                
                self.log_message("✓ Logging system initialized - All console output redirected to Logs tab", "SUCCESS")
            except Exception as e:
                print(f"Setup logging error: {e}")

        def log_ml_message(self, message, level="INFO"):
            """Add message to ML training log"""
            try:
                if hasattr(self, 'ml_log_text'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] [{level}] {message}\n"
                    self.ml_log_text.insert(tk.END, log_entry, level)
                    self.ml_log_text.see(tk.END)
                
                # Also log to main log
                self.log_message(message, level)
            except Exception as e:
                print(f"ML logging error: {e}")
        
        def init_config_variables(self):
            """Initialize all configuration variables"""
            # Trading Configuration
            self.symbol_var = tk.StringVar(value="GOLD.ls")
            self.volume_var = tk.StringVar(value="0.01")
            self.magic_var = tk.StringVar(value="2026002")
            self.risk_var = tk.StringVar(value="1.0")
            self.signal_strength_var = tk.StringVar(value="0.45")
            self.max_spread_var = tk.StringVar(value="0.12")
            self.max_volatility_var = tk.StringVar(value="0.005")
            self.filling_mode_var = tk.StringVar(value="FOK")
            self.sl_multiplier_var = tk.StringVar(value="50.0")
            self.risk_reward_var = tk.StringVar(value="2.0")
            self.tp_mode_var = tk.StringVar(value="FixedDollar")
            self.tp_dollar_var = tk.StringVar(value="0.8")
            self.max_floating_loss_var = tk.StringVar(value="5")
            self.max_floating_profit_var = tk.StringVar(value="0.5")
            self.mt5_path_var = tk.StringVar(value="C:\\Program Files\\MT5\\terminal64.exe")
            self.enable_ml_var = tk.BooleanVar(value=False)
            # Commission Configuration (TAMBAHKAN INI)
            self.commission_var = tk.StringVar(value="0.9")  # Default $0.90 per trade
            
            # Indicator Configuration
            self.ema_fast_var = tk.StringVar(value="7")
            self.ema_slow_var = tk.StringVar(value="21")
            self.rsi_period_var = tk.StringVar(value="7")
            self.rsi_overbought_var = tk.StringVar(value="68")
            self.rsi_oversold_var = tk.StringVar(value="32")
            self.atr_period_var = tk.StringVar(value="14")
            self.momentum_period_var = tk.StringVar(value="5")
            
            # Risk Limits
            self.limit_vars = {
                'max_daily_loss': tk.StringVar(value="40"),
                'daily_target_profit': tk.StringVar(value="0"),  # ✅ NEW: Daily target profit
                'max_daily_trades': tk.StringVar(value="1000"),
                'max_daily_volume': tk.StringVar(value="10"),
                'max_position_size': tk.StringVar(value="2"),
                'max_positions': tk.StringVar(value="20"),
                'max_drawdown_pct': tk.StringVar(value="10")
            }
            
            # Telegram Configuration
            self.telegram_token_var = tk.StringVar(value="")
            self.telegram_chat_ids_var = tk.StringVar(value="")
            self.telegram_bots = {}  # Dictionary to store telegram bots per bot_id


        def t(self, key):
            """Get translated text for current language"""
            lang = self.current_language.get()
            return TRANSLATIONS.get(lang, TRANSLATIONS['EN']).get(key, key)
        
        def configure_styles(self):
            """Configure modern dark theme styles"""
            bg_color = '#0a0e27'
            label_bg = "#1a1e3a"
            secondary_bg = "#252952"
            tertiary_bg = "#2d3561"
            fg_color = '#e0e0e0'
            accent_secondary = '#7c4dff'
            success_color = '#00e676'
            danger_color = '#ff1744'
            
            self.style.configure('TFrame', background=bg_color)
            self.style.configure('TLabel', background=label_bg, foreground=fg_color, font=('Segoe UI', 10))
            self.style.configure('Title.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#ffffff', background=bg_color)
            self.style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'), foreground=accent_secondary, background=label_bg)
            self.style.configure('Metric.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#00e676', background=label_bg)
            self.style.configure('TButton', font=('Segoe UI', 10, 'bold'))
            self.style.configure('Start.TButton', background=success_color, foreground='#000000')
            self.style.configure('Stop.TButton', background=danger_color, foreground='#ffffff')
            self.style.configure('TEntry', fieldbackground=secondary_bg, foreground=fg_color)
            self.style.configure('TCombobox', fieldbackground='#000000', foreground='#ffffff')
            self.style.configure('TCheckbutton', background=label_bg, foreground=fg_color)
            # Progress bar style - Green color
            self.style.configure('Backtest.Horizontal.TProgressbar', background='#00e676', troughcolor='#1a1e3a')
            
            # ✅ Red Scrollbar Style
            self.style.configure('Red.Vertical.TScrollbar', background='#ff1744', troughcolor='#1a1e3a', 
                               lightcolor='#ff1744', darkcolor='#ff1744', bordercolor='#ff1744',
                               arrowcolor='#ffffff')
            self.style.configure('Red.Horizontal.TScrollbar', background='#ff1744', troughcolor='#1a1e3a',
                               lightcolor='#ff1744', darkcolor='#ff1744', bordercolor='#ff1744',
                               arrowcolor='#ffffff')
        
        def create_gui(self):
            """Create main GUI layout"""
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.pack(fill=tk.BOTH, expand=True)

            content_frame = ttk.Frame(main_frame)
            content_frame.pack(fill=tk.BOTH, expand=True)

            # Sidebar
            sidebar = ttk.Frame(content_frame, width=220, padding="5")
            sidebar.pack(side=tk.LEFT, fill=tk.Y)
            sidebar.pack_propagate(False)

            ttk.Label(sidebar, text="🤖 Bots", font=('Segoe UI', 12, 'bold')).pack(pady=(0, 5))

            # ✅ IMPROVED: Custom Listbox with PERSISTENT selection highlight across tab switches
            self.bot_listbox = tk.Listbox(
                sidebar, 
                height=12, 
                font=('Segoe UI', 10, 'bold'),
                bg='#1a1e3a', 
                fg='#e0e0e0',
                selectbackground='#00e676',  # ← Bright green highlight (PERSISTENT)
                selectforeground='#000000',  # ← Black text untuk kontras
                activestyle='none',  # ← Disable default active style
                exportselection=False,  # ✅ CRITICAL: Prevent losing selection when focus changes!
                relief=tk.FLAT,  # ← Cleaner appearance
                highlightthickness=0  # ← Remove border
            )
            self.bot_listbox.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            self.bot_listbox.bind('<<ListboxSelect>>', self.on_bot_selected)

            btn_frame = ttk.Frame(sidebar)
            btn_frame.pack(fill=tk.X, pady=(5, 0))

            # Row 1
            btn_row1 = ttk.Frame(btn_frame)
            btn_row1.pack(fill=tk.X, pady=2)
            add_btn = ttk.Button(btn_row1, text="➕ Add", command=self.on_add_bot_disabled, width=10)
            add_btn.pack(side=tk.LEFT, padx=2)
            Tooltip(add_btn, "Silahkan hubungi CS kami")
            
            remove_btn = ttk.Button(btn_row1, text="🗑️ Remove", command=self.on_remove_bot_disabled, width=13)
            remove_btn.pack(side=tk.LEFT, padx=2)
            Tooltip(remove_btn, "Silahkan hubungi CS kami")

            # Row 2 - RENAME button
            btn_row2 = ttk.Frame(btn_frame)
            btn_row2.pack(fill=tk.X, pady=2)
            ttk.Button(btn_row2, text="✏️ Rename", command=self.rename_bot, width=23).pack(padx=2)

            # Row 3 - EXPORT/IMPORT buttons
            btn_row3 = ttk.Frame(btn_frame)
            btn_row3.pack(fill=tk.X, pady=2)
            ttk.Button(btn_row3, text="📤 Export", command=self.export_session, width=11).pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_row3, text="📥 Import", command=self.import_session, width=11).pack(side=tk.LEFT, padx=2)

            # Row 4 - START/STOP ALL buttons
            btn_row4 = ttk.Frame(btn_frame)
            btn_row4.pack(fill=tk.X, pady=2)
            ttk.Button(btn_row4, text="▶️ Start All", command=self.start_all_bots, width=11, 
                    style='Start.TButton').pack(side=tk.LEFT, padx=2)
            ttk.Button(btn_row4, text="⏹️ Stop All", command=self.stop_all_bots, width=11, 
                    style='Stop.TButton').pack(side=tk.LEFT, padx=2)

            # Main content
            main_content = ttk.Frame(content_frame)
            main_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Header
            header_frame = ttk.Frame(main_content)
            header_frame.pack(fill=tk.X, pady=(0, 10))

            # === PC PERFORMANCE MONITOR (NEW) ===
            perf_sidebar = ttk.Frame(main_content, width=200, padding="5")
            perf_sidebar.pack(side=tk.RIGHT, fill=tk.Y)
            perf_sidebar.pack_propagate(False)

            ttk.Label(perf_sidebar, text="💻 PC Performance", 
                    font=('Segoe UI', 10, 'bold')).pack(pady=(0, 10))

            # CPU
            self.cpu_label = ttk.Label(perf_sidebar, text="CPU: 0%", font=('Segoe UI', 9))
            self.cpu_label.pack(anchor=tk.W, padx=5)

            # RAM
            self.ram_label = ttk.Label(perf_sidebar, text="RAM: 0%", font=('Segoe UI', 9))
            self.ram_label.pack(anchor=tk.W, padx=5)

            # GPU (if available)
            self.gpu_label = ttk.Label(perf_sidebar, text="GPU: N/A", font=('Segoe UI', 9))
            self.gpu_label.pack(anchor=tk.W, padx=5)

            # Network
            self.net_label = ttk.Label(perf_sidebar, text="Network: 0 KB/s", font=('Segoe UI', 9))
            self.net_label.pack(anchor=tk.W, padx=5)

            # Disk
            self.disk_label = ttk.Label(perf_sidebar, text="Disk: 0%", font=('Segoe UI', 9))
            self.disk_label.pack(anchor=tk.W, padx=5)

            # Start monitor
            self.root.after(1000, self.update_pc_performance)

            self.title_label = ttk.Label(header_frame, text=self.t('title'), style='Title.TLabel')
            self.title_label.pack(side=tk.LEFT)

            # Language selector
            lang_frame = ttk.Frame(header_frame)
            lang_frame.pack(side=tk.RIGHT)

            ttk.Label(lang_frame, text="🌐", font=('Segoe UI', 14), 
                    background='#0a0e27', foreground='#ffffff').pack(side=tk.LEFT, padx=(0, 5))

            lang_selector = ttk.Combobox(lang_frame, textvariable=self.current_language,
                                        values=['EN', 'ID'], width=5, state='readonly')
            lang_selector.pack(side=tk.LEFT)
            lang_selector.bind('<<ComboboxSelected>>', self.on_language_changed)

            # Notebook
            self.notebook = ttk.Notebook(main_content)
            self.notebook.pack(fill=tk.BOTH, expand=True)

            self.control_tab = ttk.Frame(self.notebook)
            self.performance_tab = ttk.Frame(self.notebook)
            self.risk_tab = ttk.Frame(self.notebook)
            self.ml_tab = ttk.Frame(self.notebook)
            self.strategy_tab = ttk.Frame(self.notebook)
            self.log_tab = ttk.Frame(self.notebook)
            self.telegram_tab = ttk.Frame(self.notebook)

            self.notebook.add(self.control_tab, text=self.t('tab_control'))
            self.notebook.add(self.performance_tab, text=self.t('tab_performance'))
            self.notebook.add(self.risk_tab, text=self.t('tab_risk'))
            self.notebook.add(self.ml_tab, text=self.t('tab_ml'))
            self.notebook.add(self.strategy_tab, text=self.t('tab_strategy'))
            self.notebook.add(self.log_tab, text=self.t('tab_logs'))
            self.notebook.add(self.telegram_tab, text=self.t('tab_telegram'))

            # Add this binding before building tabs
            self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)

            # Build tabs
            self.build_control_tab()
            self.build_performance_tab()
            self.build_log_tab()
            self.build_risk_tab()
            self.build_ml_tab()
            self.build_strategy_tab()
            self.build_telegram_tab()

            # Status bar
            self.status_bar = ttk.Label(main_content, text=self.t('status_ready'), relief=tk.SUNKEN, anchor=tk.W,
                                        background='#1a1e3a', foreground='#00e676')
            self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

        def build_control_tab(self):
            """Build comprehensive control panel tab"""
            try:
                # Create scrollable frame
                canvas = tk.Canvas(self.control_tab, bg='#0a0e27', highlightthickness=0)
                scrollbar = ttk.Scrollbar(self.control_tab, orient="vertical", command=canvas.yview, style='Red.Vertical.TScrollbar')
                scrollable_frame = ttk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

            # ✅ ADD THIS: Active Bot Indicator at TOP of Control Panel
                active_bot_frame = ttk.Frame(scrollable_frame, style='TFrame')
                active_bot_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
                
                ttk.Label(
                    active_bot_frame, 
                    text="🎯 Editing Bot:", 
                    font=('Segoe UI', 11, 'bold'),
                    foreground='#7c4dff',
                    background='#0a0e27'
                ).pack(side=tk.LEFT, padx=5)
                
                self.active_bot_indicator = ttk.Label(
                    active_bot_frame,
                    text="None",
                    font=('Segoe UI', 11, 'bold'),
                    foreground='#00e676',
                    background='#0a0e27'
                )
                self.active_bot_indicator.pack(side=tk.LEFT, padx=5)    

                # === TRADING CONFIGURATION ===
                config_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Trading Configuration", padding=10)
                config_frame.pack(fill=tk.X, padx=10, pady=5)

                # Row 1: Symbol, Volume, Magic
                row1 = ttk.Frame(config_frame)
                row1.pack(fill=tk.X, pady=2)
                
                ttk.Label(row1, text="Symbol:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row1, textvariable=self.symbol_var, width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row1, text="Volume:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row1, textvariable=self.volume_var, width=10).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row1, text="Magic:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row1, textvariable=self.magic_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 2: Risk, Signal Strength, Max Spread
                row2 = ttk.Frame(config_frame)
                row2.pack(fill=tk.X, pady=2)
                
                ttk.Label(row2, text="Risk per Trade (%):", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row2, textvariable=self.risk_var, width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row2, text="Min Signal:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row2, textvariable=self.signal_strength_var, width=10).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row2, text="Max Spread:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row2, textvariable=self.max_spread_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 3: Max Volatility, Filling Mode, SL Multiplier
                row3 = ttk.Frame(config_frame)
                row3.pack(fill=tk.X, pady=2)
                
                ttk.Label(row3, text="Max Volatility:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row3, textvariable=self.max_volatility_var, width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row3, text="Filling Mode:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Combobox(row3, textvariable=self.filling_mode_var, values=['FOK', 'IOC', 'RETURN'], 
                            width=8, state='readonly').pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row3, text="SL Multiplier:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row3, textvariable=self.sl_multiplier_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 4: Risk: Reward, TP Mode, TP Amount
                row4 = ttk.Frame(config_frame)
                row4.pack(fill=tk.X, pady=2)
                
                ttk.Label(row4, text="Risk: Reward Ratio:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row4, textvariable=self.risk_reward_var, width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row4, text="TP Mode:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Combobox(row4, textvariable=self.tp_mode_var, values=['FixedDollar', 'RiskReward'], 
                            width=11, state='readonly').pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row4, text="TP Amount ($):", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row4, textvariable=self.tp_dollar_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 5: Max Floating Loss/Profit
                row5 = ttk.Frame(config_frame)
                row5.pack(fill=tk.X, pady=2)
                
                ttk.Label(row5, text="Max Floating Loss ($):", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row5, textvariable=self.max_floating_loss_var, width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(row5, text="TP Target ($):", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(row5, textvariable=self.max_floating_profit_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 6: Commission Settings (TAMBAHKAN INI SETELAH ROW 5)
                row6 = ttk.Frame(config_frame)
                row6.pack(fill=tk.X, pady=2)

                ttk.Label(row6, text="Commission per Trade ($):", width=20).pack(side=tk.LEFT, padx=5)
                self.commission_var = tk.StringVar(value="0.0")  # Default $0.90
                ttk.Entry(row6, textvariable=self.commission_var, width=15).pack(side=tk.LEFT, padx=5)

                ttk.Label(row6, text="ℹ️ Set broker commission per round-trip trade", 
                        font=('Segoe UI', 8), foreground='#7c4dff').pack(side=tk.LEFT, padx=5)

                # === TRADING SESSIONS ===
                session_frame = ttk.LabelFrame(scrollable_frame, text="⏰ Trading Sessions (WIB/UTC+7)", padding=10)
                session_frame.pack(fill=tk.X, padx=10, pady=5)

                # Row 1: Enable Sessions
                session_row1 = ttk.Frame(session_frame)
                session_row1.pack(fill=tk.X, pady=2)
                self.trading_sessions_enabled = tk.BooleanVar(value=True)
                ttk.Checkbutton(session_row1, text="Enable Trading Session Restrictions", 
                              variable=self.trading_sessions_enabled).pack(side=tk.LEFT, padx=5)

                # Row 2: London Session
                session_row2 = ttk.Frame(session_frame)
                session_row2.pack(fill=tk.X, pady=2)
                self.london_session_enabled = tk.BooleanVar(value=True)
                ttk.Checkbutton(session_row2, text="🇬🇧 London Session (15:00-23:30 WIB)", 
                              variable=self.london_session_enabled).pack(side=tk.LEFT, padx=5)
                ttk.Label(session_row2, text="Start:", width=6).pack(side=tk.LEFT, padx=2)
                self.london_start_var = tk.StringVar(value="15:00")
                ttk.Entry(session_row2, textvariable=self.london_start_var, width=8).pack(side=tk.LEFT, padx=2)
                ttk.Label(session_row2, text="End:", width=6).pack(side=tk.LEFT, padx=2)
                self.london_end_var = tk.StringVar(value="23:30")
                ttk.Entry(session_row2, textvariable=self.london_end_var, width=8).pack(side=tk.LEFT, padx=2)

                # Row 3: NY Session
                session_row3 = ttk.Frame(session_frame)
                session_row3.pack(fill=tk.X, pady=2)
                self.ny_session_enabled = tk.BooleanVar(value=True)
                ttk.Checkbutton(session_row3, text="🗽 New York Session (20:00-04:00 WIB)", 
                              variable=self.ny_session_enabled).pack(side=tk.LEFT, padx=5)
                ttk.Label(session_row3, text="Start:", width=6).pack(side=tk.LEFT, padx=2)
                self.ny_start_var = tk.StringVar(value="20:00")
                ttk.Entry(session_row3, textvariable=self.ny_start_var, width=8).pack(side=tk.LEFT, padx=2)
                ttk.Label(session_row3, text="End:", width=6).pack(side=tk.LEFT, padx=2)
                self.ny_end_var = tk.StringVar(value="04:00")
                ttk.Entry(session_row3, textvariable=self.ny_end_var, width=8).pack(side=tk.LEFT, padx=2)

                # Row 4: Asia Session
                session_row4 = ttk.Frame(session_frame)
                session_row4.pack(fill=tk.X, pady=2)
                self.asia_session_enabled = tk.BooleanVar(value=False)
                ttk.Checkbutton(session_row4, text="🏮 Asia Session (05:00-15:00 WIB)", 
                              variable=self.asia_session_enabled).pack(side=tk.LEFT, padx=5)
                ttk.Label(session_row4, text="Start:", width=6).pack(side=tk.LEFT, padx=2)
                self.asia_start_var = tk.StringVar(value="05:00")
                ttk.Entry(session_row4, textvariable=self.asia_start_var, width=8).pack(side=tk.LEFT, padx=2)
                ttk.Label(session_row4, text="End:", width=6).pack(side=tk.LEFT, padx=2)
                self.asia_end_var = tk.StringVar(value="15:00")
                ttk.Entry(session_row4, textvariable=self.asia_end_var, width=8).pack(side=tk.LEFT, padx=2)

                # === TECHNICAL INDICATORS ===
                indicator_frame = ttk.LabelFrame(scrollable_frame, text="📊 Technical Indicators", padding=10)
                indicator_frame.pack(fill=tk.X, padx=10, pady=5)

                # Row 1: EMA Settings
                ind_row1 = ttk.Frame(indicator_frame)
                ind_row1.pack(fill=tk.X, pady=2)
                
                ttk.Label(ind_row1, text="EMA Fast Period:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row1, textvariable=self.ema_fast_var, width=10).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(ind_row1, text="EMA Slow Period:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row1, textvariable=self.ema_slow_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 2: RSI Settings
                ind_row2 = ttk.Frame(indicator_frame)
                ind_row2.pack(fill=tk.X, pady=2)
                
                ttk.Label(ind_row2, text="RSI Period:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row2, textvariable=self.rsi_period_var, width=10).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(ind_row2, text="RSI Overbought:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row2, textvariable=self.rsi_overbought_var, width=10).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(ind_row2, text="RSI Oversold:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row2, textvariable=self.rsi_oversold_var, width=10).pack(side=tk.LEFT, padx=5)

                # Row 3: ATR & Momentum
                ind_row3 = ttk.Frame(indicator_frame)
                ind_row3.pack(fill=tk.X, pady=2)
                
                ttk.Label(ind_row3, text="ATR Period:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row3, textvariable=self.atr_period_var, width=10).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(ind_row3, text="Momentum Period:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(ind_row3, textvariable=self.momentum_period_var, width=10).pack(side=tk.LEFT, padx=5)

                # === MT5 & ML SETTINGS ===
                mt5_frame = ttk.LabelFrame(scrollable_frame, text="🔧 MT5 & ML Settings", padding=10)
                mt5_frame.pack(fill=tk.X, padx=10, pady=5)

                mt5_row = ttk.Frame(mt5_frame)
                mt5_row.pack(fill=tk.X, pady=2)
                
                ttk.Label(mt5_row, text="MT5 Path:", width=15).pack(side=tk.LEFT, padx=5)
                ttk.Entry(mt5_row, textvariable=self.mt5_path_var, width=50).pack(side=tk.LEFT, padx=5)
                ttk.Button(mt5_row, text="📁 Browse", command=self.browse_mt5_path, width=10).pack(side=tk.LEFT, padx=5)

                ml_row = ttk.Frame(mt5_frame)
                ml_row.pack(fill=tk.X, pady=2)
                
                ttk.Checkbutton(ml_row, text="Enable ML Predictions", variable=self.enable_ml_var).pack(side=tk.LEFT, padx=5)

                # === CONTROL BUTTONS ===
                button_frame = ttk.Frame(scrollable_frame)
                button_frame.pack(fill=tk.X, padx=10, pady=10)

                self.start_btn = ttk.Button(button_frame, text="▶️ START TRADING", 
                                        command=self.start_trading, style='Start.TButton', width=20)
                self.start_btn.pack(side=tk.LEFT, padx=5)

                # ✅ NEW: Manual close positions button
                ttk.Button(button_frame, text="❌ Close All Positions", 
                        command=self.manual_close_all_positions, width=20).pack(side=tk.LEFT, padx=5)
                
                self.stop_btn = ttk.Button(button_frame, text="⏹️ STOP TRADING", 
                        command=self.stop_trading, style='Stop.TButton', width=20, state=tk.DISABLED)
                self.stop_btn.pack(side=tk.LEFT, padx=5)
                
                ttk.Button(button_frame, text="💾 Save Config", command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="📁 Load Config", command=self.load_config_dialog, width=15).pack(side=tk.LEFT, padx=5)

                # === PRESET BUTTONS ===
                preset_frame = ttk.LabelFrame(scrollable_frame, text="⚡ Quick Load Presets", padding=10)
                preset_frame.pack(fill=tk.X, padx=10, pady=5)

                preset_buttons = ttk.Frame(preset_frame)
                preset_buttons.pack(fill=tk.X)
                
                ttk.Button(preset_buttons, text="🥇 GOLD Config", command=lambda: self.load_preset("config_GOLD.ls.json"), width=15).pack(side=tk.LEFT, padx=5)
                ttk.Button(preset_buttons, text="💱 EURUSD Config", command=lambda:  self.load_preset("config_EURUSD.json"), width=19).pack(side=tk.LEFT, padx=5)
                ttk.Button(preset_buttons, text="🏅 XAUUSD Config", command=lambda: self.load_preset("config_XAUUSD.json"), width=19).pack(side=tk.LEFT, padx=5)
                ttk.Button(preset_buttons, text="₿ BTCUSD Config", command=lambda: self.load_preset("config_BTCUSD.json"), width=15).pack(side=tk.LEFT, padx=5)

            except Exception as e:
                self.log_message(f"Build control tab error: {e}", "ERROR")

        def build_performance_tab(self):
            """Build comprehensive performance monitoring tab"""
            try:
                # Main container with scrolling
                main_container = ttk.Frame(self.performance_tab)
                main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # === ACTIVE BOT INDICATOR ===
                bot_indicator_frame = ttk.Frame(main_container)
                bot_indicator_frame.pack(fill=tk.X, pady=(0, 10))
                
                ttk.Label(bot_indicator_frame, text="Monitoring Bot:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
                
                self.active_bot_label = ttk.Label(bot_indicator_frame, text="None", 
                                                font=('Segoe UI', 10, 'bold'), foreground='#00e676')
                self.active_bot_label.pack(side=tk.LEFT, padx=5)

                # === TRADING METRICS ===
                metrics_frame = ttk.LabelFrame(main_container, text="📊 Real-Time Trading Metrics", padding=10)
                metrics_frame.pack(fill=tk.X, pady=(0, 10))

                # Row 1: Trades, Wins, Losses, Win Rate
                metrics_row1 = ttk.Frame(metrics_frame)
                metrics_row1.pack(fill=tk.X, pady=2)
                
                self.create_metric_display(metrics_row1, "Trades Today:", self.perf_vars['trades_today'], width=12)
                self.create_metric_display(metrics_row1, "Wins:", self.perf_vars['wins'], width=10)
                self.create_metric_display(metrics_row1, "Losses:", self.perf_vars['losses'], width=10)
                self.create_metric_display(metrics_row1, "Win Rate:", self.perf_vars['win_rate'], width=12)

                # Row 2: Daily P&L, Signals, Position, Volume, Total Lot Today
                metrics_row2 = ttk.Frame(metrics_frame)
                metrics_row2.pack(fill=tk.X, pady=2)
                
                self.create_metric_display(metrics_row2, "Daily P&L:", self.perf_vars['daily_pnl'], width=15)
                self.create_metric_display(metrics_row2, "Signals:", self.perf_vars['signals'], width=10)
                self.create_metric_display(metrics_row2, "Position:", self.perf_vars['position'], width=10)
                self.create_metric_display(metrics_row2, "Volume:", self.perf_vars['position_vol'], width=10)
                self.create_metric_display(metrics_row2, "Total Lot Today:", self.perf_vars['total_lot_today'], width=15)

                # === ACCOUNT METRICS ===
                account_frame = ttk.LabelFrame(main_container, text="💰 Account Status", padding=10)
                account_frame.pack(fill=tk.X, pady=(0, 10))

                account_row = ttk.Frame(account_frame)
                account_row.pack(fill=tk.X, pady=2)
                
                self.create_metric_display(account_row, "Balance:", self.perf_vars['balance'], width=15)
                self.create_metric_display(account_row, "Equity:", self.perf_vars['equity'], width=15)
                self.create_metric_display(account_row, "Floating P&L:", self.perf_vars['floating'], width=15)

                # === PERFORMANCE METRICS ===
                perf_frame = ttk.LabelFrame(main_container, text="⚡ Performance Metrics", padding=10)
                perf_frame.pack(fill=tk.X, pady=(0, 10))

                # Row 1: Latency
                perf_row1 = ttk.Frame(perf_frame)
                perf_row1.pack(fill=tk.X, pady=2)
                
                self.create_metric_display(perf_row1, "Avg Latency:", self.perf_vars['latency_avg'], width=15)
                self.create_metric_display(perf_row1, "Max Latency:", self.perf_vars['latency_max'], width=15)
                self.create_metric_display(perf_row1, "Ticks Processed:", self.perf_vars['ticks'], width=15)

                # Row 2: Execution
                perf_row2 = ttk.Frame(perf_frame)
                perf_row2.pack(fill=tk.X, pady=2)
                
                self.create_metric_display(perf_row2, "Avg Exec Time:", self.perf_vars['exec_avg'], width=15)
                self.create_metric_display(perf_row2, "Max Exec Time:", self.perf_vars['exec_max'], width=15)

                # === EQUITY CURVE CHART ===
                chart_frame = ttk.LabelFrame(main_container, text="📈 Equity Curve", padding=10)
                chart_frame.pack(fill=tk.BOTH, expand=True)

                # Chart container
                self.chart_container = ttk.Frame(chart_frame)
                self.chart_container.pack(fill=tk.BOTH, expand=True)

                # Initialize chart
                self.init_equity_chart()

                # Chart controls
                chart_controls = ttk.Frame(chart_frame)
                chart_controls.pack(fill=tk.X, pady=(5, 0))
                
                ttk.Button(chart_controls, text="🔄 Reset Chart", command=self.reset_chart, width=15).pack(side=tk.LEFT, padx=5)
                ttk.Label(chart_controls, text="📈 Real-time updates every 1 second", 
                        foreground='#7c4dff', font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=10)

            except Exception as e: 
                self.log_message(f"Build performance tab error: {e}", "ERROR")

        def create_metric_display(self, parent, label_text, variable, width=15):
            """Create a metric display widget"""
            container = ttk.Frame(parent)
            container.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(container, text=label_text, font=('Segoe UI', 9)).pack(side=tk.LEFT)
            ttk.Label(container, textvariable=variable, style='Metric.TLabel', width=width).pack(side=tk.LEFT, padx=(5, 0))

        def init_equity_chart(self):
            """Initialize matplotlib chart for equity curve"""
            try:
                if not self.matplotlib_loaded:
                    import matplotlib
                    matplotlib.use('TkAgg')
                    import matplotlib.pyplot as plt
                    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
                    from matplotlib.figure import Figure
                    self.matplotlib_loaded = True
                    self.log_message("✓ Chart library loaded", "SUCCESS")

                from matplotlib.figure import Figure
                from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

                # Create figure with dark theme
                self.figure = Figure(figsize=(10, 4), dpi=100, facecolor='#1a1e3a')
                self.ax = self.figure.add_subplot(111, facecolor='#0a0e27')
                
                # Style
                self.ax.set_title('Real-Time Equity Curve', color='#e0e0e0', fontsize=12, fontweight='bold')
                self.ax.set_xlabel('Time', color='#e0e0e0')
                self.ax.set_ylabel('Equity ($)', color='#e0e0e0')
                self.ax.tick_params(colors='#e0e0e0')
                self.ax.grid(True, alpha=0.2, color='#7c4dff')
                self.ax.spines['bottom'].set_color('#7c4dff')
                self.ax.spines['top'].set_color('#7c4dff')
                self.ax.spines['left'].set_color('#7c4dff')
                self.ax.spines['right'].set_color('#7c4dff')

                # Initial empty plot
                self.equity_line, = self.ax.plot([], [], color='#00e676', linewidth=2, label='Equity')
                self.balance_line, = self.ax.plot([], [], color='#00b0ff', linewidth=1, linestyle='--', label='Balance')
                self.ax.legend(facecolor='#1a1e3a', edgecolor='#7c4dff', labelcolor='#e0e0e0')

                # Embed in tkinter
                self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_container)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            except Exception as e: 
                self.log_message(f"Chart init error: {e}", "ERROR")

        def update_equity_chart(self):
            """Update equity curve chart with latest data"""
            try:
                if not self.matplotlib_loaded or self.ax is None:
                    return

                if len(self.chart_data['timestamps']) == 0:
                    return

                # Update data
                timestamps = list(self.chart_data['timestamps'])
                equity = list(self.chart_data['equity'])
                balance = list(self.chart_data['balance'])

                # Validate data (remove NaN/Inf)
                valid_indices = []
                for i, (e, b) in enumerate(zip(equity, balance)):
                    import math
                    if not math.isnan(e) and not math.isinf(e) and not math.isnan(b) and not math.isinf(b):
                        valid_indices.append(i)

                if not valid_indices:
                    return  # No valid data to plot

                # Filter to valid data only
                valid_equity = [equity[i] for i in valid_indices]
                valid_balance = [balance[i] for i in valid_indices]

                # Update lines
                self.equity_line.set_data(range(len(valid_equity)), valid_equity)
                self.balance_line.set_data(range(len(valid_balance)), valid_balance)

                # Auto-scale
                self.ax.relim()
                self.ax.autoscale_view()

                # Redraw
                try:
                    self.canvas.draw_idle()
                except:
                    pass  # Canvas may not be ready

            except Exception as e:
                self.log_message(f"Chart update error: {e}", "WARNING")

        def reset_chart(self):
            """Reset chart data"""
            try:
                self.chart_data['timestamps'].clear()
                self.chart_data['equity'].clear()
                self.chart_data['balance'].clear()
                self.log_message("✓ Chart data reset", "INFO")
            except Exception as e: 
                self.log_message(f"Chart reset error: {e}", "ERROR")

        def update_performance_display(self):
            """Update performance metrics display (called every 1 second)"""
            try:
                # Check if active bot is running
                if self.active_bot_id and self.active_bot_id in self.bots:
                    bot = self.bots[self.active_bot_id]
                    
                    if bot['is_running'] and bot['engine']:
                        # ✅ FIX: Get performance snapshot from ACTIVE BOT's engine
                        snapshot = bot['engine'].get_performance_snapshot()
                        
                        if snapshot is None:
                            self.reset_performance_display()
                            return
                        
                        # Safe helper to format numbers (NaN/Inf protection)
                        def safe_format(value, format_str='f', decimals=2, default="N/A", prefix="", suffix=""):
                            """Safely format numbers, handling NaN, Inf, and errors"""
                            try:
                                import math
                                if isinstance(value, str):
                                    return value
                                if value is None:
                                    return default
                                if math.isnan(value) or math.isinf(value):
                                    return default
                                if format_str == 'f':
                                    return f"{prefix}{value:.{decimals}f}{suffix}"
                                else:
                                    return f"{prefix}{value}{suffix}"
                            except:
                                return default
                        
                        # Update trading metrics with NaN protection
                        try:
                            trades = int(snapshot.get('trades_today', 0) or 0)
                            wins = int(snapshot.get('wins', 0) or 0)
                            losses = int(snapshot.get('losses', 0) or 0)
                            win_rate = float(snapshot.get('win_rate', 0) or 0)
                            daily_pnl = float(snapshot.get('daily_pnl', 0) or 0)
                            signals = int(snapshot.get('signals_generated', 0) or 0)
                            position_vol = float(snapshot.get('position_volume', 0) or 0)
                            
                            # ✅ NEW: Get total lot today from risk manager's daily_volume tracker (or DB fallback)
                            daily_volume_total = bot['risk_manager'].get_daily_volume_from_db() if bot['risk_manager'] else 0.0
                            
                            self.perf_vars['trades_today'].set(str(trades))
                            self.perf_vars['wins'].set(str(wins))
                            self.perf_vars['losses'].set(str(losses))
                            self.perf_vars['win_rate'].set(safe_format(win_rate, decimals=1, suffix="%"))
                            self.perf_vars['daily_pnl'].set(safe_format(daily_pnl, decimals=2, prefix="$"))
                            self.perf_vars['signals'].set(str(signals))
                            self.perf_vars['position'].set(str(snapshot.get('current_position', 'None') or 'None'))
                            self.perf_vars['position_vol'].set(safe_format(position_vol, decimals=2))
                            self.perf_vars['total_lot_today'].set(safe_format(daily_volume_total, decimals=2))
                        except Exception as e:
                            self.log_message(f"Error updating trading metrics: {e}", "WARNING")
                        
                        # Update account metrics with NaN protection
                        try:
                            balance = float(snapshot.get('balance', 0) or 0)
                            equity = float(snapshot.get('equity', 0) or 0)
                            floating = float(snapshot.get('floating', 0) or 0)
                            
                            self.perf_vars['balance'].set(safe_format(balance, decimals=2, prefix="$"))
                            self.perf_vars['equity'].set(safe_format(equity, decimals=2, prefix="$"))
                            self.perf_vars['floating'].set(safe_format(floating, decimals=2, prefix="$"))
                        except Exception as e:
                            self.log_message(f"Error updating account metrics: {e}", "WARNING")
                        
                        # Update performance metrics with NaN protection
                        try:
                            latency_avg = float(snapshot.get('tick_latency_avg', 0) or 0)
                            latency_max = float(snapshot.get('tick_latency_max', 0) or 0)
                            exec_avg = float(snapshot.get('exec_time_avg', 0) or 0)
                            exec_max = float(snapshot.get('exec_time_max', 0) or 0)
                            ticks = int(snapshot.get('ticks_processed', 0) or 0)
                            
                            self.perf_vars['latency_avg'].set(safe_format(latency_avg, decimals=1, suffix=" μs"))
                            self.perf_vars['latency_max'].set(safe_format(latency_max, decimals=1, suffix=" μs"))
                            self.perf_vars['exec_avg'].set(safe_format(exec_avg, decimals=2, suffix=" ms"))
                            self.perf_vars['exec_max'].set(safe_format(exec_max, decimals=2, suffix=" ms"))
                            self.perf_vars['ticks'].set(str(ticks))
                        except Exception as e:
                            self.log_message(f"Error updating performance metrics: {e}", "WARNING")
                        
                        # Update chart data with NaN protection
                        try:
                            chart_equity = float(snapshot.get('equity', 0) or 0)
                            chart_balance = float(snapshot.get('balance', 0) or 0)
                            
                            # Only add to chart if valid numbers
                            import math
                            if not math.isnan(chart_equity) and not math.isinf(chart_equity) and not math.isnan(chart_balance) and not math.isinf(chart_balance):
                                self.chart_data['timestamps'].append(datetime.now())
                                self.chart_data['equity'].append(chart_equity)
                                self.chart_data['balance'].append(chart_balance)
                                
                                # Update chart
                                self.update_equity_chart()
                        except Exception as e:
                            self.log_message(f"Error updating chart: {e}", "WARNING")
                    else:
                        # Bot not running - show zeros
                        self.reset_performance_display()
                else:
                    # No active bot
                    self.reset_performance_display()
                
            except Exception as e:
                self.log_message(f"Performance display update failed: {e}", "ERROR")
            
            finally:
                # Schedule next update
                try:
                    self.root.after(1000, self.update_performance_display)
                except:
                    pass  # Root window may have been destroyed

        def reset_performance_display(self):
            """Reset performance display to zeros"""
            try:
                self.perf_vars['trades_today'].set("0")
                self.perf_vars['wins'].set("0")
                self.perf_vars['losses'].set("0")
                self.perf_vars['win_rate'].set("0.0%")
                self.perf_vars['daily_pnl'].set("$0.00")
                self.perf_vars['signals'].set("0")
                self.perf_vars['position'].set("None")
                self.perf_vars['position_vol'].set("0.00")
                self.perf_vars['total_lot_today'].set("0.00")
                self.perf_vars['balance'].set("$0.00")
                self.perf_vars['equity'].set("$0.00")
                self.perf_vars['floating'].set("$0.00")
                self.perf_vars['latency_avg'].set("0.0 μs")
                self.perf_vars['latency_max'].set("0.0 μs")
                self.perf_vars['exec_avg'].set("0.00 ms")
                self.perf_vars['exec_max'].set("0.00 ms")
                self.perf_vars['ticks'].set("0")
            except Exception as e:
                self.log_message(f"Error resetting performance display: {e}", "WARNING")

        def build_log_tab(self):
            """Build logging tab"""
            try:
                self.log_text = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD, height=30,
                                                        bg='#1a1e3a', fg='#e0e0e0', font=("Courier", 9))
                self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                self.log_text.tag_config("INFO", foreground="#00e676")
                self.log_text.tag_config("WARNING", foreground="#ffd600")
                self.log_text.tag_config("ERROR", foreground="#ff1744")
                self.log_text.tag_config("SUCCESS", foreground="#00b0ff")
            except Exception as e:
                print(f"Build log tab error: {e}")

        def browse_mt5_path(self):
            """Browse for MT5 executable"""
            try:
                filename = filedialog.askopenfilename(
                    title="Select MT5 Terminal",
                    filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
                )
                if filename:
                    self.mt5_path_var.set(filename)
                    self.log_message(f"MT5 path set to: {filename}", "SUCCESS")
            except Exception as e: 
                self.log_message(f"Browse error: {e}", "ERROR")

        def load_preset(self, preset_file):
            """Load configuration preset"""
            try:
                if os.path.exists(preset_file):
                    with open(preset_file, 'r') as f:
                        config = json.load(f)
                    self.apply_config(config)
                    self.log_message(f"✓ Loaded preset: {preset_file}", "SUCCESS")
                else:
                    self.log_message(f"Preset file not found: {preset_file}", "WARNING")
            except Exception as e: 
                self.log_message(f"Load preset error: {e}", "ERROR")

        def apply_config(self, config):
            """Apply configuration to GUI fields"""
            try:
                self.symbol_var.set(config.get('symbol', 'GOLD.ls'))
                self.volume_var.set(config.get('volume', '0.01'))
                # ✅ FIX:  MAGIC NUMBER MUST BE LOADED! 
                self.magic_var.set(str(config.get('magic_number', 2026002)))
                self.risk_var.set(config.get('risk_per_trade', '1.0'))
                self.signal_strength_var.set(config.get('min_signal_strength', '0.45'))
                self.max_spread_var.set(config.get('max_spread', '0.12'))
                self.max_volatility_var.set(config.get('max_volatility', '0.005'))
                self.filling_mode_var.set(config.get('filling_mode', 'FOK'))
                self.sl_multiplier_var.set(config.get('sl_multiplier', '50.0'))
                self.risk_reward_var.set(config.get('risk_reward_ratio', '2.0'))
                self.tp_mode_var.set(config.get('tp_mode', 'FixedDollar'))
                self.tp_dollar_var.set(config.get('tp_dollar_amount', '0.8'))
                self.max_floating_loss_var.set(config.get('max_floating_loss', '5'))
                self.max_floating_profit_var.set(config.get('max_floating_profit', '0.5'))
                self.mt5_path_var.set(config.get('mt5_path', 'C:\\Program Files\\MT5\\terminal64.exe'))
                self.enable_ml_var.set(config.get('use_ml', False))
                # ✅ ADD COMMISSION
                self.commission_var.set(config.get('commission_per_trade', '0.9'))
                # Indicators
                self.ema_fast_var.set(config.get('ema_fast_period', '7'))
                self.ema_slow_var.set(config.get('ema_slow_period', '21'))
                self.rsi_period_var.set(config.get('rsi_period', '7'))
                self.rsi_overbought_var.set(config.get('rsi_overbought', '68'))
                self.rsi_oversold_var.set(config.get('rsi_oversold', '32'))
                self.atr_period_var.set(config.get('atr_period', '14'))
                self.momentum_period_var.set(config.get('momentum_period', '5'))
                
                # ✅ FIX: Risk Limits - read from top level (same as get_config_from_gui)
                self.limit_vars['max_daily_loss'].set(str(config.get('max_daily_loss', '40')))
                self.limit_vars['daily_target_profit'].set(str(config.get('daily_target_profit', '0')))
                self.limit_vars['max_daily_trades'].set(str(config.get('max_daily_trades', '1000')))
                self.limit_vars['max_daily_volume'].set(str(config.get('max_daily_volume', '10')))
                self.limit_vars['max_position_size'].set(str(config.get('max_position_size', '2')))
                self.limit_vars['max_positions'].set(str(config.get('max_positions', '20')))
                self.limit_vars['max_drawdown_pct'].set(str(config.get('max_drawdown_pct', '10')))
                
                # Telegram Configuration
                if 'telegram' in config:
                    telegram_config = config['telegram']
                    self.telegram_token_var.set(telegram_config.get('token', ''))
                    chat_ids = telegram_config.get('chat_ids', [])
                    self.telegram_chat_ids_var.set(','.join(str(cid) for cid in chat_ids))
                        
            except Exception as e:
                self.log_message(f"Apply config error: {e}", "ERROR")

        def get_config_from_gui(self):
            """Get configuration from GUI fields"""
            try:  
                config = {
                    'bot_id': self.active_bot_id or 'unknown',
                    'symbol': self.symbol_var.get().strip(),
                    'default_volume': float(self.volume_var.get().strip()),
                    # ✅ FIX: MAGIC NUMBER HARUS ADA DI CONFIG!
                    'magic_number': int(self.magic_var.get().strip()),
                    'risk_per_trade': float(self.risk_var.get().strip()),
                    'min_signal_strength': float(self.signal_strength_var.get().strip()),
                    'max_spread': float(self.max_spread_var.get().strip()),
                    'max_volatility': float(self.max_volatility_var.get().strip()),
                    'filling_mode': self.filling_mode_var.get().strip(),
                    'sl_multiplier': float(self.sl_multiplier_var.get().strip()),
                    'risk_reward_ratio': float(self.risk_reward_var.get().strip()),
                    'tp_mode': self.tp_mode_var.get().strip(),
                    'tp_dollar_amount': float(self.tp_dollar_var.get().strip()),
                    'max_floating_loss': float(self.max_floating_loss_var.get().strip()),
                    'max_floating_profit': float(self.max_floating_profit_var.get().strip()),
                    'mt5_path': self.mt5_path_var.get().strip(),
                    'enable_ml':  self.enable_ml_var.get(),
                    # ✅ ADD COMMISSION
                    'commission_per_trade':  float(self.commission_var.get().strip()),
                    
                    # Trading Sessions
                    'trading_sessions_enabled': self.trading_sessions_enabled.get(),
                    'london_session_enabled': self.london_session_enabled.get(),
                    'london_start': self.london_start_var.get().strip(),
                    'london_end': self.london_end_var.get().strip(),
                    'ny_session_enabled': self.ny_session_enabled.get(),
                    'ny_start': self.ny_start_var.get().strip(),
                    'ny_end': self.ny_end_var.get().strip(),
                    'asia_session_enabled': self.asia_session_enabled.get(),
                    'asia_start': self.asia_start_var.get().strip(),
                    'asia_end': self.asia_end_var.get().strip(),
                    
                    # Indicators
                    'ema_fast_period': int(self.ema_fast_var.get().strip()),
                    'ema_slow_period': int(self.ema_slow_var.get().strip()),
                    'rsi_period': int(self.rsi_period_var.get().strip()),
                    'rsi_overbought': float(self.rsi_overbought_var.get().strip()),
                    'rsi_oversold': float(self.rsi_oversold_var.get().strip()),
                    'atr_period': int(self.atr_period_var.get().strip()),
                    'momentum_period': int(self.momentum_period_var.get().strip()),
                    
                    # Risk Limits
                    'max_daily_loss': float(self.limit_vars['max_daily_loss'].get().strip()),
                    'daily_target_profit': float(self.limit_vars['daily_target_profit'].get().strip()),
                    'max_daily_trades': int(self.limit_vars['max_daily_trades'].get().strip()),
                    'max_daily_volume': float(self.limit_vars['max_daily_volume'].get().strip()),
                    'max_position_size': float(self.limit_vars['max_position_size'].get().strip()),
                    'max_positions': int(self.limit_vars['max_positions'].get().strip()),
                    'max_drawdown_pct': float(self.limit_vars['max_drawdown_pct'].get().strip()),
                    
                    # Telegram Configuration
                    'telegram': {
                        'token': self.telegram_token_var.get().strip(),
                        'chat_ids': [cid.strip() for cid in self.telegram_chat_ids_var.get().split(',') if cid.strip()]
                    }
                }
                return config
            except Exception as e:  
                self.log_message(f"Get config error: {e}", "ERROR")
                return {}

        def save_config(self):
            """Save current active bot's configuration to file"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                # ✅ FIX:  Save current GUI state to active bot FIRST
                self.save_gui_config_to_bot(self.active_bot_id)
                
                # Get active bot's config
                import copy
                config = copy.deepcopy(self.bots[self.active_bot_id]['config'])
                
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title=f"Save {self.active_bot_id} Config"
                )
                if filename:
                    with open(filename, 'w') as f:
                        json.dump(config, f, indent=4)
                    self.log_message(f"✓ {self.active_bot_id} configuration saved to:  {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Save config error: {e}", "ERROR")

        def load_config_dialog(self):
            """Load configuration from file to active bot"""
            try: 
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                filename = filedialog.askopenfilename(
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title=f"Load Config for {self.active_bot_id}"
                )
                if filename:
                    with open(filename, 'r') as f:
                        config = json.load(f)
                    
                    # ✅ FIX: Apply config ONLY to active bot
                    import copy
                    self.bots[self.active_bot_id]['config'] = copy.deepcopy(config)
                    
                    # Load to GUI
                    self.apply_config(config)
                    
                    self.log_message(f"✓ Configuration loaded to {self.active_bot_id} from: {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"Load config error: {e}", "ERROR")

        def start_trading(self):
            """Start trading for active bot"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if bot['is_running']:
                    messagebox.showwarning("Warning", f"{self.active_bot_id} is already running!")
                    return
                
                # Load core modules
                if not self.core_modules_loaded:
                    from aventa_hft_core import UltraLowLatencyEngine
                    from risk_manager import RiskManager
                    from ml_predictor import MLPredictor
                    self.core_modules_loaded = True
                    self.log_message("✓ Core modules loaded", "SUCCESS")
                
                # Save current GUI config to bot
                self.save_gui_config_to_bot(self.active_bot_id)
                
                # Get bot's config
                config = bot['config']
                
                # Create components for this bot
                from risk_manager import RiskManager
                from aventa_hft_core import UltraLowLatencyEngine
                
                bot['risk_manager'] = RiskManager(config)
                
                # Create ML predictor first if enabled
                ml_predictor = None
                enable_ml = config.get('enable_ml', False)
                
                if enable_ml:
                    from ml_predictor import MLPredictor
                    
                    # ✅ FIX: Check if bot already has trained ML predictor
                    if bot.get('ml_predictor') and bot['ml_predictor'].is_trained:
                        # Reuse existing trained predictor
                        ml_predictor = bot['ml_predictor']
                        self.log_message(f"✅ {self.active_bot_id}: ML Predictor ENABLED & TRAINED (Ready to use)", "SUCCESS")
                    else:
                        # Create new predictor (will not have trained models unless loaded)
                        ml_predictor = MLPredictor(config['symbol'], config)
                        bot['ml_predictor'] = ml_predictor
                        
                        # Check if ML model is trained
                        if ml_predictor.is_trained:
                            self.log_message(f"✅ {self.active_bot_id}: ML Predictor ENABLED & TRAINED (Ready to use)", "SUCCESS")
                        else:
                            self.log_message(f"⚠️  {self.active_bot_id}: ML Predictor ENABLED but NOT YET TRAINED!", "WARNING")
                            self.log_message(f"   → All trading signals will be REJECTED until you train the model!", "WARNING")
                            self.log_message(f"   → Go to 'ML Training' tab to train the model first.", "INFO")
                            messagebox.showwarning(
                                "ML Model Not Trained",
                                f"ML Prediction is ENABLED for {self.active_bot_id}, but the model is not trained yet.\n\n"
                                f"⚠️  WARNING: All trading signals will be REJECTED until the model is trained!\n\n"
                                f"Please go to the 'ML Training' tab and train the model first."
                            )
                else:
                    self.log_message(f"{self.active_bot_id}: ML Prediction DISABLED (Technical signals only)", "INFO")
                
                bot['engine'] = UltraLowLatencyEngine(config['symbol'], config, bot['risk_manager'], ml_predictor, 
                                                telegram_callback=lambda **data: self.send_telegram_signal(bot_id=self.active_bot_id, **data))
                
                # Initialize and start
                if bot['engine'].initialize():
                    bot['is_running'] = True
                    bot['engine'].start()
                    
                    # Update GUI references (for active bot only)
                    self.engine = bot['engine']
                    self.risk_manager = bot['risk_manager']
                    
                    # Update button states for THIS bot
                    self.update_button_states()
                    
                    # Update status bar
                    self.status_bar.config(text=f"{self.active_bot_id}:  TRADING ACTIVE", foreground='#00e676')
                    
                    # Update bot status in IPC (for Telegram)
                    additional_info = {
                        'symbol': config['symbol'],
                        'magic_number': config['magic_number'],
                        'volume': config.get('default_volume', 0.01)
                    }
                    self.telegram_integration.update_bot_status(self.active_bot_id, True, additional_info)
                    
                    self.log_message(f"✓ {self.active_bot_id} started successfully!", "SUCCESS")
                    self.log_message(f"  Symbol: {config['symbol']} | Magic: {config['magic_number']}", "INFO")
                else:
                    self.log_message(f"{self.active_bot_id}:  Failed to initialize engine", "ERROR")
                    
            except Exception as e:
                self.log_message(f"Start trading error: {e}", "ERROR")

        def stop_trading(self):
            """Stop trading for active bot"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if not bot['is_running']:  
                    return
                
                bot['is_running'] = False
                
                if bot['engine']: 
                    bot['engine'].stop()
                
                # Update button states
                self.update_button_states()
                
                # Update status bar
                self.status_bar.config(text=f"{self.active_bot_id}:   Stopped", foreground='#ff1744')
                
                # Update bot status in IPC (for Telegram)
                self.telegram_integration.update_bot_status(self.active_bot_id, False)
                
                self.log_message(f"✓ {self.active_bot_id} stopped", "INFO")
                
            except Exception as e:
                self.log_message(f"Stop trading error:   {e}", "ERROR")

        def on_add_bot_disabled(self):
            """Show notification when Add button is clicked (disabled)"""
            messagebox.showinfo("Fitur Tidak Tersedia", "Silahkan hubungi CS kami")

        def on_remove_bot_disabled(self):
            """Show notification when Remove button is clicked (disabled)"""
            messagebox.showinfo("Fitur Tidak Tersedia", "Silahkan hubungi CS kami")

        def add_bot(self, default=False):
            """Add a new bot instance with independent config and unique magic number"""
            try:
                # Generate default name
                bot_id = f"Bot_{len(self.bots) + 1}"
                
                # ✅ CRITICAL FIX: Use DEFAULT config (NOT current GUI config!)
                # New bot should start with default settings, not copy from previous bot
                default_config = self.config_manager.create_isolated_config(
                    base_config=None,  # ← Use DEFAULT_CONFIG, not GUI config!
                    bot_id=bot_id
                )
                
                # ✅ AUTO-INCREMENT MAGIC NUMBER (CRITICAL FIX!)
                # Each bot needs unique magic number
                next_magic = 2026000 + len(self.bots) + 1
                default_config['magic_number'] = next_magic
                
                # Verify isolation
                if not self.config_manager.validate_config(default_config):
                    raise ValueError("Invalid config generated")
                
                self.bots[bot_id] = {
                    'config': default_config,  # Deep copied with default values
                    'engine': None,
                    'risk_manager': None,
                    'ml_predictor': None,
                    'is_running': False,
                    'update_thread': None
                }
                
                self.bot_listbox.insert(tk.END, bot_id)
                
                # Select the new bot
                if default or len(self.bots) == 1:
                    self.bot_listbox.selection_clear(0, tk.END)
                    self.bot_listbox.selection_set(self.bot_listbox.size() - 1)
                    self.active_bot_id = bot_id
                    self.load_bot_config_to_gui(bot_id)
                    self.update_button_states()
                
                self.log_message(f"✓ {bot_id} added successfully (Magic: {next_magic})", "SUCCESS")
                
                # Update Telegram bot selector if Telegram tab is already built
                try:
                    if hasattr(self, 'telegram_bot_selector'):
                        self.update_telegram_bot_selector()
                except:
                    pass
                
            except Exception as e:
                self.log_message(f"Add bot error: {e}", "ERROR")

        def remove_bot(self):
            """Remove selected bot with confirmation"""
            try:
                selection = self.bot_listbox.curselection()
                if not selection:
                    messagebox.showwarning("Warning", "Please select a bot to remove")
                    return
                
                bot_id = self.bot_listbox.get(selection[0])
                
                # Can't remove if only 1 bot
                if len(self.bots) <= 1:
                    messagebox. showwarning("Warning", "Cannot remove the last bot!")
                    return
                
                # Check if bot is running
                if bot_id in self.bots and self.bots[bot_id]['is_running']:
                    messagebox.showwarning(
                        "Warning", 
                        f"{bot_id} is currently running!\n\n"
                        "Please stop the bot before removing it."
                    )
                    return
                
                # ✅ NEW: Confirmation dialog with detailed info
                bot = self.bots[bot_id]
                config = bot['config']
                
                confirm_message = f"""Are you sure you want to remove {bot_id}? 

        Bot Configuration:
        • Symbol: {config. get('symbol', 'N/A')}
        • Magic Number: {config.get('magic_number', 'N/A')}
        • Volume: {config.get('default_volume', 'N/A')}

        ⚠️ WARNING: 
        • Bot configuration will be lost
        • This action cannot be undone
        • Any open positions will remain active in MT5

        Continue with removal?"""
                
                response = messagebox.askyesno(
                    "Confirm Remove Bot",
                    confirm_message,
                    icon='warning'
                )
                
                if not response:
                    self.log_message(f"❌ Remove {bot_id} cancelled by user", "INFO")
                    return
                
                # ✅ Check for open positions (optional warning)
                magic = config.get('magic_number')
                symbol = config.get('symbol')
                
                try:
                    positions = mt5.positions_get(symbol=symbol)
                    if positions:
                        our_positions = [p for p in positions if p.magic == magic]
                        
                        if len(our_positions) > 0:
                            position_warning = f"""⚠️ OPEN POSITIONS DETECTED! 

        {bot_id} has {len(our_positions)} open position(s):
        """
                            total_profit = 0.0
                            for pos in our_positions:
                                pos_type = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
                                position_warning += f"\n• {pos_type} {pos.volume} @ {pos.price_open:.5f} | P&L: ${pos. profit:.2f}"
                                total_profit += pos.profit
                            
                            position_warning += f"\n\nTotal Floating P&L: ${total_profit:.2f}"
                            position_warning += "\n\n⚠️ These positions will remain active after bot removal."
                            position_warning += "\n\nDo you want to:"
                            position_warning += "\n• YES = Remove bot (positions remain open)"
                            position_warning += "\n• NO = Cancel removal"
                            
                            final_confirm = messagebox.askyesno(
                                "Open Positions Warning",
                                position_warning,
                                icon='warning'
                            )
                            
                            if not final_confirm:
                                self.log_message(f"❌ Remove {bot_id} cancelled (has open positions)", "WARNING")
                                return
                except Exception as e:
                    self.log_message(f"⚠️ Could not check positions: {e}", "WARNING")
                
                # ✅ Proceed with removal
                # Remove from dict
                if bot_id in self.bots:
                    del self.bots[bot_id]
                
                # Remove from listbox
                self.bot_listbox.delete(selection[0])
                
                # Select first bot
                if len(self.bots) > 0:
                    self.bot_listbox.selection_set(0)
                    first_bot_id = self.bot_listbox.get(0)
                    self.active_bot_id = first_bot_id
                    self.load_bot_config_to_gui(first_bot_id)
                
                # Save session after removal
                self.save_session()
                
                self.log_message(f"✓ {bot_id} removed successfully", "SUCCESS")
                
                # Update Telegram bot selector if Telegram tab is already built
                try:
                    if hasattr(self, 'telegram_bot_selector'):
                        self.update_telegram_bot_selector()
                except:
                    pass
                
            except Exception as e:
                self.log_message(f"Remove bot error: {e}", "ERROR")
                messagebox.showerror("Error", f"Failed to remove bot:\n{e}")

        def rename_bot(self):
            """Rename selected bot"""
            try:
                selection = self.bot_listbox.curselection()
                if not selection:
                    messagebox.showwarning("Warning", "Please select a bot to rename")
                    return
                
                old_bot_id = self.bot_listbox.get(selection[0])
                
                # Ask for new name
                from tkinter import simpledialog
                new_name = simpledialog.askstring(
                    "Rename Bot",
                    f"Enter new name for {old_bot_id}:",
                    initialvalue=old_bot_id
                )
                
                if new_name and new_name.strip():
                    new_name = new_name.strip()
                    
                    # Check if name already exists
                    if new_name in self.bots and new_name != old_bot_id:
                        messagebox.showerror("Error", f"Bot named '{new_name}' already exists!")
                        return
                    
                    # Check if bot is running (can't rename running bot)
                    if self.bots[old_bot_id]['is_running']:
                        messagebox.showwarning("Warning", f"Cannot rename running bot!  Stop {old_bot_id} first.")
                        return
                    
                    # Rename bot in dictionary
                    self.bots[new_name] = self.bots.pop(old_bot_id)

                    # Update active_bot_id if this was active
                    if self.active_bot_id == old_bot_id:
                        self.active_bot_id = new_name

                    # Update listbox
                    self.bot_listbox.delete(selection[0])
                    self.bot_listbox.insert(selection[0], new_name)
                    self.bot_listbox.selection_set(selection[0])

                    # Save session immediately after rename
                    self.save_session()

                    self.log_message(f"✓ Bot renamed:  {old_bot_id} → {new_name}", "SUCCESS")

            except Exception as e:
                self.log_message(f"Rename bot error: {e}", "ERROR")
                
        def get_default_config(self):
            """Get default configuration for new bot"""
            return {
                'symbol': 'GOLD.ls',
                'default_volume': 0.01,
                'magic_number': 2026002 + len(self.bots),
                'risk_per_trade': 1.0,
                'min_signal_strength': 0.45,
                'max_spread': 0.12,
                'max_volatility': 0.005,
                'filling_mode': 'FOK',
                'sl_multiplier': 50.0,
                'risk_reward_ratio': 2.0,
                'tp_mode': 'FixedDollar',
                'tp_dollar_amount': 0.8,
                'max_floating_loss': 5.0,
                'max_floating_profit': 0.5,
                'mt5_path':  'C:\\Program Files\\MT5\\terminal64.exe',
                'enable_ml': False,
                # ✅ ADD COMMISSION
                'commission_per_trade': 0.9,  # Default $0.90 per trade
                # Indicators
                'ema_fast_period': 7,
                'ema_slow_period': 21,
                'rsi_period': 7,
                'rsi_overbought': 68,
                'rsi_oversold': 32,
                'atr_period':  14,
                'momentum_period': 5,
                
                # Risk Limits
                'max_daily_loss': 40.0,
                'max_daily_trades': 1000,
                'max_daily_volume': 10.0,
                'max_position_size':  2.0,
                'max_positions': 20,
                'max_drawdown_pct': 10.0
            }

        def save_gui_config_to_bot(self, bot_id):
            """Save current GUI config to specific bot"""
            try:
                if bot_id not in self.bots:
                    return
                
                # ✅ FIX: Get FRESH config from GUI (don't reuse references)
                import copy
                config = copy.deepcopy(self.get_config_from_gui())
                
                # Save to bot's config
                self.bots[bot_id]['config'] = config
                
                # Update telegram bot if telegram config exists
                self.update_telegram_bot_for_config(bot_id, config)
                
                # If bot is running, update its risk_manager live
                if self.bots[bot_id]['is_running'] and self.bots[bot_id]['risk_manager']:
                    rm = self.bots[bot_id]['risk_manager']
                    rm.max_daily_loss = config['max_daily_loss']
                    rm.max_daily_trades = config['max_daily_trades']
                    rm.max_daily_volume = config['max_daily_volume']
                    rm.max_position_size = config['max_position_size']
                    rm.max_positions = config['max_positions']
                    rm.max_drawdown_pct = config['max_drawdown_pct']
                    
                    self.log_message(f"✓ {bot_id} config updated (running bot)", "SUCCESS")
                else:
                    self.log_message(f"✓ {bot_id} config saved", "SUCCESS")
                
            except Exception as e: 
                self.log_message(f"Save GUI config error: {e}", "ERROR")

        def update_telegram_bot_for_config(self, bot_id, config):
            """Update telegram bot for a bot's config"""
            try:
                if 'telegram' in config:
                    telegram_config = config['telegram']
                    token = telegram_config.get('token', '').strip()
                    chat_ids = [str(cid).strip() for cid in telegram_config.get('chat_ids', []) if str(cid).strip()]
                    
                    if token and chat_ids:
                        # Import TelegramBot if not already imported
                        try:
                            from telegram_bot import TelegramBot
                        except ImportError:
                            self.log_message("TelegramBot module not found", "WARNING")
                            return
                            
                        self.telegram_bots[bot_id] = TelegramBot(token, chat_ids)
                        self.log_message(f"✓ Telegram bot updated for {bot_id}", "INFO")
                    else:
                        # Remove telegram bot if config is incomplete
                        if bot_id in self.telegram_bots:
                            del self.telegram_bots[bot_id]
                            self.log_message(f"✓ Telegram bot removed for {bot_id} (incomplete config)", "INFO")
                else:
                    # Remove telegram bot if no telegram config
                    if bot_id in self.telegram_bots:
                        del self.telegram_bots[bot_id]
                        self.log_message(f"✓ Telegram bot removed for {bot_id} (no config)", "INFO")
                        
            except Exception as e:
                self.log_message(f"Update telegram bot error for {bot_id}: {e}", "ERROR")

        def load_bot_config_to_gui(self, bot_id):
            """Load specific bot's config to GUI (COMPLETE VERSION)"""
            try:
                if bot_id not in self.bots:
                    return
                
                # ✅ FIX: Create a copy to prevent GUI changes affecting bot config
                import copy
                config = copy.deepcopy(self.bots[bot_id]['config'])
                
                # === TRADING CONFIGURATION ===
                self.symbol_var.set(config.get('symbol', 'GOLD.ls'))
                self.volume_var.set(str(config.get('default_volume', 0.01)))
                self.magic_var.set(str(config.get('magic_number', 2026002)))
                self.risk_var.set(str(config.get('risk_per_trade', 1.0)))
                self.signal_strength_var.set(str(config.get('min_signal_strength', 0.45)))
                self.max_spread_var.set(str(config.get('max_spread', 0.12)))
                self.max_volatility_var.set(str(config.get('max_volatility', 0.005)))
                self.filling_mode_var.set(config.get('filling_mode', 'FOK'))
                self.sl_multiplier_var.set(str(config.get('sl_multiplier', 50.0)))
                self.risk_reward_var.set(str(config.get('risk_reward_ratio', 2.0)))
                self.tp_mode_var.set(config.get('tp_mode', 'FixedDollar'))
                self.tp_dollar_var.set(str(config.get('tp_dollar_amount', 0.8)))
                self.max_floating_loss_var.set(str(config.get('max_floating_loss', 5.0)))
                self.max_floating_profit_var.set(str(config.get('max_floating_profit', 0.5)))
                
                # ✅ FIX: MT5 PATH - INI YANG PALING PENTING!
                self.mt5_path_var.set(config.get('mt5_path', 'C:\\Program Files\\MT5\\terminal64.exe'))
                
                self.enable_ml_var.set(config.get('enable_ml', False))
                self.commission_var.set(str(config.get('commission_per_trade', 0.9)))
                
                # === TRADING SESSIONS ===
                self.trading_sessions_enabled.set(config.get('trading_sessions_enabled', True))
                self.london_session_enabled.set(config.get('london_session_enabled', True))
                self.london_start_var.set(config.get('london_start', '08:00'))
                self.london_end_var.set(config.get('london_end', '16:30'))
                self.ny_session_enabled.set(config.get('ny_session_enabled', True))
                self.ny_start_var.set(config.get('ny_start', '13:00'))
                self.ny_end_var.set(config.get('ny_end', '21:00'))
                self.asia_session_enabled.set(config.get('asia_session_enabled', False))
                self.asia_start_var.set(config.get('asia_start', '22:00'))
                self.asia_end_var.set(config.get('asia_end', '08:00'))
                
                # === INDICATORS ===
                self.ema_fast_var.set(str(config.get('ema_fast_period', 7)))
                self.ema_slow_var.set(str(config.get('ema_slow_period', 21)))
                self.rsi_period_var.set(str(config.get('rsi_period', 7)))
                self.rsi_overbought_var.set(str(config.get('rsi_overbought', 68)))
                self.rsi_oversold_var.set(str(config.get('rsi_oversold', 32)))
                self.atr_period_var.set(str(config.get('atr_period', 14)))
                self.momentum_period_var.set(str(config.get('momentum_period', 5)))
                
                # === RISK LIMITS ===
                self.limit_vars['max_daily_loss'].set(str(config.get('max_daily_loss', 40.0)))
                self.limit_vars['max_daily_trades'].set(str(config.get('max_daily_trades', 1000)))
                self.limit_vars['max_daily_volume'].set(str(config.get('max_daily_volume', 10.0)))
                self.limit_vars['max_position_size'].set(str(config.get('max_position_size', 2.0)))
                self.limit_vars['max_positions'].set(str(config.get('max_positions', 20)))
                self.limit_vars['max_drawdown_pct'].set(str(config.get('max_drawdown_pct', 10.0)))
                
                self.log_message(f"✓ Loaded {bot_id} config to GUI (all {len(config)} fields)", "INFO")
                
            except Exception as e:
                self.log_message(f"Load bot config error: {e}", "ERROR")
                import traceback
                traceback.print_exc()

        def on_bot_selected(self, event):
            """Handle bot selection - load selected bot's config and update buttons"""
            try:
                selection = self.bot_listbox.curselection()
                if not selection:
                    return
                
                bot_id = self.bot_listbox.get(selection[0])
                
                # ✅ FIX: Save current bot's GUI config BEFORE switching
                if self.active_bot_id and self.active_bot_id in self.bots:
                    self.save_gui_config_to_bot(self.active_bot_id)
                    self.log_message(f"✓ Saved {self.active_bot_id} config before switch", "INFO")
                
                # Switch to new bot
                self.active_bot_id = bot_id
                
                # Load new bot's config to GUI
                self.load_bot_config_to_gui(bot_id)
                
                # ✅ FIX: Force selection to stay visible
                self.bot_listbox.selection_set(selection[0])
                self.bot_listbox.activate(selection[0])
                self.bot_listbox.see(selection[0])
                
                # Update button states
                self.update_button_states()
                
                # Update active bot label in Performance Tab
                if hasattr(self, 'active_bot_label'):
                    self.active_bot_label.config(text=bot_id)

                    # ✅ Update Control Panel indicator
                if hasattr(self, 'active_bot_indicator'):
                    self.active_bot_indicator.config(text=bot_id)
                
                # ✅ FIX: Update status bar with colored indicator
                bot = self.bots[bot_id]
                if bot['is_running']:
                    status_text = f"🟢 {bot_id}:  TRADING ACTIVE"
                    status_color = '#00e676'
                else: 
                    status_text = f"🔵 {bot_id}: Ready"
                    status_color = '#00b0ff'

                self.status_bar.config(text=status_text, foreground=status_color)

                # ✅ ADD: Update ML tab indicator
                if hasattr(self, 'ml_active_bot_label'):
                    self.ml_active_bot_label.config(text=bot_id)

                # ✅ ADD: Update ML status display
                self.update_ml_status_display()
                
                # ✅ NEW: Log ML status when switching bots
                config = bot['config']
                enable_ml = config.get('enable_ml', False)
                ml_predictor = bot.get('ml_predictor')
                
                if enable_ml:
                    if ml_predictor and ml_predictor.is_trained:
                        self.log_message(f"✅ {bot_id}: ML Prediction ENABLED & TRAINED (Ready to assist decisions)", "SUCCESS")
                    else:
                        self.log_message(f"⚠️  {bot_id}: ML Prediction ENABLED but NOT YET TRAINED", "WARNING")
                        self.log_message(f"   Go to 'ML Training' tab to train the model", "INFO")
                else:
                    self.log_message(f"🔵 {bot_id}: ML Prediction DISABLED (Technical signals only)", "INFO")

                self.log_message(f"✓ Switched to {bot_id}", "INFO")
                
            except Exception as e:
                self.log_message(f"Bot selection error: {e}", "ERROR")

        def update_button_states(self):
            """Update START/STOP button states based on active bot's status"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if bot['is_running']:
                    # Bot is running - disable START, enable STOP
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                else:
                    # Bot is stopped - enable START, disable STOP
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    
            except Exception as e: 
                self.log_message(f"Update button states error: {e}", "ERROR")

        def on_language_changed(self, event=None):
            try:
                self.log_message("Language changed", "INFO")
            except Exception as e:
                self.log_message(f"Language change error: {e}", "ERROR")

        def async_init(self):
            """Initialize asynchronously"""
            def init_thread():
                try:
                    # ✅ CRITICAL FIX: Load session directly in thread, don't schedule to event loop yet
                    session_loaded = self.load_session()
                    
                    # If no session was loaded, create default bot
                    if not session_loaded:
                        self.root.after(0, lambda: self.add_bot(default=True))
                        # Auto-load default config if exists
                        if os.path.exists("config_GOLD.ls.json"):
                            with open("config_GOLD.ls.json", 'r') as f:
                                config = json.load(f)
                            self.root.after(0, lambda: self.apply_config(config))
                            self.root.after(0, lambda: self.log_message("✓ Auto-loaded GOLD config", "SUCCESS"))

                    self.root.after(0, lambda: self.log_message("System ready. Configure and click START TRADING.", "INFO"))
                except Exception as e:
                    self.root.after(0, lambda: self.log_message(f"Init warning: {str(e)}", "WARNING"))

            threading.Thread(target=init_thread, daemon=True).start()

        def log_message(self, message, level="INFO"):
            """Add log message"""
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] [{level}] {message}\n"
                if hasattr(self, 'log_text'):
                    self.log_text.insert(tk.END, log_entry, level)
                    self.log_text.see(tk.END)
            except Exception as e:
                print(f"Logging error: {e}")


        def build_risk_tab(self):
            """Build comprehensive risk management tab"""
            try:
                # Main container
                main_container = ttk.Frame(self.risk_tab)
                main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # === RISK LIMITS CONFIGURATION ===
                limits_frame = ttk.LabelFrame(main_container, text="🛡️ Risk Limits Configuration", padding=10)
                limits_frame.pack(fill=tk.X, pady=(0, 10))

                # Row 1: Max Daily Loss, Max Daily Trades
                limits_row1 = ttk.Frame(limits_frame)
                limits_row1.pack(fill=tk.X, pady=2)
                
                ttk.Label(limits_row1, text="Max Daily Loss ($):", width=25).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row1, textvariable=self.limit_vars['max_daily_loss'], width=15).pack(side=tk.LEFT, padx=5)
                
                # ✅ NEW: Daily Target Profit
                ttk.Label(limits_row1, text="Daily Target Profit ($):", width=25).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row1, textvariable=self.limit_vars['daily_target_profit'], width=15).pack(side=tk.LEFT, padx=5)
                
                # Row 1b: Max Daily Trades, Max Daily Volume
                limits_row1b = ttk.Frame(limits_frame)
                limits_row1b.pack(fill=tk.X, pady=2)
                
                ttk.Label(limits_row1b, text="Max Daily Trades:", width=25).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row1b, textvariable=self.limit_vars['max_daily_trades'], width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(limits_row1b, text="Max Daily Volume:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row1b, textvariable=self.limit_vars['max_daily_volume'], width=15).pack(side=tk.LEFT, padx=5)

                # Row 2: Max Position Size, Max Positions
                limits_row2 = ttk.Frame(limits_frame)
                limits_row2.pack(fill=tk.X, pady=2)
                
                ttk.Label(limits_row2, text="Max Position Size (lots):", width=25).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row2, textvariable=self.limit_vars['max_position_size'], width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(limits_row2, text="Max Open Positions:", width=20).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row2, textvariable=self.limit_vars['max_positions'], width=15).pack(side=tk.LEFT, padx=5)

                # Row 3: Max Drawdown
                limits_row3 = ttk.Frame(limits_frame)
                limits_row3.pack(fill=tk.X, pady=2)
                
                ttk.Label(limits_row3, text="Max Drawdown (%):", width=25).pack(side=tk.LEFT, padx=5)
                ttk.Entry(limits_row3, textvariable=self.limit_vars['max_drawdown_pct'], width=15).pack(side=tk.LEFT, padx=5)

                # Update button
                update_btn_frame = ttk.Frame(limits_frame)
                update_btn_frame.pack(fill=tk.X, pady=(10, 0))
                ttk.Button(update_btn_frame, text="🔄 Update & Refresh Status", command=self.update_risk_limits, width=25).pack(side=tk.LEFT, padx=5)

                # === REAL-TIME RISK METRICS ===
                metrics_frame = ttk.LabelFrame(main_container, text="📊 Real-Time Risk Metrics", padding=10)
                metrics_frame.pack(fill=tk.X, pady=(0, 10))

                # Initialize risk metric variables
                if not hasattr(self, 'risk_vars'):
                    self.risk_vars = {
                        'current_exposure': tk.StringVar(value="$0.00"),
                        'position_count': tk.StringVar(value="0"),
                        'daily_pnl': tk.StringVar(value="$0.00"),
                        'daily_pnl_pct': tk.StringVar(value="0.0%"),
                        'daily_trades': tk.StringVar(value="0"),
                        'trades_pct': tk.StringVar(value="0.0%"),
                        'drawdown':  tk.StringVar(value="0.0%"),
                        'max_drawdown_today': tk.StringVar(value="0.0%"),  # ✅ NEW: Max drawdown today
                        'risk_level': tk.StringVar(value="LOW"),
                    }

                # Metrics display
                metrics_grid = ttk.Frame(metrics_frame)
                metrics_grid.pack(fill=tk.X, pady=5)

                # Row 1
                row1 = ttk.Frame(metrics_grid)
                row1.pack(fill=tk.X, pady=2)
                self.create_risk_metric(row1, "Current Exposure:", self.risk_vars['current_exposure'], width=15)
                self.create_risk_metric(row1, "Open Positions:", self.risk_vars['position_count'], width=10)

                # Row 2
                row2 = ttk.Frame(metrics_grid)
                row2.pack(fill=tk.X, pady=2)
                self.create_risk_metric(row2, "Daily P&L:", self.risk_vars['daily_pnl'], width=15)
                self.create_risk_metric(row2, "of Limit:", self.risk_vars['daily_pnl_pct'], width=10)

                # Row 3
                row3 = ttk.Frame(metrics_grid)
                row3.pack(fill=tk.X, pady=2)
                self.create_risk_metric(row3, "Daily Trades:", self.risk_vars['daily_trades'], width=15)
                self.create_risk_metric(row3, "of Limit:", self.risk_vars['trades_pct'], width=10)

                # Row 4
                row4 = ttk.Frame(metrics_grid)
                row4.pack(fill=tk.X, pady=2)
                self.create_risk_metric(row4, "Current Drawdown:", self.risk_vars['drawdown'], width=15)
                self.create_risk_metric(row4, "Risk Level:", self.risk_vars['risk_level'], width=10)

                # Row 5 - ✅ NEW: Max drawdown today
                row5 = ttk.Frame(metrics_grid)
                row5.pack(fill=tk.X, pady=2)
                self.create_risk_metric(row5, "Max DD Today:", self.risk_vars['max_drawdown_today'], width=15)

                # === CIRCUIT BREAKER STATUS ===
                cb_frame = ttk.LabelFrame(main_container, text="🚨 Circuit Breaker Status", padding=10)
                cb_frame.pack(fill=tk.X, pady=(0, 10))

                self.circuit_breaker_status = tk.StringVar(value="✅ INACTIVE - Trading Allowed")
                self.circuit_breaker_reason = tk.StringVar(value="No breaches detected")

                status_frame = ttk.Frame(cb_frame)
                status_frame.pack(fill=tk.X, pady=5)

                ttk.Label(status_frame, text="Status:", font=('Segoe UI', 10, 'bold')).pack(side=tk.LEFT, padx=5)
                ttk.Label(status_frame, textvariable=self.circuit_breaker_status, font=('Segoe UI', 10, 'bold'), 
                        foreground='#00e676').pack(side=tk.LEFT, padx=5)

                reason_frame = ttk.Frame(cb_frame)
                reason_frame.pack(fill=tk.X, pady=5)

                ttk.Label(reason_frame, text="Reason:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
                ttk.Label(reason_frame, textvariable=self.circuit_breaker_reason, font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)

                # Manual controls
                control_frame = ttk.Frame(cb_frame)
                control_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Button(control_frame, text="🔓 Reset Circuit Breaker", command=self.reset_circuit_breaker, width=25).pack(side=tk.LEFT, padx=5)
                ttk.Button(control_frame, text="🚫 Manual Trigger", command=self.manual_trigger_cb, width=20).pack(side=tk.LEFT, padx=5)

                # === RISK EVENTS LOG ===
                events_frame = ttk.LabelFrame(main_container, text="📋 Risk Events & Alerts", padding=10)
                events_frame.pack(fill=tk.BOTH, expand=True)

                self.risk_events_text = scrolledtext.ScrolledText(events_frame, wrap=tk.WORD, height=15,
                                                                bg='#1a1e3a', fg='#e0e0e0', font=("Courier", 9))
                self.risk_events_text.pack(fill=tk.BOTH, expand=True, pady=5)

                self.risk_events_text.tag_config("WARNING", foreground="#ffd600")
                self.risk_events_text.tag_config("CRITICAL", foreground="#ff1744")
                self.risk_events_text.tag_config("INFO", foreground="#00e676")

                # Clear button
                ttk.Button(events_frame, text="🗑️ Clear Events", command=self.clear_risk_events, width=15).pack(pady=(5, 0))

                # Start risk monitoring updates
                self.root.after(1000, self.update_risk_metrics)

            except Exception as e:
                self.log_message(f"Build risk tab error: {e}", "ERROR")

        def create_risk_metric(self, parent, label_text, variable, width=15):
            """Create a risk metric display widget"""
            container = ttk.Frame(parent)
            container.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(container, text=label_text, font=('Segoe UI', 9)).pack(side=tk.LEFT)
            ttk.Label(container, textvariable=variable, style='Metric.TLabel', width=width).pack(side=tk.LEFT, padx=(5, 0))

        def update_risk_limits(self):
            """Update risk limits for active bot"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                bot = self.bots[self.active_bot_id]
                
                # Update bot's config
                bot['config']['max_daily_loss'] = float(self.limit_vars['max_daily_loss'].get())
                bot['config']['daily_target_profit'] = float(self.limit_vars['daily_target_profit'].get())
                bot['config']['max_daily_trades'] = int(self.limit_vars['max_daily_trades'].get())
                bot['config']['max_daily_volume'] = float(self.limit_vars['max_daily_volume'].get())
                bot['config']['max_position_size'] = float(self.limit_vars['max_position_size'].get())
                bot['config']['max_positions'] = int(self.limit_vars['max_positions'].get())
                bot['config']['max_drawdown_pct'] = float(self.limit_vars['max_drawdown_pct'].get())
                
                # If bot is running, update risk_manager live
                if bot['risk_manager']:
                    bot['risk_manager'].max_daily_loss = bot['config']['max_daily_loss']
                    bot['risk_manager'].set_daily_target_profit(bot['config']['daily_target_profit'])
                    bot['risk_manager'].max_daily_trades = bot['config']['max_daily_trades']
                    bot['risk_manager'].max_daily_volume = bot['config']['max_daily_volume']
                    bot['risk_manager'].max_position_size = bot['config']['max_position_size']
                    bot['risk_manager'].max_positions = bot['config']['max_positions']
                    bot['risk_manager'].max_drawdown_pct = bot['config']['max_drawdown_pct']
                    
                    self.log_message(f"✓ {self.active_bot_id} risk limits updated", "SUCCESS")
                    self.add_risk_event(f"{self.active_bot_id} risk limits updated", "INFO")
                else:
                    self.log_message(f"✓ {self.active_bot_id} risk limits saved to config", "SUCCESS")
                    
            except Exception as e:
                self.log_message(f"Update risk limits error: {e}", "ERROR")

        def update_risk_metrics(self):
            """Update risk metrics display (called every 1 second)"""
            try:
                # Check if active bot is running
                if self.active_bot_id and self.active_bot_id in self.bots:
                    bot = self.bots[self.active_bot_id]
                    
                    if bot['is_running'] and bot['risk_manager'] and bot['engine']:
                        # Get account info
                        account = mt5.account_info()
                        if account:
                            balance = account.balance
                            equity = account.equity
                        else:
                            balance = 0
                            equity = 0

                        # Get MT5 positions for this bot's magic number
                        magic = bot['risk_manager'].config.get('magic_number', 2026002)
                        positions = mt5.positions_get(symbol=bot['engine'].symbol)
                        bot_positions = []
                        if positions:
                            bot_positions = [p for p in positions if p.magic == magic]

                        # ✅ FIX: Get daily_trades and daily_pnl from ENGINE instead of risk_manager
                        # The engine tracks actual trades executed, risk_manager only tracks recorded trades
                        engine_snapshot = bot['engine'].get_performance_snapshot()
                        daily_trades_actual = engine_snapshot.get('trades_today', 0)
                        daily_pnl_actual = engine_snapshot.get('daily_pnl', 0.0)
                        
                        # Get risk metrics from active bot's risk manager (now with position data)
                        try:
                            # ✅ Also sync risk_manager's counters with engine's actual data
                            bot['risk_manager'].daily_trades = daily_trades_actual
                            bot['risk_manager'].daily_pnl = daily_pnl_actual
                            
                            metrics = bot['risk_manager'].get_risk_metrics(balance, bot_positions)
                            
                            # Update displays with safe access
                            self.risk_vars['current_exposure'].set(f"${metrics.current_exposure:.2f}")
                            self.risk_vars['position_count'].set(str(metrics.position_count))
                            
                            # ✅ USE ACTUAL VALUES FROM ENGINE
                            self.risk_vars['daily_pnl'].set(f"${daily_pnl_actual:.2f}")
                            self.risk_vars['daily_trades'].set(str(daily_trades_actual))
                            
                            # Calculate percentages safely
                            max_daily_loss = bot['risk_manager'].max_daily_loss
                            max_daily_trades = bot['risk_manager'].max_daily_trades
                            
                            pnl_pct = (abs(daily_pnl_actual) / max_daily_loss * 100) if max_daily_loss > 0 else 0
                            self.risk_vars['daily_pnl_pct'].set(f"{pnl_pct:.1f}%")
                            
                            trades_pct = (daily_trades_actual / max_daily_trades * 100) if max_daily_trades > 0 else 0
                            self.risk_vars['trades_pct'].set(f"{trades_pct:.1f}%")

                            self.risk_vars['drawdown'].set(f"{metrics.max_drawdown:.2f}%")
                            self.risk_vars['max_drawdown_today'].set(f"{metrics.max_drawdown_today:.2f}%")  # ✅ NEW: Display max drawdown today
                            self.risk_vars['risk_level'].set(metrics.risk_level)

                            # Update circuit breaker status
                            if bot['risk_manager'].circuit_breaker_triggered:
                                reason = bot['risk_manager'].last_circuit_reason or "Unknown"
                                self.circuit_breaker_status.set(f"❌ TRIGGERED - {reason}")
                                self.circuit_breaker_reason.set(reason)
                            else:
                                self.circuit_breaker_status.set("✅ INACTIVE - Trading Allowed")
                                self.circuit_breaker_reason.set("No breaches detected")

                            # Log critical events
                            if metrics.risk_level == 'CRITICAL' and not bot['risk_manager'].circuit_breaker_triggered:
                                self.add_risk_event(f"⚠️ {self.active_bot_id} CRITICAL RISK - P&L: ${daily_pnl_actual:.2f}", "CRITICAL")
                        
                        except Exception as e:
                            self.log_message(f"Error getting risk metrics: {e}", "ERROR")
                            self.reset_risk_display()
                    else:
                        # Bot not running - reset displays
                        self.reset_risk_display()
                else:
                    # No active bot
                    self.reset_risk_display()

            except Exception as e:
                self.log_message(f"Error updating risk metrics: {e}", "ERROR")
            
            finally:
                try:
                    self.root.after(1000, self.update_risk_metrics)
                except:
                    pass  # Root window may have been destroyed

        def add_risk_event(self, message, level="INFO"):
            """Add risk event to log"""
            try: 
                if hasattr(self, 'risk_events_text'):
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



                    event_entry = f"[{timestamp}] [{level}] {message}\n"
                    self.risk_events_text.insert(tk.END, event_entry, level)
                    self.risk_events_text.see(tk.END)
            except Exception as e:
                pass

        def clear_risk_events(self):
            """Clear risk events log"""
            try:
                if hasattr(self, 'risk_events_text'):
                    self.risk_events_text.delete(1.0, tk.END)
            except Exception as e:
                pass

        def reset_circuit_breaker(self):
            """Reset circuit breaker for active bot"""
            try: 
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if bot['risk_manager']:
                    bot['risk_manager'].circuit_breaker_triggered = False
                    bot['risk_manager'].trading_enabled = True
                    self.log_message(f"✓ {self.active_bot_id} circuit breaker reset", "SUCCESS")
                    self.add_risk_event(f"{self.active_bot_id} circuit breaker reset by user", "INFO")
                else:
                    messagebox.showwarning("Warning", f"{self.active_bot_id} risk manager not initialized")
                    
            except Exception as e:
                self.log_message(f"Reset circuit breaker error: {e}", "ERROR")

        def manual_trigger_cb(self):
            """Manually trigger circuit breaker for active bot"""
            try: 
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if bot['risk_manager']:
                    bot['risk_manager'].trigger_circuit_breaker(f"Manual trigger by user for {self.active_bot_id}")
                    self.log_message(f"🚨 {self.active_bot_id} circuit breaker triggered manually", "WARNING")
                    self.add_risk_event(f"{self.active_bot_id} circuit breaker triggered manually", "CRITICAL")
                else:
                    messagebox.showwarning("Warning", f"{self.active_bot_id} risk manager not initialized")
                    
            except Exception as e:
                self.log_message(f"Manual trigger error: {e}", "ERROR")


        def build_strategy_tab(self):
            """Build comprehensive Strategy Tester tab"""
            try:  
                # Create Canvas with scrollbar for entire tab
                canvas = tk.Canvas(self.strategy_tab, bg='#1a1e3a', highlightthickness=0)
                scrollbar = ttk.Scrollbar(self.strategy_tab, orient=tk.VERTICAL, command=canvas.yview, style='Red.Vertical.TScrollbar')
                
                canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                canvas.configure(yscrollcommand=scrollbar.set)
                
                # Main container inside canvas
                main_container = ttk.Frame(canvas)
                canvas_window = canvas.create_window((0, 0), window=main_container, anchor='nw')
                
                # Update scroll region when frame changes
                def on_frame_configure(event=None):
                    canvas.configure(scrollregion=canvas.bbox('all'))
                    # Make canvas window width match canvas width
                    canvas.itemconfig(canvas_window, width=canvas.winfo_width())
                
                main_container.bind('<Configure>', on_frame_configure)
                canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
                
                # Enable mousewheel scrolling
                def on_mousewheel(event):
                    canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
                canvas.bind_all('<MouseWheel>', on_mousewheel)

                # === BACKTEST CONFIGURATION ===
                config_frame = ttk.LabelFrame(main_container, text="⚙️ Backtest Configuration", padding=10)
                config_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

                # Row 1: Date Range
                date_row = ttk.Frame(config_frame)
                date_row.pack(fill=tk.X, pady=5)
                
                ttk.Label(date_row, text="Start Date (YYYY-MM-DD):", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
                self.bt_start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
                ttk.Entry(date_row, textvariable=self.bt_start_date_var, width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Label(date_row, text="End Date (YYYY-MM-DD):", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
                self.bt_end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
                ttk.Entry(date_row, textvariable=self.bt_end_date_var, width=15).pack(side=tk.LEFT, padx=5)

                # Row 2: Symbol & Initial Balance
                settings_row = ttk.Frame(config_frame)
                settings_row.pack(fill=tk.X, pady=5)

                ttk.Label(settings_row, text="Symbol:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
                self.bt_symbol_var = tk.StringVar(value="GOLD")
                ttk.Entry(settings_row, textvariable=self.bt_symbol_var, width=12).pack(side=tk.LEFT, padx=5)

                ttk.Label(settings_row, text="Timeframe:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
                self.bt_timeframe_var = tk.StringVar(value="M5")
                ttk.Entry(settings_row, textvariable=self.bt_timeframe_var, width=12).pack(side=tk.LEFT, padx=5)

                ttk.Label(settings_row, text="Company:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
                self.bt_company_var = tk.StringVar(value="MetaTrader 5")
                ttk.Entry(settings_row, textvariable=self.bt_company_var, width=15).pack(side=tk.LEFT, padx=5)

                ttk.Label(settings_row, text="Balance ($):", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=(20, 5))
                self.bt_balance_var = tk.StringVar(value="1000")
                ttk.Entry(settings_row, textvariable=self.bt_balance_var, width=12).pack(side=tk.LEFT, padx=5)

                # Row 3: Config Source
                config_row = ttk.Frame(config_frame)
                config_row.pack(fill=tk.X, pady=5)
                
                ttk.Label(config_row, text="Configuration:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
                self.bt_use_current_config = tk.BooleanVar(value=True)
                ttk.Checkbutton(config_row, text="Use Current Bot Config", 
                            variable=self.bt_use_current_config).pack(side=tk.LEFT, padx=5)

                # Control Buttons
                control_row = ttk.Frame(config_frame)
                control_row.pack(fill=tk.X, pady=(10, 0))
                
                self.bt_run_btn = ttk.Button(control_row, text="🚀 Run Backtest", 
                                            command=self.run_backtest, 
                                            style='Start.TButton', width=20)
                self.bt_run_btn.pack(side=tk.LEFT, padx=5)
                
                self.bt_cancel_btn = ttk.Button(control_row, text="⏹️ Cancel", 
                                                command=self.cancel_backtest, 
                                                width=15, state=tk.DISABLED)
                self.bt_cancel_btn.pack(side=tk.LEFT, padx=5)
                
                ttk.Button(control_row, text="📊 Export Results", 
                        command=self.export_backtest_results, width=18).pack(side=tk.LEFT, padx=5)
                
                ttk.Button(control_row, text="📁 Export Trades CSV", 
                        command=self.export_trades_csv, width=18).pack(side=tk.LEFT, padx=11)

                # Progress Bar
                progress_frame = ttk.Frame(config_frame)
                progress_frame.pack(fill=tk.X, pady=(10, 0))
                
                ttk.Label(progress_frame, text="Progress:", font=('Segoe UI', 9)).pack(side=tk.LEFT, padx=5)
                
                self.bt_progress = ttk.Progressbar(progress_frame, mode='determinate', length=500, style='Backtest.Horizontal.TProgressbar')
                self.bt_progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
                
                self.bt_progress_label = tk.StringVar(value="Ready")
                ttk.Label(progress_frame, textvariable=self.bt_progress_label, 
                        font=('Segoe UI', 9), foreground='#00e676').pack(side=tk.LEFT, padx=5)

                # === RESULTS SUMMARY ===
                results_frame = ttk.LabelFrame(main_container, text="📊 Backtest Results", padding=10)
                results_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

                # Initialize result variables
                self.bt_results = {
                    'total_trades': tk.StringVar(value="0"),
                    'wins': tk.StringVar(value="0"),
                    'losses': tk.StringVar(value="0"),
                    'win_rate': tk.StringVar(value="0.0%"),
                    'total_pnl': tk.StringVar(value="$0.00"),
                    'profit_factor': tk.StringVar(value="0.00"),
                    'max_drawdown': tk.StringVar(value="0.0%"),
                    'sharpe_ratio': tk.StringVar(value="0.00"),
                    'best_trade': tk.StringVar(value="$0.00"),
                    'worst_trade': tk.StringVar(value="$0.00"),
                    'avg_trade':  tk.StringVar(value="$0.00"),
                    'avg_duration': tk.StringVar(value="0 min"),
                }

                # Results Grid
                results_grid = ttk.Frame(results_frame)
                results_grid.pack(fill=tk.X, pady=5)

                # Row 1
                res_row1 = ttk.Frame(results_grid)
                res_row1.pack(fill=tk.X, pady=2)
                self.create_bt_result(res_row1, "Total Trades:", self.bt_results['total_trades'], width=12)
                self.create_bt_result(res_row1, "Wins:", self.bt_results['wins'], width=10)
                self.create_bt_result(res_row1, "Losses:", self.bt_results['losses'], width=10)
                self.create_bt_result(res_row1, "Win Rate:", self.bt_results['win_rate'], width=12)

                # Row 2
                res_row2 = ttk.Frame(results_grid)
                res_row2.pack(fill=tk.X, pady=2)
                self.create_bt_result(res_row2, "Total P&L:", self.bt_results['total_pnl'], width=15)
                self.create_bt_result(res_row2, "Profit Factor:", self.bt_results['profit_factor'], width=12)
                self.create_bt_result(res_row2, "Max Drawdown:", self.bt_results['max_drawdown'], width=12)
                self.create_bt_result(res_row2, "Sharpe Ratio:", self.bt_results['sharpe_ratio'], width=12)

                # Row 3
                res_row3 = ttk.Frame(results_grid)
                res_row3.pack(fill=tk.X, pady=2)
                self.create_bt_result(res_row3, "Best Trade:", self.bt_results['best_trade'], width=15)
                self.create_bt_result(res_row3, "Worst Trade:", self.bt_results['worst_trade'], width=15)
                self.create_bt_result(res_row3, "Avg Trade:", self.bt_results['avg_trade'], width=15)
                self.create_bt_result(res_row3, "Avg Duration:", self.bt_results['avg_duration'], width=15)

                # === ML ANALYSIS RESULTS ===
                ml_results_frame = ttk.LabelFrame(main_container, text="🤖 ML Analysis Results", padding=10)
                ml_results_frame.pack(fill=tk.X, pady=(0, 10), padx=10)

                # Initialize ML result variables
                self.ml_results = {
                    'ml_trades': tk.StringVar(value="0"),
                    'ml_accuracy': tk.StringVar(value="0.0%"),
                    'ml_predicted_wins': tk.StringVar(value="0"),
                    'ml_predicted_losses': tk.StringVar(value="0"),
                    'ml_avg_confidence': tk.StringVar(value="0.0%"),
                    'ml_trained': tk.StringVar(value="❌ Not Trained"),
                    'ml_training_status': tk.StringVar(value="Ready"),
                }

                # ML Results Grid
                ml_grid = ttk.Frame(ml_results_frame)
                ml_grid.pack(fill=tk.X, pady=5)

                # Row 1
                ml_row1 = ttk.Frame(ml_grid)
                ml_row1.pack(fill=tk.X, pady=2)
                self.create_bt_result(ml_row1, "Model Status:", self.ml_results['ml_trained'], width=15)
                self.create_bt_result(ml_row1, "ML Trades:", self.ml_results['ml_trades'], width=10)
                self.create_bt_result(ml_row1, "ML Accuracy:", self.ml_results['ml_accuracy'], width=12)
                self.create_bt_result(ml_row1, "Avg Confidence:", self.ml_results['ml_avg_confidence'], width=15)

                # Row 2
                ml_row2 = ttk.Frame(ml_grid)
                ml_row2.pack(fill=tk.X, pady=2)
                self.create_bt_result(ml_row2, "ML Predicted Wins:", self.ml_results['ml_predicted_wins'], width=12)
                self.create_bt_result(ml_row2, "ML Predicted Losses:", self.ml_results['ml_predicted_losses'], width=12)
                
                # ML Training Button
                ml_button_frame = ttk.Frame(ml_results_frame)
                ml_button_frame.pack(fill=tk.X, pady=(10, 0))
                
                self.ml_train_btn = ttk.Button(ml_button_frame, text="🧠 Train ML Model", 
                                              command=self.train_ml_model, width=18)
                self.ml_train_btn.pack(side=tk.LEFT, padx=5)
                trades_frame = ttk.LabelFrame(main_container, text="📋 Trade History", padding=10)
                trades_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=10)

                # Create Treeview with scrollbars
                tree_container = ttk.Frame(trades_frame)
                tree_container.pack(fill=tk.BOTH, expand=True)

                # Scrollbars
                tree_scroll_y = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, style='Red.Vertical.TScrollbar')
                tree_scroll_x = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, style='Red.Horizontal.TScrollbar')

                # Treeview
                columns = ('#', 'Date/Time', 'Type', 'Entry', 'Exit', 'Profit', 'ML Pred', 'ML Conf', 'Duration')
                self.bt_trades_tree = ttk.Treeview(tree_container, columns=columns, show='headings', 
                                                height=10,
                                                yscrollcommand=tree_scroll_y.set,
                                                xscrollcommand=tree_scroll_x.set)

                tree_scroll_y.config(command=self.bt_trades_tree.yview)
                tree_scroll_x.config(command=self.bt_trades_tree.xview)

                # Define headings
                self.bt_trades_tree.heading('#', text='#')
                self.bt_trades_tree.heading('Date/Time', text='Date/Time')
                self.bt_trades_tree.heading('Type', text='Type')
                self.bt_trades_tree.heading('Entry', text='Entry')
                self.bt_trades_tree.heading('Exit', text='Exit')
                self.bt_trades_tree.heading('Profit', text='Profit')
                self.bt_trades_tree.heading('ML Pred', text='ML Pred')
                self.bt_trades_tree.heading('ML Conf', text='ML Conf %')
                self.bt_trades_tree.heading('Duration', text='Duration')

                # Define column widths
                self.bt_trades_tree.column('#', width=40, anchor=tk.CENTER)
                self.bt_trades_tree.column('Date/Time', width=150, anchor=tk.W)
                self.bt_trades_tree.column('Type', width=60, anchor=tk.CENTER)
                self.bt_trades_tree.column('Entry', width=80, anchor=tk.E)
                self.bt_trades_tree.column('Exit', width=80, anchor=tk.E)
                self.bt_trades_tree.column('Profit', width=100, anchor=tk.E)
                self.bt_trades_tree.column('ML Pred', width=70, anchor=tk.CENTER)
                self.bt_trades_tree.column('ML Conf', width=70, anchor=tk.CENTER)
                self.bt_trades_tree.column('Duration', width=100, anchor=tk.CENTER)

                # Pack treeview and scrollbars using grid
                self.bt_trades_tree.grid(row=0, column=0, sticky='nsew', padx=(0, 2), pady=(0, 2))
                tree_scroll_y.grid(row=0, column=1, sticky='ns', padx=(0, 0), pady=(0, 2))
                tree_scroll_x.grid(row=1, column=0, sticky='ew', padx=(0, 2), pady=(0, 0))
                
                # Configure grid weights for proper resizing
                tree_container.grid_rowconfigure(0, weight=1)
                tree_container.grid_rowconfigure(1, weight=0)
                tree_container.grid_columnconfigure(0, weight=1)
                tree_container.grid_columnconfigure(1, weight=0)

                # Configure row colors
                self.bt_trades_tree.tag_configure('profit', background='#1a4d2e', foreground='#00e676')
                self.bt_trades_tree.tag_configure('loss', background='#4d1a1a', foreground='#ff1744')

                # === BACKTEST LOGS ===
                logs_frame = ttk.LabelFrame(main_container, text="📝 Backtest Logs", padding=10)
                logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

                self.bt_log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, height=10,
                                                            bg='#1a1e3a', fg='#e0e0e0', font=("Courier", 9))
                self.bt_log_text.pack(fill=tk.BOTH, expand=True, pady=5)

                # Tag configs
                self.bt_log_text.tag_config("INFO", foreground="#00e676")
                self.bt_log_text.tag_config("WARNING", foreground="#ffd600")
                self.bt_log_text.tag_config("ERROR", foreground="#ff1744")
                self.bt_log_text.tag_config("SUCCESS", foreground="#00b0ff")

                # Clear logs button
                ttk.Button(logs_frame, text="🗑️ Clear Logs", 
                        command=self.clear_bt_logs, width=15).pack(pady=(5, 0))

                # Store backtest data
                self.bt_trade_list = []
                self.bt_cancel_flag = False

                # Initial log
                self.add_bt_log("Strategy Tester initialized - Ready to backtest!", "INFO")
                self.add_bt_log("Configure parameters above and click 'Run Backtest'", "INFO")

            except Exception as e:
                self.log_message(f"Build strategy tab error: {e}", "ERROR")
                import traceback
                traceback.print_exc()

        def create_bt_result(self, parent, label_text, variable, width=15):
            """Create backtest result display widget"""
            container = ttk.Frame(parent)
            container.pack(side=tk.LEFT, padx=5)
            
            ttk.Label(container, text=label_text, font=('Segoe UI', 9)).pack(side=tk.LEFT)
            ttk.Label(container, textvariable=variable, style='Metric.TLabel', 
                    width=width).pack(side=tk.LEFT, padx=(5, 0))

        def add_bt_log(self, message, level="INFO"):
            """Add message to backtest logs"""
            try:
                if hasattr(self, 'bt_log_text'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {message}\n"
                    self.bt_log_text.insert(tk.END, log_entry, level)
                    self.bt_log_text.see(tk.END)
            except Exception as e: 
                pass

        def clear_bt_logs(self):
            """Clear backtest logs"""
            try: 
                if hasattr(self, 'bt_log_text'):
                    self.bt_log_text.delete(1.0, tk.END)
                    self.add_bt_log("Logs cleared", "INFO")
            except Exception as e:
                pass

        def update_bt_progress(self, progress, message=""):
            """Update backtest progress (called from backtester)"""
            try:
                self.root.after(0, lambda: self.bt_progress.config(value=progress))
                self.root.after(0, lambda: self.bt_progress_label.set(f"{progress:.1f}%"))
                if message:
                    self.root.after(0, lambda: self.add_bt_log(message, "INFO"))
            except Exception as e:
                pass

        def display_backtest_results(self, results):
            """Display backtest results in UI with ML predictions"""
            try:
                # Update result variables
                self.bt_results['total_trades'].set(str(results.get('total_trades', 0)))
                self.bt_results['wins'].set(str(results.get('wins', 0)))
                self.bt_results['losses'].set(str(results.get('losses', 0)))
                self.bt_results['win_rate'].set(f"{results.get('win_rate', 0):.1f}%")
                self.bt_results['total_pnl'].set(f"${results.get('total_pnl', 0):.2f}")
                self.bt_results['profit_factor'].set(f"{results.get('profit_factor', 0):.2f}")
                self.bt_results['max_drawdown'].set(f"{results.get('max_drawdown', 0):.2f}%")
                self.bt_results['sharpe_ratio'].set(f"{results.get('sharpe_ratio', 0):.2f}")
                self.bt_results['best_trade'].set(f"${results.get('best_trade', 0):.2f}")
                self.bt_results['worst_trade'].set(f"${results.get('worst_trade', 0):.2f}")
                self.bt_results['avg_trade'].set(f"${results.get('avg_trade', 0):.2f}")
                self.bt_results['avg_duration'].set(results.get('avg_duration', '0 min'))
                
                # Update ML results if available
                if hasattr(self, 'ml_predictor') and self.ml_predictor:
                    ml_trades = results.get('ml_trades', 0)
                    ml_accuracy = results.get('ml_accuracy', 0)
                    ml_pred_wins = results.get('ml_predicted_wins', 0)
                    ml_pred_losses = results.get('ml_predicted_losses', 0)
                    ml_avg_conf = results.get('ml_avg_confidence', 0)
                    
                    self.ml_results['ml_trades'].set(str(ml_trades))
                    self.ml_results['ml_accuracy'].set(f"{ml_accuracy:.1f}%")
                    self.ml_results['ml_predicted_wins'].set(str(ml_pred_wins))
                    self.ml_results['ml_predicted_losses'].set(str(ml_pred_losses))
                    self.ml_results['ml_avg_confidence'].set(f"{ml_avg_conf:.1f}%")
                
                # Clear and populate trade history table
                for item in self.bt_trades_tree.get_children():
                    self.bt_trades_tree.delete(item)
                
                # Store trades for export
                self.bt_trade_list = results.get('trades', [])
                
                # Populate table
                for i, trade in enumerate(self.bt_trade_list, 1):
                    profit = trade.get('profit', 0)
                    tag = 'profit' if profit > 0 else 'loss'
                    
                    # Format datetime
                    dt = trade.get('entry_time', datetime.now())
                    if isinstance(dt, str):
                        dt_str = dt
                    else:
                        dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Get ML prediction if available
                    ml_pred = trade.get('ml_prediction', '')
                    ml_confidence = trade.get('ml_confidence', 0)
                    
                    self.bt_trades_tree.insert('', 'end', values=(
                        i,
                        dt_str,
                        trade.get('type', ''),
                        f"{trade.get('entry_price', 0):.5f}",
                        f"{trade.get('exit_price', 0):.5f}",
                        f"${profit:.2f}",
                        ml_pred if ml_pred else '—',
                        f"{ml_confidence:.0f}%" if ml_confidence else '—',
                        trade.get('duration', '')
                    ), tags=(tag,))
                
                self.add_bt_log(f"✓ Results displayed: {len(self.bt_trade_list)} trades", "SUCCESS")
                
            except Exception as e:
                self.log_message(f"Display results error: {e}", "ERROR")
                import traceback
                traceback.print_exc()

        def train_ml_model(self):
            """Train ML model in background thread"""
            try:
                symbol = self.bt_symbol_var.get().strip()
                if not symbol:
                    messagebox.showerror("Error", "Please enter a symbol first!")
                    return
                
                self.ml_train_btn.config(state=tk.DISABLED)
                self.ml_results['ml_training_status'].set("Training...")
                
                def ml_training_thread():
                    try:
                        self.root.after(0, lambda: self.add_bt_log("="*60, "INFO"))
                        self.root.after(0, lambda: self.add_bt_log("🧠 Starting ML Model Training...", "INFO"))
                        self.root.after(0, lambda: self.add_bt_log(f"📊 Symbol: {symbol}", "INFO"))
                        self.root.after(0, lambda: self.add_bt_log("⏳ Collecting historical data (30 days)...", "INFO"))
                        
                        # Import ML predictor
                        from ml_predictor import MLPredictor
                        import MetaTrader5 as mt5
                        
                        # Initialize MT5 first
                        if not mt5.initialize():
                            self.root.after(0, lambda: self.add_bt_log("❌ Failed to initialize MT5", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("   Make sure MT5 is running", "ERROR"))
                            self.root.after(0, lambda: self.ml_results['ml_trained'].set("❌ MT5 Failed"))
                            self.root.after(0, lambda: self.ml_results['ml_training_status'].set("MT5 Error"))
                            return
                        
                        self.root.after(0, lambda: self.add_bt_log("✓ MT5 initialized", "INFO"))
                        
                        # Get bot config
                        if self.active_bot_id and self.active_bot_id in self.bots:
                            import copy
                            config = copy.deepcopy(self.bots[self.active_bot_id]['config'])
                        else:
                            config = self.get_config_from_gui()
                        
                        config['symbol'] = symbol
                        config['enable_ml'] = True
                        
                        # Initialize ML predictor
                        self.root.after(0, lambda: self.add_bt_log(f"📚 Initializing ML predictor for {symbol}...", "INFO"))
                        ml_predictor = MLPredictor(symbol, config)
                        
                        # Train
                        self.root.after(0, lambda: self.add_bt_log("📚 Training models (RandomForest + GradientBoosting)...", "INFO"))
                        success = ml_predictor.train(days=30)
                        
                        if success:
                            self.root.after(0, lambda: self.add_bt_log("✅ ML Model Training Completed!", "SUCCESS"))
                            self.root.after(0, lambda: self.ml_results['ml_trained'].set("✅ Trained"))
                            self.root.after(0, lambda: self.ml_results['ml_training_status'].set("Ready"))
                            
                            # Store ML predictor for backtest
                            self.ml_predictor = ml_predictor
                            
                            # Log training stats
                            if hasattr(ml_predictor, 'training_stats'):
                                stats = ml_predictor.training_stats
                                self.root.after(0, lambda: self.add_bt_log(f"  📈 Training Accuracy: {stats.get('train_accuracy', 0):.2%}", "INFO"))
                                self.root.after(0, lambda: self.add_bt_log(f"  🎯 Test Accuracy: {stats.get('test_accuracy', 0):.2%}", "INFO"))
                        else:
                            self.root.after(0, lambda: self.add_bt_log("❌ ML Training Failed!", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("   Check backtest logs for details", "ERROR"))
                            self.root.after(0, lambda: self.ml_results['ml_trained'].set("❌ Failed"))
                            self.root.after(0, lambda: self.ml_results['ml_training_status'].set("Failed"))
                        
                        self.root.after(0, lambda: self.add_bt_log("="*60, "INFO"))
                        
                    except ImportError as e:
                        self.root.after(0, lambda: self.add_bt_log("❌ Failed to import ML predictor", "ERROR"))
                        self.root.after(0, lambda: self.add_bt_log(f"   Error: {str(e)}", "ERROR"))
                        self.root.after(0, lambda: self.add_bt_log("   Make sure ml_predictor.py is in the same folder", "ERROR"))
                        self.root.after(0, lambda: self.ml_results['ml_trained'].set("❌ Import Failed"))
                    except Exception as e:
                        self.root.after(0, lambda: self.add_bt_log(f"❌ ML Training Error: {str(e)}", "ERROR"))
                        self.root.after(0, lambda: self.ml_results['ml_trained'].set("❌ Error"))
                        import traceback
                        self.root.after(0, lambda: self.add_bt_log(f"   Traceback: {traceback.format_exc()}", "ERROR"))
                    finally:
                        self.root.after(0, lambda: self.ml_train_btn.config(state=tk.NORMAL))
                
                # Start training thread
                threading.Thread(target=ml_training_thread, daemon=True, name="MLTrainingThread").start()
                
            except Exception as e:
                messagebox.showerror("Error", f"ML training error: {str(e)}")
                self.ml_train_btn.config(state=tk.NORMAL)

        def cancel_backtest(self):
            """Cancel running backtest"""
            try: 
                self.bt_cancel_flag = True
                self.add_bt_log("⚠️ Cancelling backtest...", "WARNING")
            except Exception as e:
                self.log_message(f"Cancel backtest error: {e}", "ERROR")

        def launch_csv_converter(self):
            """Launch CSV to Excel Converter GUI"""
            try:
                import subprocess
                import os
                
                converter_path = os.path.join(os.path.dirname(__file__), "csv_to_excel_converter_gui.py")
                
                if not os.path.exists(converter_path):
                    messagebox.showerror("Error", f"Converter not found: {converter_path}")
                    return
                
                # Launch in separate process
                subprocess.Popen(["python", converter_path])
                self.log_message("✓ CSV to Excel Converter launched", "INFO")
                
            except Exception as e:
                self.log_message(f"Launch converter error: {e}", "ERROR")
                messagebox.showerror("Error", f"Failed to launch converter:\n{e}")

        def export_backtest_results(self):
            """Export backtest results to JSON"""
            try:
                if not hasattr(self, 'bt_trade_list') or len(self.bt_trade_list) == 0:
                    messagebox.showwarning("Warning", "No backtest results to export!")
                    return
                
                filename = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                    title="Export Backtest Results",
                    initialfile=f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                if filename:
                    # Prepare export data
                    results_data = {
                        'backtest_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': self.bt_symbol_var.get(),
                        'start_date': self.bt_start_date_var.get(),
                        'end_date': self.bt_end_date_var.get(),
                        'initial_balance': self.bt_balance_var.get(),
                        'config': self.get_config_from_gui() if hasattr(self, 'get_config_from_gui') else {},
                        'results': {
                            'total_trades':  self.bt_results['total_trades'].get(),
                            'wins': self.bt_results['wins'].get(),
                            'losses': self.bt_results['losses'].get(),
                            'win_rate': self.bt_results['win_rate'].get(),
                            'total_pnl': self.bt_results['total_pnl'].get(),
                            'profit_factor':  self.bt_results['profit_factor'].get(),
                            'max_drawdown': self.bt_results['max_drawdown'].get(),
                            'sharpe_ratio': self.bt_results['sharpe_ratio'].get(),
                            'best_trade':  self.bt_results['best_trade'].get(),
                            'worst_trade': self.bt_results['worst_trade'].get(),
                            'avg_trade':  self.bt_results['avg_trade'].get(),
                            'avg_duration': self.bt_results['avg_duration'].get(),
                        },
                        'trades': []
                    }
                    
                    # Add trade details (convert datetime to string)
                    for trade in self.bt_trade_list:
                        trade_copy = dict(trade)
                        # Convert datetime objects to strings
                        for key in ['entry_time', 'exit_time']:
                            if key in trade_copy and isinstance(trade_copy[key], datetime):
                                trade_copy[key] = trade_copy[key].strftime('%Y-%m-%d %H:%M:%S')
                        results_data['trades'].append(trade_copy)
                    
                    # Write to file
                    with open(filename, 'w') as f:
                        json.dump(results_data, f, indent=4)
                    
                    self.add_bt_log(f"✓ Results exported to:  {filename}", "SUCCESS")
                    messagebox.showinfo("Success", f"Results exported to:\n{filename}")
                    
            except Exception as e:
                error_msg = f"Export results error: {str(e)}"
                self.add_bt_log(error_msg, "ERROR")
                messagebox.showerror("Error", error_msg)

        def export_trades_csv(self):
            """Export trade history to CSV with running balance"""
            try: 
                if not hasattr(self, 'bt_trade_list') or len(self.bt_trade_list) == 0:
                    messagebox.showwarning("Warning", "No trades to export!")
                    return
                
                filename = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    title="Export Trade History",
                    initialfile=f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                
                if filename:
                    import csv
                    
                    with open(filename, 'w', newline='') as f:
                        writer = csv.writer(f)
                        
                        # Get initial balance from first trade's Saldo Awal
                        initial_balance = 0.0
                        if len(self.bt_trade_list) > 0:
                            first_trade = self.bt_trade_list[0]
                            initial_balance = float(first_trade.get('profit', 0))
                            # Calculate backward to get true initial balance
                            running_balance = 0.0
                            for i, trade in enumerate(self.bt_trade_list):
                                profit = float(trade.get('profit', 0))
                                if i == 0:
                                    initial_balance = -profit  # First trade's profit to reverse back to initial
                                running_balance += profit
                            # Get initial balance from first trade
                            initial_balance = 0.0
                            if len(self.bt_trade_list) > 0:
                                # Reverse calculate from all trades
                                total_profit = sum(float(t.get('profit', 0)) for t in self.bt_trade_list)
                                initial_balance = self.balance - total_profit if hasattr(self, 'balance') else 1000.0
                                # Or use the value from backtest
                                if hasattr(self, 'bt_balance_var'):
                                    try:
                                        initial_balance = float(self.bt_balance_var.get())
                                    except:
                                        initial_balance = 1000.0
                        
                        # Baris pertama: Initial Balance
                        writer.writerow(['Initial Balance ($)', initial_balance])
                        writer.writerow([])  # Empty row for spacing
                        
                        # Get volume from trading configuration
                        try:
                            volume = float(self.volume_var.get().strip())
                        except:
                            volume = 0.01
                        
                        # Header
                        writer.writerow(['#', 'Entry Time', 'Exit Time', 'Type', 'Entry Price', 
                                    'Exit Price', 'Volume', 'Profit', 'Saldo Awal', 'Saldo Akhir', 'Duration', 'Reason', 
                                    'Symbol', 'Period', 'Company'])
                        
                        # Calculate running balance
                        running_balance = initial_balance
                        
                        # Trades
                        for i, trade in enumerate(self.bt_trade_list, 1):
                            # Format datetime
                            entry_time = trade.get('entry_time', '')
                            exit_time = trade.get('exit_time', '')
                            
                            if isinstance(entry_time, datetime):
                                entry_time = entry_time.strftime('%Y-%m-%d %H:%M:%S')
                            if isinstance(exit_time, datetime):
                                exit_time = exit_time.strftime('%Y-%m-%d %H:%M:%S')
                            
                            profit = float(trade.get('profit', 0))
                            saldo_awal = running_balance
                            saldo_akhir = running_balance + profit
                            running_balance = saldo_akhir
                            
                            # Get trading parameters
                            symbol = self.bt_symbol_var.get() if hasattr(self, 'bt_symbol_var') else 'Unknown'
                            period = self.bt_timeframe_var.get() if hasattr(self, 'bt_timeframe_var') else 'Unknown'
                            company = self.bt_company_var.get() if hasattr(self, 'bt_company_var') else 'Unknown'
                            
                            writer.writerow([
                                i,
                                entry_time,
                                exit_time,
                                trade.get('type', ''),
                                f"{trade.get('entry_price', 0):.5f}",
                                f"{trade.get('exit_price', 0):.5f}",
                                f"{volume:.2f}",
                                f"{profit:.2f}",
                                f"{saldo_awal:.2f}",
                                f"{saldo_akhir:.2f}",
                                trade.get('duration', ''),
                                trade.get('reason', ''),
                                symbol,
                                period,
                                company
                            ])
                    
                    self.add_bt_log(f"✓ Trades exported to: {filename}", "SUCCESS")
                    messagebox.showinfo("Success", f"Trades exported to:\n{filename}")
                    
            except Exception as e:
                error_msg = f"Export trades error: {str(e)}"
                self.add_bt_log(error_msg, "ERROR")
                messagebox.showerror("Error", error_msg)

        def run_backtest(self):
            """Run backtest in background thread with progress tracking"""
            try:
                # ✅ FIX 1: Validate inputs PROPERLY
                try:
                    start_date = datetime.strptime(self.bt_start_date_var.get(), "%Y-%m-%d")
                    end_date = datetime.strptime(self.bt_end_date_var.get(), "%Y-%m-%d")
                    
                    if start_date >= end_date:
                        messagebox.showerror("Error", "Start date must be before end date!")
                        return
                    
                    days_diff = (end_date - start_date).days
                    
                    if days_diff > 365:
                        response = messagebox.askyesno(
                            "Long Backtest Warning", 
                            f"Backtest period is {days_diff} days ({days_diff/365:.1f} years).\n\n" +
                            "This may take a long time and use significant memory.\n\n" +
                            "Continue anyway?"
                        )
                        if not response:
                            return
                    
                    if days_diff < 1:
                        messagebox.showerror("Error", "Backtest period must be at least 1 day!")
                        return
                        
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid date format!\n\nUse YYYY-MM-DD format.\n\nError: {e}")
                    return

                # ✅ FIX 2: Validate balance from GUI
                try:
                    initial_balance = float(self.bt_balance_var.get())
                    if initial_balance <= 0:
                        messagebox.showerror("Error", "Initial balance must be positive!")
                        return
                    if initial_balance < 100:
                        messagebox.showwarning("Warning", f"Initial balance is very low (${initial_balance:.2f})")
                except ValueError:
                    messagebox.showerror("Error", "Invalid balance amount!")
                    return

                # ✅ FIX 3: Validate symbol from GUI
                symbol = self.bt_symbol_var.get().strip()
                if not symbol:  
                    messagebox.showerror("Error", "Please enter a symbol!")
                    return

                # Update UI state
                self.bt_run_btn.config(state=tk.DISABLED)
                self.bt_cancel_btn.config(state=tk.NORMAL)
                self.bt_cancel_flag = False

                # Clear previous results
                self.bt_trade_list = []
                for item in self.bt_trades_tree.get_children():
                    self.bt_trades_tree.delete(item)
                
                # Reset result displays
                for key in self.bt_results: 
                    if key == 'total_trades':
                        self.bt_results[key].set("0")
                    elif 'pct' in key or 'rate' in key:
                        self.bt_results[key].set("0.0%")
                    elif 'ratio' in key or 'factor' in key:
                        self.bt_results[key].set("0.00")
                    elif key == 'avg_duration':
                        self.bt_results[key].set("0 min")
                    else:
                        self.bt_results[key].set("$0.00")

                # Reset progress
                self.bt_progress['value'] = 0
                self.bt_progress_label.set("Starting...")

                # Log start
                self.add_bt_log("="*60, "INFO")
                self.add_bt_log("🚀 BACKTEST STARTED", "SUCCESS")
                self.add_bt_log("="*60, "INFO")
                self.add_bt_log(f"📅 Period: {self.bt_start_date_var.get()} to {self.bt_end_date_var.get()}", "INFO")
                self.add_bt_log(f"📊 Symbol: {symbol}", "INFO")
                self.add_bt_log(f"💰 Initial Balance: ${initial_balance: ,.2f}", "INFO")
                self.add_bt_log(f"📆 Duration: {days_diff} days", "INFO")

                # ✅ CRITICAL FIX: Create thread-safe callback
                progress_callback = ThreadSafeCallback(self.root, self.update_bt_progress)
                
                # ✅ FIX 4: Run backtest in background thread WITH PROPER CONFIG
                def backtest_thread():
                    try:
                        # ✅ CREATE ISOLATED CONFIG (CRITICAL FIX!)
                        if self.bt_use_current_config.get() and self.active_bot_id and self.active_bot_id in self.bots:
                            # Use active bot's config as BASE
                            bot = self.bots[self.active_bot_id]
                            import copy
                            config = copy.deepcopy(bot['config'])  # Deep copy untuk isolasi
                            self.root.after(0, lambda: self.add_bt_log(f"✓ Using {self.active_bot_id} configuration", "INFO"))
                        else:
                            # Use GUI config
                            config = self.get_config_from_gui()
                            self.root.after(0, lambda: self.add_bt_log("✓ Using GUI configuration", "INFO"))
                        
                        # ✅ OVERRIDE CRITICAL PARAMS FROM GUI (ALWAYS!)
                        config['symbol'] = symbol  # ← MUST use GUI symbol!  
                        self.root.after(0, lambda: self.add_bt_log(f"✓ Symbol: {symbol}", "INFO"))
                        self.root.after(0, lambda: self.add_bt_log(f"✓ Initial balance: ${initial_balance:,.2f}", "INFO"))

                        # Import backtester
                        self.root.after(0, lambda: self.add_bt_log("📦 Loading backtester module...", "INFO"))
                        self.root.after(0, lambda: self.bt_progress_label.set("Loading module..."))
                        
                        from strategy_backtester import StrategyBacktester
                        
                        # ✅ GET ML PREDICTOR IF AVAILABLE
                        ml_predictor = getattr(self, 'ml_predictor', None)
                        if ml_predictor and hasattr(ml_predictor, 'is_trained') and ml_predictor.is_trained:
                            self.root.after(0, lambda: self.add_bt_log("✅ ML Predictor available and trained", "SUCCESS"))
                        else:
                            ml_predictor = None
                        
                        # ✅ CREATE BACKTESTER WITH ISOLATED BALANCE AND ML PREDICTOR
                        self.root.after(0, lambda: self.add_bt_log("✓ Backtester initialized", "SUCCESS"))
                        backtester = StrategyBacktester(config, initial_balance, ml_predictor=ml_predictor)  # ← WITH ML!
                        
                        # ✅ CHECK SYMBOL AVAILABILITY WITH FUZZY MATCHING
                        self.root.after(0, lambda: self.add_bt_log(f"🔍 Checking symbol availability...", "INFO"))
                        actual_symbol = backtester.find_symbol_in_mt5(symbol)
                        
                        if not actual_symbol:
                            # Symbol not found
                            available_symbols = backtester.get_available_symbols()
                            self.root.after(0, lambda: self.add_bt_log(f"❌ Symbol '{symbol}' NOT FOUND in MT5", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log(f"Available symbols (first 20): {', '.join(available_symbols[:20])}", "INFO"))
                            self.root.after(0, lambda: self.add_bt_log("Trying with case-insensitive matching or partial matching...", "INFO"))
                            self.root.after(0, lambda: self.bt_progress_label.set("Symbol not available"))
                            return
                        
                        self.root.after(0, lambda: self.add_bt_log(f"✓ Symbol found: '{symbol}' → '{actual_symbol}'", "SUCCESS"))
                        
                        # Run backtest with progress tracking
                        self.root.after(0, lambda: self.add_bt_log("⏳ Running backtest simulation...", "INFO"))
                        self.root.after(0, lambda: self.bt_progress_label.set("Running..."))
                        
                        results = backtester.run_backtest(
                            start_date,
                            end_date,
                            progress_callback=progress_callback,  # ✅ NOW THREAD-SAFE!
                            cancel_check=lambda: self.bt_cancel_flag
                        )
                        
                        # Handle results
                        if self.bt_cancel_flag:
                            self.root.after(0, lambda: self.add_bt_log("="*60, "WARNING"))
                            self.root.after(0, lambda: self.add_bt_log("⚠️ BACKTEST CANCELLED BY USER", "WARNING"))
                            self.root.after(0, lambda: self.add_bt_log("="*60, "WARNING"))
                            self.root.after(0, lambda: self.bt_progress_label.set("Cancelled"))
                            
                        elif results:  
                            # Display results
                            self.root.after(0, lambda: self.display_backtest_results(results))
                            
                            # Log summary
                            self.root.after(0, lambda: self.add_bt_log("="*60, "SUCCESS"))
                            self.root.after(0, lambda: self.add_bt_log("✅ BACKTEST COMPLETED SUCCESSFULLY!", "SUCCESS"))
                            self.root.after(0, lambda: self.add_bt_log("="*60, "SUCCESS"))
                            self.root.after(0, lambda: self.add_bt_log(f"📊 Total Trades: {results.get('total_trades', 0)}", "INFO"))
                            self.root.after(0, lambda: self.add_bt_log(f"💰 Total P&L: ${results.get('total_pnl', 0):.2f}", "INFO"))
                            self.root.after(0, lambda: self.add_bt_log(f"📈 Win Rate: {results.get('win_rate', 0):.1f}%", "INFO"))
                            self.root.after(0, lambda: self.add_bt_log(f"📉 Max Drawdown: {results.get('max_drawdown', 0):.2f}%", "INFO"))
                            self.root.after(0, lambda: self.bt_progress_label.set("Complete ✓"))
                            
                        else:  
                            self.root.after(0, lambda: self.add_bt_log("="*60, "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("❌ BACKTEST FAILED - NO RESULTS", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("="*60, "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("Possible causes:", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("  - No historical data available for symbol", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("  - MT5 connection failed", "ERROR"))
                            self.root.after(0, lambda: self.add_bt_log("  - Invalid date range", "ERROR"))
                            self.root.after(0, lambda: self.bt_progress_label.set("Failed ✗"))
                            
                    except ImportError as e:
                        error_msg = f"Failed to import backtester module: {str(e)}"
                        self.root.after(0, lambda: self.add_bt_log(f"❌ {error_msg}", "ERROR"))
                        self.root.after(0, lambda: self.add_bt_log("Make sure strategy_backtester.py is in the same folder", "ERROR"))
                        self.root.after(0, lambda: messagebox.showerror("Import Error", error_msg))
                        
                    except Exception as e:  
                        error_msg = str(e)
                        self.root.after(0, lambda: self.add_bt_log("="*60, "ERROR"))
                        self.root.after(0, lambda: self.add_bt_log(f"❌ BACKTEST ERROR: {error_msg}", "ERROR"))
                        self.root.after(0, lambda: self.add_bt_log("="*60, "ERROR"))
                        
                        # Log full traceback to console
                        import traceback
                        tb = traceback.format_exc()
                        print("\n" + "="*60)
                        print("BACKTEST ERROR DETAILS:")
                        print("="*60)
                        print(tb)
                        print("="*60 + "\n")
                        
                        self.root.after(0, lambda: self.add_bt_log("Full error details printed to console", "ERROR"))
                        self.root.after(0, lambda: messagebox.showerror(
                            "Backtest Error", 
                            f"An error occurred during backtest:\n\n{error_msg}\n\nCheck console and logs for details."
                        ))
                        
                    finally:
                        # Re-enable UI controls
                        self.root.after(0, lambda: self.bt_run_btn.config(state=tk.NORMAL))
                        self.root.after(0, lambda: self.bt_cancel_btn.config(state=tk.DISABLED))
                        
                        # Final progress update
                        if not self.bt_cancel_flag:
                            self.root.after(0, lambda: self.bt_progress.config(value=100))

                # Start backtest thread
                threading.Thread(target=backtest_thread, daemon=True, name="BacktestThread").start()
                
                self.add_bt_log("✓ Backtest thread started", "INFO")

            except Exception as e:
                error_msg = f"Failed to start backtest: {str(e)}"
                self.add_bt_log(f"❌ {error_msg}", "ERROR")
                self.log_message(error_msg, "ERROR")
                messagebox.showerror("Error", error_msg)
                
                # Re-enable buttons on error
                self.bt_run_btn.config(state=tk.NORMAL)
                self.bt_cancel_btn.config(state=tk.DISABLED)

        def view_trade_history(self):
            """NEW: View trade history from database"""
            if not self.active_bot_id:
                messagebox.showwarning("Warning", "Select a bot first")
                return
            
            # Create new window
            history_window = tk.Toplevel(self.root)
            history_window.title(f"Trade History - {self.active_bot_id}")
            history_window.geometry("1000x600")
            
            # Get trades from database
            trades = self.trade_db.get_trades(bot_id=self.active_bot_id, limit=100)
            
            # Create treeview
            tree = ttk.Treeview(history_window, columns=(
                'timestamp', 'symbol', 'type', 'volume', 'profit'
            ), show='headings')
            
            tree.heading('timestamp', text='Time')
            tree.heading('symbol', text='Symbol')
            tree.heading('type', text='Type')
            tree.heading('volume', text='Volume')
            tree.heading('profit', text='Profit')
            
            # Populate
            for trade in trades:
                dt = datetime.fromtimestamp(trade['timestamp'])
                tree.insert('', 'end', values=(
                    dt.strftime('%Y-%m-%d %H:%M:%S'),
                    trade['symbol'],
                    trade['trade_type'],
                    f"{trade['volume']:.2f}",
                    f"${trade['profit']:.2f}"
                ))
            
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Export button
            ttk.Button(
                history_window,
                text="📤 Export CSV",
                command=lambda: self.trade_db.export_to_csv(
                    f"{self.active_bot_id}_trades.csv",
                    self.active_bot_id
                )
            ).pack(pady=10)



        def on_tab_changed(self, event):
            """Handle tab change events - Keep active bot selected"""
            try:
                selected_tab = event.widget.select()
                tab_text = event.widget.tab(selected_tab, "text")
                
                # ✅ RESTORE ACTIVE BOT SELECTION (Persist across tab switches)
                if self.active_bot_id and self.active_bot_id in self.bots:
                    try:
                        bot_list = list(self.bots.keys())
                        idx = bot_list.index(self.active_bot_id)
                        
                        # ✅ Clear and re-apply selection to ensure highlight is visible
                        self.bot_listbox.selection_clear(0, tk.END)
                        self.bot_listbox.selection_set(idx)
                        self.bot_listbox.activate(idx)  # ← Also activate for focus
                        self.bot_listbox.see(idx)  # ← Ensure it's visible in listbox
                        
                        self.log_message(f"✓ {self.active_bot_id} kept selected", "INFO")
                    except (ValueError, tk.TclError):
                        pass
                
                # Build ML Models tab when first opened
                if "ML" in tab_text and not hasattr(self, 'ml_log_text'):
                    self.build_ml_tab()
                
                # Build Strategy Tester tab when first opened
                if "Strategy" in tab_text and not hasattr(self, 'bt_log_text'):
                    self.build_strategy_tab()
                
                # Update Telegram bot selector when Telegram tab is opened
                if "Telegram" in tab_text and hasattr(self, 'telegram_bot_selector'):
                    self.update_telegram_bot_selector()
                    
            except Exception as e:  
                self.log_message(f"Tab change error: {e}", "ERROR")

        def load_ml_models(self):
            """Load trained ML models from folder"""
            try: 
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                folder_path = filedialog.askdirectory(
                    title="Select ML Models Folder",
                    initialdir=os.getcwd()
                )
                
                if not folder_path:  
                    return
                
                self.log_ml_message(f"📁 Loading from: {folder_path}", "INFO")
                
                # ✅ Create MLPredictor
                bot = self.bots[self.active_bot_id]
                config = bot['config']
                
                from ml_predictor import MLPredictor
                ml_predictor = MLPredictor(config['symbol'], config)
                
                # ✅ Load models (with detailed console output)
                self.log_ml_message("🔄 Loading models...(check console for details)", "INFO")
                
                success = ml_predictor.load_models(folder_path)
                
                if success:
                    # ✅ Store in bot
                    bot['ml_predictor'] = ml_predictor
                    
                    # Verify stored
                    if bot['ml_predictor'].is_trained:
                        self.log_ml_message("✅ Models loaded and stored in bot!", "SUCCESS")
                    else:
                        self.log_ml_message("⚠️ Models loaded but not marked as trained", "WARNING")
                    
                    # Display success status
                    status_text = f"""
        ╔══════════════════════════════════════╗
        ║   ML MODELS LOADED SUCCESSFULLY      ║
        ╚══════════════════════════════════════╝

        📊 Direction Model: ✓ Loaded
        📊 Confidence Model: ✓ Loaded  
        📊 Scaler: ✓ Loaded

        📁 Source: {os.path.basename(folder_path)}
        🕐 Loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        ✅ Status: Ready for prediction! 

        💡 Next steps: 
        1.Enable "ML Predictions" in Control Panel
        2.Start trading to use ML predictions
        """
                    
                    if hasattr(self, 'ml_status_text'):
                        self.ml_status_text.delete(1.0, tk.END)
                        self.ml_status_text.insert(tk.END, status_text)
                    
                    messagebox.showinfo("Success", 
                        "ML Models loaded successfully!\n\n" +
                        "Enable 'ML Predictions' in Control Panel to use them.")
                else:
                    self.log_ml_message("❌ Failed to load models", "ERROR")
                    self.log_ml_message("   Check console window for details", "ERROR")
                    messagebox.showerror("Error", 
                        "Failed to load models!\n\n" +
                        "Check the console window for detailed error messages.")
                
            except Exception as e:  
                error_msg = f"Load error: {str(e)}"
                self.log_ml_message(error_msg, "ERROR")
                import traceback
                tb = traceback.format_exc()
                print(tb)
                messagebox.showerror("Error", f"{error_msg}\n\nCheck console for details.")

        def build_telegram_tab(self):
            """Build Telegram Service Signal tab"""
            try:
                # Create scrollable frame
                canvas = tk.Canvas(self.telegram_tab, bg='#0a0e27', highlightthickness=0)
                scrollbar = ttk.Scrollbar(self.telegram_tab, orient="vertical", command=canvas.yview, style='Red.Vertical.TScrollbar')
                scrollable_frame = ttk.Frame(canvas)

                scrollable_frame.bind(
                    "<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                )

                canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                canvas.configure(yscrollcommand=scrollbar.set)

                canvas.pack(side="left", fill="both", expand=True)
                scrollbar.pack(side="right", fill="y")

                # Title
                title_label = ttk.Label(scrollable_frame, text="📱 Telegram Service Signal",
                                      font=('Segoe UI', 16, 'bold'), foreground='#00e676',
                                      background='#0a0e27')
                title_label.pack(pady=(10, 20))

                # Bot Selection Frame
                bot_frame = ttk.LabelFrame(scrollable_frame, text="🤖 Bot Selection", padding=10)
                bot_frame.pack(fill=tk.X, padx=10, pady=5)

                ttk.Label(bot_frame, text="Select Bot:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
                self.telegram_bot_selector = ttk.Combobox(bot_frame, values=[],
                                                        state='readonly', width=20)
                self.telegram_bot_selector.pack(side=tk.LEFT, padx=5)
                self.telegram_bot_selector.bind('<<ComboboxSelected>>', self.on_telegram_bot_selected)

                # Telegram Configuration Frame
                config_frame = ttk.LabelFrame(scrollable_frame, text="⚙️ Telegram Configuration", padding=10)
                config_frame.pack(fill=tk.X, padx=10, pady=5)

                # Token input
                token_frame = ttk.Frame(config_frame)
                token_frame.pack(fill=tk.X, pady=5)
                ttk.Label(token_frame, text="Bot Token:", width=15, font=('Segoe UI', 10)).pack(side=tk.LEFT)
                self.telegram_token_entry = ttk.Entry(token_frame, textvariable=self.telegram_token_var, width=50)
                self.telegram_token_entry.pack(side=tk.LEFT, padx=5)

                # Chat IDs input
                chat_frame = ttk.Frame(config_frame)
                chat_frame.pack(fill=tk.X, pady=5)
                ttk.Label(chat_frame, text="Chat IDs (comma separated):", width=25, font=('Segoe UI', 10)).pack(side=tk.LEFT)
                self.telegram_chat_ids_entry = ttk.Entry(chat_frame, textvariable=self.telegram_chat_ids_var, width=40)
                self.telegram_chat_ids_entry.pack(side=tk.LEFT, padx=5)

                # Buttons Frame
                buttons_frame = ttk.Frame(config_frame)
                buttons_frame.pack(fill=tk.X, pady=10)

                self.test_token_btn = ttk.Button(buttons_frame, text="🔗 Test Token Connection",
                                               command=self.test_telegram_token, width=20)
                self.test_token_btn.pack(side=tk.LEFT, padx=5)

                self.test_signal_btn = ttk.Button(buttons_frame, text="📤 Test Signal",
                                                command=self.test_telegram_signal, width=15)
                self.test_signal_btn.pack(side=tk.LEFT, padx=5)

                self.save_telegram_config_btn = ttk.Button(buttons_frame, text="💾 Save Configuration",
                                                         command=self.save_telegram_config, width=20)
                self.save_telegram_config_btn.pack(side=tk.LEFT, padx=5)

                # Add Load Configuration button
                self.load_telegram_config_btn = ttk.Button(buttons_frame, text="📁 Load Configuration",
                                                         command=self.load_telegram_config, width=20)
                self.load_telegram_config_btn.pack(side=tk.LEFT, padx=5)

                # Status Frame
                status_frame = ttk.LabelFrame(scrollable_frame, text="📊 Status", padding=10)
                status_frame.pack(fill=tk.X, padx=10, pady=5)

                self.telegram_status_text = tk.Text(status_frame, height=8, width=80, bg='#1a1e3a',
                                                  fg='#e0e0e0', font=('Courier', 9))
                self.telegram_status_text.pack(fill=tk.BOTH, expand=True)

                # Signal Format Info
                info_frame = ttk.LabelFrame(scrollable_frame, text="ℹ️ Signal Format Information", padding=10)
                info_frame.pack(fill=tk.X, padx=10, pady=5)

                info_text = """
🔵 OPEN POSITION Signal Format:
• Timestamp: [Date/Time]
• Open Entry: [Price]
• Margin Level: [Percentage]%
• Balance: $[Amount]
• Equity: $[Amount]
• Free Margin: $[Amount]

🔴 CLOSE POSITION Signal Format:
• Timestamp: [Date/Time]
• Close Entry: [Price]
• Margin Level: [Percentage]%
• Balance: $[Amount]
• Equity: $[Amount]
• Free Margin: $[Amount]
• Total Lot Today: [Volume]
                """
                info_label = ttk.Label(info_frame, text=info_text, font=('Segoe UI', 9),
                                     justify=tk.LEFT, background='#1a1e3a', foreground='#e0e0e0')
                info_label.pack(fill=tk.X)

                # Initial status
                self.update_telegram_status("Ready - Select a bot and configure Telegram settings")

                # Update bot selector with current bots
                self.update_telegram_bot_selector()
                
            except Exception as e:
                self.log_message(f"Build telegram tab error: {e}", "ERROR")
                import traceback
                traceback.print_exc()

        def on_telegram_bot_selected(self, event=None):
            """Handle bot selection for telegram configuration"""
            try:
                selected_bot = self.telegram_bot_selector.get()
                if selected_bot and selected_bot in self.bots:
                    # Load existing telegram config for this bot from bot's config
                    bot_config = self.bots[selected_bot]['config']
                    telegram_config = bot_config.get('telegram', {})

                    self.telegram_token_var.set(telegram_config.get('token', ''))
                    self.telegram_chat_ids_var.set(','.join(telegram_config.get('chat_ids', [])))

                    # Create TelegramBot instance if config exists
                    token = telegram_config.get('token', '')
                    chat_ids = telegram_config.get('chat_ids', [])
                    if token and chat_ids:
                        if selected_bot not in self.telegram_bots:
                            self.telegram_bots[selected_bot] = TelegramBot(token, chat_ids)
                        else:
                            self.telegram_bots[selected_bot] = TelegramBot(token, chat_ids)

                    self.update_telegram_status(f"Loaded configuration for bot: {selected_bot}")
                else:
                    self.telegram_token_var.set('')
                    self.telegram_chat_ids_var.set('')
                    self.update_telegram_status("No bot selected")
            except Exception as e:
                self.log_message(f"Bot selection error: {e}", "ERROR")

        def test_telegram_token(self):
            """Test Telegram bot token connection"""
            try:
                token = self.telegram_token_var.get().strip()
                if not token:
                    messagebox.showerror("Error", "Please enter a bot token first!")
                    return

                self.update_telegram_status("Testing token connection...")

                # Create temporary bot to test token
                import asyncio
                from telegram import Bot

                async def test_token():
                    try:
                        bot = Bot(token=token)
                        bot_info = await bot.get_me()
                        self.update_telegram_status(f"✅ Token valid!\nBot: @{bot_info.username}\nName: {bot_info.first_name}")
                        messagebox.showinfo("Success", f"Token connection successful!\n\nBot: @{bot_info.username}")
                    except Exception as e:
                        error_msg = f"❌ Token invalid: {str(e)}"
                        self.update_telegram_status(error_msg)
                        messagebox.showerror("Error", error_msg)

                # Run async test
                asyncio.run(test_token())

            except Exception as e:
                error_msg = f"Test failed: {str(e)}"
                self.update_telegram_status(error_msg)
                messagebox.showerror("Error", error_msg)

        def test_telegram_signal(self):
            """Test sending signal to configured chat IDs"""
            try:
                token = self.telegram_token_var.get().strip()
                chat_ids_str = self.telegram_chat_ids_var.get().strip()

                if not token:
                    messagebox.showerror("Error", "Please enter a bot token first!")
                    return

                if not chat_ids_str:
                    messagebox.showerror("Error", "Please enter chat IDs first!")
                    return

                chat_ids = [id.strip() for id in chat_ids_str.split(',') if id.strip()]

                if not chat_ids:
                    messagebox.showerror("Error", "No valid chat IDs found!")
                    return

                self.update_telegram_status("Sending test signal...")

                # Create test signal message
                test_message = f"""🧪 TEST SIGNAL

🤖 Bot: {self.telegram_bot_selector.get() or 'Unknown'}
🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This is a test message from Aventa HFT Pro 2026"""

                import asyncio
                from telegram import Bot

                async def send_test():
                    try:
                        bot = Bot(token=token)
                        success_count = 0

                        for chat_id in chat_ids:
                            try:
                                await bot.send_message(chat_id=chat_id, text=test_message)
                                success_count += 1
                            except Exception as e:
                                self.update_telegram_status(f"Failed to send to {chat_id}: {str(e)}")

                        if success_count > 0:
                            self.update_telegram_status(f"✅ Test signal sent successfully to {success_count}/{len(chat_ids)} chat(s)")
                            messagebox.showinfo("Success", f"Test signal sent to {success_count} chat(s)!")
                        else:
                            self.update_telegram_status("❌ Failed to send to any chats")
                            messagebox.showerror("Error", "Failed to send to any chats")

                    except Exception as e:
                        error_msg = f"❌ Send failed: {str(e)}"
                        self.update_telegram_status(error_msg)
                        messagebox.showerror("Error", error_msg)

                # Run async send
                asyncio.run(send_test())

            except Exception as e:
                error_msg = f"Test signal failed: {str(e)}"
                self.update_telegram_status(error_msg)
                messagebox.showerror("Error", error_msg)

        def save_telegram_config(self):
            """Save Telegram configuration for selected bot"""
            try:
                selected_bot = self.telegram_bot_selector.get()
                if not selected_bot or selected_bot not in self.bots:
                    messagebox.showerror("Error", "Please select a bot first!")
                    return

                token = self.telegram_token_var.get().strip()
                chat_ids_str = self.telegram_chat_ids_var.get().strip()

                if not token:
                    messagebox.showerror("Error", "Please enter a bot token!")
                    return

                if not chat_ids_str:
                    messagebox.showerror("Error", "Please enter chat IDs!")
                    return

                chat_ids = [id.strip() for id in chat_ids_str.split(',') if id.strip()]

                # Load existing config
                config = self.config_manager.load_config(f"{selected_bot.replace(' ', '_')}_config.json")
                if config is None:
                    config = {}

                # Update telegram config
                config['telegram'] = {
                    'token': token,
                    'chat_ids': chat_ids
                }

                # Save config
                self.config_manager.save_config(config, bot_id=selected_bot)

                # Create or update telegram bot instance
                if selected_bot not in self.telegram_bots:
                    self.telegram_bots[selected_bot] = TelegramBot(token, chat_ids)
                else:
                    # Update existing bot
                    self.telegram_bots[selected_bot] = TelegramBot(token, chat_ids)
                
                # Auto-start Telegram bot in background
                try:
                    from telegram_bot_runner import get_bot_runner
                    runner = get_bot_runner()
                    runner.start()  # Start event loop if not running
                    runner.add_bot(selected_bot, self.telegram_bots[selected_bot])
                    self.log_message(f"Telegram bot {selected_bot} started", "SUCCESS")
                except Exception as e:
                    self.log_message(f"Failed to start Telegram bot: {e}", "WARNING")

                # Update bot's config in memory
                if selected_bot in self.bots:
                    self.bots[selected_bot]['config']['telegram'] = {
                        'token': token,
                        'chat_ids': chat_ids
                    }

                self.update_telegram_status(f"✅ Configuration saved for bot: {selected_bot}")
                messagebox.showinfo("Success", f"Telegram configuration saved for {selected_bot}!")

            except Exception as e:
                error_msg = f"Save failed: {str(e)}"
                self.update_telegram_status(error_msg)
                messagebox.showerror("Error", error_msg)

        def load_telegram_config(self):
            """Load Telegram configuration from bot's saved config"""
            try:
                selected_bot = self.telegram_bot_selector.get()
                if not selected_bot or selected_bot not in self.bots:
                    messagebox.showerror("Error", "Please select a bot first!")
                    return

                # Load from bot's config file
                bot_config = self.config_manager.load_config(f"{selected_bot.replace(' ', '_')}_config.json")
                
                if bot_config and 'telegram' in bot_config:
                    telegram_config = bot_config['telegram']
                    
                    # Update GUI variables
                    self.telegram_token_var.set(telegram_config.get('token', ''))
                    
                    chat_ids = telegram_config.get('chat_ids', [])
                    if isinstance(chat_ids, list):
                        self.telegram_chat_ids_var.set(','.join(chat_ids))
                    else:
                        self.telegram_chat_ids_var.set(str(chat_ids))
                    
                    # Update bot's config in memory
                    if selected_bot in self.bots:
                        self.bots[selected_bot]['config']['telegram'] = telegram_config
                    
                    # Create TelegramBot instance if config exists
                    token = telegram_config.get('token', '')
                    chat_ids = telegram_config.get('chat_ids', [])
                    if token and chat_ids:
                        if selected_bot not in self.telegram_bots:
                            self.telegram_bots[selected_bot] = TelegramBot(token, chat_ids)
                        else:
                            self.telegram_bots[selected_bot] = TelegramBot(token, chat_ids)
                    
                        
                        # Auto-start Telegram bot in background
                        try:
                            from telegram_bot_runner import get_bot_runner
                            runner = get_bot_runner()
                            runner.start()  # Start event loop if not running
                            runner.add_bot(selected_bot, self.telegram_bots[selected_bot])
                            self.log_message(f"Telegram bot {selected_bot} started", "SUCCESS")
                        except Exception as e:
                            self.log_message(f"Failed to start Telegram bot: {e}", "WARNING")
                    self.update_telegram_status(f"✅ Configuration loaded for bot: {selected_bot}")
                    messagebox.showinfo("Success", f"Telegram configuration loaded for {selected_bot}!")
                else:
                    messagebox.showwarning("Warning", "No Telegram configuration found for this bot!")

            except Exception as e:
                error_msg = f"Load failed: {str(e)}"
                self.update_telegram_status(error_msg)
                messagebox.showerror("Error", error_msg)

        def update_telegram_status(self, message):
            """Update telegram status display"""
            try:
                if hasattr(self, 'telegram_status_text'):
                    self.telegram_status_text.delete(1.0, tk.END)
                    self.telegram_status_text.insert(tk.END, message)
            except Exception as e:
                pass

        def update_telegram_bot_selector(self):
            """Update the Telegram bot selector dropdown with current bots"""
            try:
                if hasattr(self, 'telegram_bot_selector'):
                    current_selection = self.telegram_bot_selector.get()
                    bot_list = list(self.bots.keys())
                    self.log_message(f"Setting telegram bot selector values to: {bot_list}", "DEBUG")
                    self.telegram_bot_selector['values'] = bot_list
                    
                    # Force GUI update
                    self.root.update_idletasks()
                    
                    # Restore selection if it still exists
                    if current_selection in self.bots:
                        self.telegram_bot_selector.set(current_selection)
                        self.log_message(f"Restored selection: {current_selection}", "DEBUG")
                    elif self.bots:
                        # Select first bot if current selection is invalid
                        first_bot = list(self.bots.keys())[0]
                        self.telegram_bot_selector.set(first_bot)
                        # Load config for the selected bot
                        self.on_telegram_bot_selected()
                        self.log_message(f"Selected first bot: {first_bot}", "DEBUG")
                    else:
                        self.telegram_bot_selector.set('')
                        self.log_message("No bots available, cleared selection", "DEBUG")
                        
                    # Force another GUI update
                    self.root.update_idletasks()
                else:
                    self.log_message("Telegram bot selector not found", "WARNING")
            except Exception as e:
                self.log_message(f"Update telegram bot selector error: {e}", "ERROR")

        def send_telegram_signal(self, bot_id, signal_type, **kwargs):
            """Send trading signal to Telegram for SPECIFIC BOT ONLY"""
            try:
                self.log_message(f"Sending telegram signal for bot {bot_id}: {signal_type}", "INFO")
                
                # ✅ CRITICAL: Check bot exists
                if bot_id not in self.bots:
                    self.log_message(f"❌ Bot {bot_id} does not exist!", "ERROR")
                    return
                
                # ✅ CRITICAL: Check bot has telegram config
                if bot_id not in self.telegram_bots:
                    self.log_message(f"⚠️ No telegram config for bot {bot_id} - signal not sent", "WARNING")
                    return

                # ✅ GET BOT'S SPECIFIC TELEGRAM CONFIG
                bot_telegram = self.telegram_bots[bot_id]
                chat_ids = bot_telegram.allowed_users
                
                if not chat_ids:
                    self.log_message(f"⚠️ Bot {bot_id} has no chat IDs configured - signal not sent", "WARNING")
                    return

                # Format message based on signal type
                if signal_type == 'open_position':
                    message = self.format_open_position_signal(bot_id=bot_id, **kwargs)
                elif signal_type == 'close_position':
                    message = self.format_close_position_signal(bot_id=bot_id, **kwargs)
                elif signal_type == 'clear_all_positions':
                    message = self.format_clear_all_positions_signal(bot_id=bot_id, **kwargs)
                else:
                    self.log_message(f"Unknown signal type: {signal_type}", "ERROR")
                    return

                import asyncio
                import threading
                from telegram import Bot

                async def send_signal():
                    """Send signal to all chat IDs for this specific bot"""
                    try:
                        telegram_bot = Bot(token=bot_telegram.token)
                        for chat_id in chat_ids:
                            try:
                                await telegram_bot.send_message(chat_id=chat_id, text=message)
                                self.log_message(
                                    f"✅ Telegram signal sent to {chat_id} (Bot: {bot_id})",
                                    "SUCCESS"
                                )
                            except Exception as e:
                                self.log_message(
                                    f"❌ Failed to send to {chat_id} for {bot_id}: {str(e)[:100]}",
                                    "ERROR"
                                )
                    except Exception as e:
                        self.log_message(f"Telegram send error for {bot_id}: {e}", "ERROR")

                # Run in background thread to avoid blocking
                def run_async():
                    try:
                        asyncio.run(send_signal())
                    except Exception as e:
                        self.log_message(f"Async error for {bot_id}: {e}", "ERROR")

                thread = threading.Thread(target=run_async, daemon=True, name=f"TelegramSignal-{bot_id}")
                thread.start()
                
                # ✅ UPDATE STATUS with bot identification
                self.update_telegram_status(
                    f"✅ {signal_type.upper()} signal sent to {len(chat_ids)} chat(s) for bot: {bot_id}"
                )

            except Exception as e:
                error_msg = f"❌ Telegram signal error for {bot_id}: {e}"
                self.log_message(error_msg, "ERROR")
                self.update_telegram_status(error_msg)

        def format_open_position_signal(self, bot_id, symbol, order_type, volume, price, sl, tp, balance=None, equity=None, free_margin=None, margin_level=None, total_volume_today=None):
            """Format open position signal message"""
            # Format account info with N/A fallback
            balance_str = f"${balance:.2f}" if balance is not None else "N/A"
            equity_str = f"${equity:.2f}" if equity is not None else "N/A"
            free_margin_str = f"${free_margin:.2f}" if free_margin is not None else "N/A"
            margin_level_str = f"{margin_level:.2f}%" if margin_level is not None else "N/A"
            total_volume_str = f"{total_volume_today:.2f}" if total_volume_today is not None else "N/A"

            return f"""🔵 OPEN POSITION SIGNAL

🤖 Bot: {bot_id}
📊 Symbol: {symbol}
📈 Order Type: {order_type}
📦 Volume: {volume:.2f}
💰 Price: ${price:.5f}
🛡️ Stop Loss: ${sl:.5f}
🎯 Take Profit: ${tp:.5f}

💳 **Account Summary:**
💵 Balance: {balance_str}
📊 Equity: {equity_str}
🆓 Free Margin: {free_margin_str}
📊 Margin Level: {margin_level_str}
📊 Total Lot Today: {total_volume_str}

🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚀 Position opened successfully!"""

        def format_close_position_signal(self, bot_id, symbol, ticket, profit, volume, balance=None, equity=None, free_margin=None, margin_level=None, total_volume_today=None):
            """Format close position signal message (includes account info). Always show account fields (or N/A)."""
            # Format account info with N/A fallback
            balance_str = f"${balance:.2f}" if balance is not None else "N/A"
            equity_str = f"${equity:.2f}" if equity is not None else "N/A"
            free_margin_str = f"${free_margin:.2f}" if free_margin is not None else "N/A"
            margin_level_str = f"{margin_level:.2f}%" if margin_level is not None else "N/A"
            total_volume_str = f"{total_volume_today:.2f}" if total_volume_today is not None else "N/A"

            return f"""🚀 **CLOSE POSITION SIGNAL**

🤖 Bot: {bot_id}
📊 Symbol: {symbol}
🎫 Ticket: {ticket}
💰 Profit: ${profit:.2f}
📈 Volume: {volume:.2f}

💳 **Account Summary:**
💵 Balance: {balance_str}
📊 Equity: {equity_str}
🆓 Free Margin: {free_margin_str}
📊 Margin Level: {margin_level_str}
📊 Total Lot Today: {total_volume_str}

🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        def format_clear_all_positions_signal(self, bot_id, closed_count, total_profit, balance=None, equity=None, free_margin=None, margin_level=None, total_volume_today=None):
            """Format clear all positions signal message"""
            # Format account info with N/A fallback
            balance_str = f"${balance:.2f}" if balance is not None else "N/A"
            equity_str = f"${equity:.2f}" if equity is not None else "N/A"
            free_margin_str = f"${free_margin:.2f}" if free_margin is not None else "N/A"
            margin_level_str = f"{margin_level:.2f}%" if margin_level is not None else "N/A"
            total_volume_str = f"{total_volume_today:.2f}" if total_volume_today is not None else "N/A"

            return f"""🧹 **CLEANSHEET - ALL POSITIONS CLEARED**

🤖 Bot: {bot_id}
✅ Positions Closed: {closed_count}
💰 Total P&L: ${total_profit:.2f}

💳 **Account Summary:**
💵 Balance: {balance_str}
📊 Equity: {equity_str}
🆓 Free Margin: {free_margin_str}
📊 Margin Level: {margin_level_str}
📊 Total Lot Today: {total_volume_str}

🕐 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🎯 All positions successfully cleared!"""

        def build_ml_tab(self):
            """Build ML Models tab"""
            try:
                # Main container
                main_container = ttk.Frame(self.ml_tab)
                main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

                # ✅ ADD: Bot indicator
                bot_indicator_frame = ttk.Frame(main_container)
                bot_indicator_frame.pack(fill=tk.X, pady=(0, 10))

                ttk.Label(
                    bot_indicator_frame, 
                    text="Training for Bot:", 
                    font=('Segoe UI', 10, 'bold')
                ).pack(side=tk.LEFT, padx=5)

                self.ml_active_bot_label = ttk.Label(
                    bot_indicator_frame, 
                    text="None", 
                    font=('Segoe UI', 10, 'bold'), 
                    foreground='#00e676'
                )
                self.ml_active_bot_label.pack(side=tk.LEFT, padx=5)

                # === MODEL TRAINING SECTION ===
                training_frame = ttk.LabelFrame(main_container, text="🤖 Model Training", padding=10)
                training_frame.pack(fill=tk.X, pady=(0, 10))

                # Training controls
                controls_row = ttk.Frame(training_frame)
                controls_row.pack(fill=tk.X, pady=5)

                ttk.Label(controls_row, text="Training Days:", font=('Segoe UI', 10)).pack(side=tk.LEFT, padx=5)
                
                self.training_days_var = tk.StringVar(value="30")
                days_combo = ttk.Combobox(controls_row, textvariable=self.training_days_var, 
                                        values=['7', '14', '30', '60', '90'], width=10, state='readonly')
                days_combo.pack(side=tk.LEFT, padx=5)

                ttk.Button(controls_row, text="🧠 Train Models", command=self.train_ml_models, 
                        style='Start.TButton', width=15).pack(side=tk.LEFT, padx=5)
                
                ttk.Button(controls_row, text="💾 Save Models", command=self.save_ml_models, 
                        width=15).pack(side=tk.LEFT, padx=5)
                
                # ✅ CHANGE: Load folder instead of file
                ttk.Button(controls_row, text="📁 Load Models", command=self.load_ml_models_folder, 
                        width=15).pack(side=tk.LEFT, padx=5)

                # Progress bar
                self.training_progress_var = tk.DoubleVar()
                progress_frame = ttk.Frame(training_frame)
                progress_frame.pack(fill=tk.X, pady=5)
                
                ttk.Label(progress_frame, text="Training Progress:", font=('Segoe UI', 9)).pack(anchor=tk.W)
                self.training_progress = ttk.Progressbar(progress_frame, variable=self.training_progress_var, 
                                                        maximum=100, length=400)
                self.training_progress.pack(fill=tk.X, pady=5)

                # === MODEL STATUS ===
                status_frame = ttk.LabelFrame(main_container, text="📊 Model Status", padding=10)
                status_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

                # Status text
                self.ml_status_text = scrolledtext.ScrolledText(status_frame, wrap=tk.WORD, height=10,
                                                                bg='#1a1e3a', fg='#e0e0e0', font=("Courier", 9))
                self.ml_status_text.pack(fill=tk.BOTH, expand=True)
                self.ml_status_text.tag_config("METRIC", foreground="#00e676")

                # === TRAINING LOGS ===
                logs_frame = ttk.LabelFrame(main_container, text="📝 Training Logs", padding=10)
                logs_frame.pack(fill=tk.BOTH, expand=True)

                self.ml_log_text = scrolledtext.ScrolledText(logs_frame, wrap=tk.WORD, height=15,
                                                            bg='#1a1e3a', fg='#e0e0e0', font=("Courier", 9))
                self.ml_log_text.pack(fill=tk.BOTH, expand=True)
                
                self.ml_log_text.tag_config("INFO", foreground="#00e676")
                self.ml_log_text.tag_config("WARNING", foreground="#ffd600")
                self.ml_log_text.tag_config("ERROR", foreground="#ff1744")
                self.ml_log_text.tag_config("SUCCESS", foreground="#00b0ff")

                # Log initial status
                self.log_ml_message("ML Models tab initialized", "INFO")
                self.log_ml_message("Ready for model training", "INFO")

            except Exception as e:
                self.log_message(f"Build ML tab error: {e}", "ERROR")

        def ml_log(self, message, level="INFO"):
            """Add log to ML status text"""
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_entry = f"[{timestamp}] [{level}] {message}\n"
                if hasattr(self, 'ml_log_text'):
                    self.ml_log_text.insert(tk.END, log_entry, level)
                    self.ml_log_text.see(tk.END)
                # Also log to main log
                self.log_message(message, level)
            except Exception as e:
                print(f"ML logging error: {e}")

        def train_ml_models(self):
            """Train ML models in background thread"""
            try:
                # ✅ FIX:  Validate active bot
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return

                # ✅ FIX: Get symbol FROM BOT CONFIG (not GUI)
                bot = self.bots[self.active_bot_id]
                config = bot['config']
                symbol = config['symbol']  # <-- CRITICAL FIX!
                days = int(self.training_days_var.get())

                self.log_ml_message(f"[{self.active_bot_id}] Starting ML training for {symbol}", "INFO")
                self.log_ml_message(f"Training period: {days} days", "INFO")

                # Check if market is open
                if not mt5.initialize():
                    self.log_ml_message("[ERROR] MT5 not initialized!", "ERROR")
                    messagebox.showerror("Error", "MT5 is not connected!")
                    return

                # Reset progress
                self.training_progress['value'] = 0

                # Run training in background thread
                def training_thread():
                    try:
                        # Import ML predictor
                        from ml_predictor import MLPredictor

                        self.root.after(0, lambda: self.log_ml_message(f"[{self.active_bot_id}] Loading ML Predictor...", "INFO"))
                        self.root.after(0, lambda: self.training_progress.configure(value=10))

                        # ✅ FIX: Create predictor with BOT's config
                        ml_predictor = MLPredictor(symbol, config)

                        self.root.after(0, lambda: self.log_ml_message(f"[{self.active_bot_id}] Downloading market data for {symbol}...", "INFO"))
                        self.root.after(0, lambda: self.training_progress.configure(value=30))

                        # Get historical data
                        import MetaTrader5 as mt5
                        from datetime import datetime, timedelta
                        
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=days)
                        
                        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_date, end_date)
                        
                        if rates is None or len(rates) == 0:
                            self.root.after(0, lambda: self.log_ml_message(f"[ERROR] No data available for {symbol}", "ERROR"))
                            self.root.after(0, lambda: self.training_progress.stop())
                            mt5.shutdown()
                            return
                        
                        self.root.after(0, lambda: self.log_ml_message(f"[{self.active_bot_id}] Downloaded {len(rates)} bars", "SUCCESS"))
                        
                        # Prepare data
                        import pandas as pd
                        df = pd.DataFrame(rates)
                        df['time'] = pd.to_datetime(df['time'], unit='s')
                        
                        # Calculate indicators
                        self.root.after(0, lambda: self.log_ml_message(f"[{self.active_bot_id}] Calculating technical indicators...", "INFO"))
                        
                        # EMA
                        ema_fast = config.get('ema_fast_period', 7)
                        ema_slow = config.get('ema_slow_period', 21)
                        df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
                        df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
                        
                        # RSI
                        rsi_period = config.get('rsi_period', 7)
                        delta = df['close'].diff()
                        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
                        # LANJUTAN LINE 2891:
                        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
                        rs = gain / loss
                        df['rsi'] = 100 - (100 / (1 + rs))
                        
                        # ATR
                        atr_period = config.get('atr_period', 14)
                        high_low = df['high'] - df['low']
                        high_close = np.abs(df['high'] - df['close'].shift())
                        low_close = np.abs(df['low'] - df['close'].shift())
                        ranges = pd.concat([high_low, high_close, low_close], axis=1)
                        true_range = np.max(ranges, axis=1)
                        df['atr'] = true_range.rolling(atr_period).mean()
                        
                        # Momentum
                        momentum_period = config.get('momentum_period', 5)
                        df['momentum'] = df['close'].diff(momentum_period)
                        
                        # Drop NaN
                        df = df.dropna()
                        
                        if len(df) < 100:
                            self.root.after(0, lambda: self.log_ml_message("[ERROR] Insufficient data for training", "ERROR"))
                            self.root.after(0, lambda: self.training_progress.stop())
                            mt5.shutdown()
                            return
                        
                        # Prepare features (X) and target (y)
                        feature_cols = ['ema_fast', 'ema_slow', 'rsi', 'atr', 'momentum', 'open', 'high', 'low', 'close', 'tick_volume']
                        X = df[feature_cols].values
                        
                        # Target:  1 if price goes up, 0 if down
                        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
                        y = df['target'].values[:-1]
                        X = X[:-1]
                        
                        self.root.after(0, lambda: self.log_ml_message(f"[{self.active_bot_id}] Training models with {len(X)} samples...", "INFO"))
                        
                        # Train models
                        results = ml_predictor.train_models(X, y)
                        
                        # Stop progress
                        self.root.after(0, lambda: self.training_progress.stop())
                        
                        # Handle results
                        if results and results.get('status') == 'success':
                            bot['ml_predictor'] = ml_predictor
                            self.root.after(0, lambda: self.log_ml_message(f"✅ {self.active_bot_id} models trained successfully!", "SUCCESS"))
                            
                            # Display metrics
                            metrics = results.get('metrics', {})
                            for model_name, model_metrics in metrics.items():
                                self.root.after(0, lambda m=model_name, mm=model_metrics: self.log_ml_message(
                                    f"  {m}: Train={mm.get('train_score', 0):.3f}, Test={mm.get('test_score', 0):.3f}", "INFO"
                                ))
                        else:
                            self.root.after(0, lambda: self.log_ml_message("❌ Training failed", "ERROR"))
                            
                    except Exception as e:
                        error_msg = str(e)
                        self.root.after(0, lambda: self.log_ml_message(f"❌ Training error: {error_msg}", "ERROR"))
                        import traceback
                        traceback.print_exc()
                    finally:
                        mt5.shutdown()

                threading.Thread(target=training_thread, daemon=True).start()

            except Exception as e:
                self.log_ml_message(f"Start training error: {e}", "ERROR")

        def save_ml_models(self):
            """Save trained ML models to folder"""
            try:
                # ✅ FIX: Get from active bot
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                bot = self.bots[self.active_bot_id]
                
                # Check if bot has trained ml_predictor
                if not bot.get('ml_predictor') or bot['ml_predictor'] is None:
                    messagebox.showwarning("Warning", f"No trained models found for {self.active_bot_id}!\n\nTrain models first.")
                    return
                
                ml_predictor = bot['ml_predictor']
                
                # Check if models exist
                if not hasattr(ml_predictor, 'direction_model') or ml_predictor.direction_model is None:
                    messagebox.showwarning("Warning", "No trained models found!  Train models first.")
                    return
                
                # Ask user to select save folder
                folder_path = filedialog.askdirectory(
                    title=f"Select Folder to Save Models for {self.active_bot_id}",
                    initialdir=os.getcwd()
                )
                
                if not folder_path: 
                    return
                
                # ✅ FIX: Create subfolder with bot name + symbol + timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                symbol = bot['config']['symbol'].replace('.', '_')
                bot_name = self.active_bot_id.replace(' ', '_')
                
                save_folder = os.path.join(
                    folder_path, 
                    f"ml_models_{bot_name}_{symbol}_{timestamp}"
                )
                os.makedirs(save_folder, exist_ok=True)
                
                self.log_ml_message(f"[{self.active_bot_id}] Saving models to:  {save_folder}", "INFO")
                
                # Save models
                success = ml_predictor.save_models(save_folder)
                
                if success:
                    self.log_ml_message(f"✓ Models saved successfully for {self.active_bot_id}!", "SUCCESS")
                    self.log_ml_message(f"  Location: {save_folder}", "INFO")
                    messagebox.showinfo("Success", f"Models saved for {self.active_bot_id}:\n\n{save_folder}")
                else:
                    self.log_ml_message(f"[ERROR] Failed to save models for {self.active_bot_id}", "ERROR")
                    messagebox.showerror("Error", "Failed to save models")
                
            except Exception as e: 
                error_msg = f"Save models error: {str(e)}"
                self.log_ml_message(error_msg, "ERROR")
                messagebox.showerror("Error", error_msg)


        def train_models_gui(self):
            """Train ML models with GUI feedback"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return

                bot = self.bots[self.active_bot_id]
                config = bot['config']
                symbol = config['symbol']
                training_days = int(self.training_days_var.get())

                self.ml_log_message(f"[INFO] Starting ML training for {symbol}")
                self.ml_log_message(f"[INFO] Training period: {training_days} days")

                # Check if market is open
                if not mt5.initialize():
                    self.ml_log_message("[ERROR] MT5 not initialized!", "ERROR")
                    messagebox.showerror("Error", "MT5 is not connected!")
                    return

                # Reset progress
                self.training_progress['value'] = 0

                # Run training in background thread
                def train_thread():
                    try:
                        # Import ML predictor
                        from ml_predictor import MLPredictor

                        self.root.after(0, lambda: self.ml_log_message("[INFO] Loading ML Predictor..."))
                        self.root.after(0, lambda: self.training_progress.configure(value=10))

                        # Create predictor
                        ml_predictor = MLPredictor(symbol, config)

                        self.root.after(0, lambda: self.ml_log_message("[INFO] Downloading market data..."))
                        self.root.after(0, lambda: self.training_progress.configure(value=30))

                        # Train models
                        success = ml_predictor.train_models(training_days)

                        if success:
                            self.root.after(0, lambda: self.training_progress.configure(value=100))
                            self.root.after(0, lambda: self.ml_log_message("[SUCCESS] ✓ Training completed!", "SUCCESS"))
                            self.root.after(0, lambda: self.ml_status_vars['model_loaded'].set("✅ Loaded"))
                            self.root.after(0, lambda: self.ml_status_vars['last_trained'].set(datetime.now().strftime("%Y-%m-%d %H:%M")))
                            self.root.after(0, lambda: self.ml_status_vars['model_accuracy'].set("70%"))  # Example
                            self.root.after(0, lambda: messagebox.showinfo("Success", "ML models trained successfully!"))

                            # Save to bot
                            bot['ml_predictor'] = ml_predictor
                        else:
                            self.root.after(0, lambda: self.ml_log_message("[ERROR] Training failed!", "ERROR"))
                            self.root.after(0, lambda: messagebox.showerror("Error", "Training failed!  Check logs."))

                    except Exception as e:
                        self.root.after(0, lambda: self.ml_log_message(f"[ERROR] {str(e)}", "ERROR"))
                        self.root.after(0, lambda: messagebox.showerror("Error", f"Training error: {e}"))

                # Start training thread
                threading.Thread(target=train_thread, daemon=True).start()

            except Exception as e:
                self.ml_log_message(f"[ERROR] {str(e)}", "ERROR")

        def train_models_async(self):
            """Train ML models in background thread"""
            def train_thread():
                try:
                    symbol = self.ml_symbol_var.get().strip()
                    days = int(self.ml_days_var.get().strip())
                    
                    self.log_message(f"Starting ML training for {symbol}", "INFO")
                    self.log_message(f"Training period: {days} days", "INFO")
                    
                    # Update progress
                    self.root.after(0, lambda: self.ml_progress.start(10))
                    
                    # Load ML Predictor
                    self.log_message("Loading ML Predictor...", "INFO")
                    from ml_predictor import MLPredictor
                    
                    config = self.get_config_from_gui()
                    ml_predictor = MLPredictor(symbol, config)
                    
                    # Download data
                    self.log_message("Downloading market data...", "INFO")
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=days)
                    
                    import MetaTrader5 as mt5
                    if not mt5.initialize():
                        raise Exception("MT5 initialization failed")
                    
                    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_date, end_date)
                    mt5.shutdown()
                    
                    if rates is None or len(rates) == 0:
                        raise Exception("No data downloaded")
                    
                    self.log_message(f"Downloaded {len(rates)} bars", "SUCCESS")
                    
                    # Calculate indicators
                    self.log_message("Calculating technical indicators...", "INFO")
                    import pandas as pd
                    df = pd.DataFrame(rates)
                    
                    # Calculate all indicators
                    df['ema_fast'] = df['close'].ewm(span=7).mean()
                    df['ema_slow'] = df['close'].ewm(span=21).mean()
                    df['rsi'] = self.calculate_rsi(df['close'], 14)
                    df['atr'] = self.calculate_atr(df, 14)
                    df['momentum'] = df['close'].diff(5)
                    
                    # Drop NaN
                    df = df.dropna()
                    
                    # Prepare features (X) and target (y)
                    feature_cols = ['ema_fast', 'ema_slow', 'rsi', 'atr', 'momentum']
                    X = df[feature_cols].values
                    
                    # Target: 1 if price goes up, 0 if down
                    df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
                    y = df['target'].values[:-1]  # Remove last row (no future data)
                    X = X[:-1]  # Match X with y
                    
                    self.log_message(f"Training models with {len(X)} samples...", "INFO")
                    
                    # Train models - PASS X AND y
                    result = ml_predictor.train_models(X, y)
                    
                    # Stop progress
                    self.root.after(0, lambda: self.ml_progress.stop())
                    
                    # Show results
                    if isinstance(result, dict) and result.get('status') == 'success':
                        self.log_message("=" * 50, "SUCCESS")
                        self.log_message("TRAINING COMPLETE!", "SUCCESS")
                        self.log_message("=" * 50, "SUCCESS")

                        # Display metrics
                        if 'metrics' in result:
                            for model_name, metrics in result['metrics'].items():
                                train_acc = metrics.get('train_score', 0) * 100
                                test_acc = metrics.get('test_score', 0) * 100
                                self.log_message(f"{model_name}:", "INFO")
                                self.log_message(f"  Training accuracy: {train_acc:.2f}%", "INFO")
                                self.log_message(f"  Testing accuracy: {test_acc:.2f}%", "INFO")

                        # Update status
                        status_text = f"✓ Models trained successfully!\n"
                        status_text += f"Train samples: {result.get('train_samples', 0)}\n"
                        status_text += f"Test samples: {result.get('test_samples', 0)}\n"
                        status_text += f"Models saved to: ml_models_{symbol}/"

                        self.root.after(0, lambda: self.ml_status_text.config(state=tk.NORMAL))
                        self.root.after(0, lambda: self.ml_status_text.delete(1.0, tk.END))
                        self.root.after(0, lambda: self.ml_status_text.insert(tk.END, status_text))
                        self.root.after(0, lambda: self.ml_status_text.config(state=tk.DISABLED))
                    elif isinstance(result, dict) and result.get('status') == 'error':
                        self.log_message(f"Training failed: {result.get('error')}", "ERROR")
                        self.root.after(0, lambda: self.ml_status_text.config(state=tk.NORMAL))
                        self.root.after(0, lambda: self.ml_status_text.delete(1.0, tk.END))
                        self.root.after(0, lambda: self.ml_status_text.insert(tk.END, f"Training failed: {result.get('error')}"))
                        self.root.after(0, lambda: self.ml_status_text.config(state=tk.DISABLED))
                    else:
                        self.log_message("Training returned invalid result format.", "ERROR")
                        self.root.after(0, lambda: self.ml_status_text.config(state=tk.NORMAL))
                        self.root.after(0, lambda: self.ml_status_text.delete(1.0, tk.END))
                        self.root.after(0, lambda: self.ml_status_text.insert(tk.END, "Training returned invalid result format."))
                        self.root.after(0, lambda: self.ml_status_text.config(state=tk.DISABLED))
                        
                except Exception as e:
                    self.log_message(f"Training error: {e}", "ERROR")
                    self.log_message(f"{type(e).__name__}: {e}", "ERROR")
                    self.root.after(0, lambda: self.ml_progress.stop())
            
            # Helper methods for indicators
            def calculate_rsi(self, prices, period=14):
                """Calculate RSI"""
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                return 100 - (100 / (1 + rs))
            
            def calculate_atr(self, df, period=14):
                """Calculate ATR"""
                high_low = df['high'] - df['low']
                high_close = abs(df['high'] - df['close'].shift())
                low_close = abs(df['low'] - df['close'].shift())
                ranges = pd.concat([high_low, high_close, low_close], axis=1)
                true_range = ranges.max(axis=1)
                return true_range.rolling(period).mean()
            
            # Start training thread
            threading.Thread(target=train_thread, daemon=True).start()


        def load_ml_models_gui(self):
            """Load ML models from disk"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return

                filename = filedialog.askopenfilename(
                    filetypes=[("Pickle files", "*.pkl"), ("All files", "*.*")],
                    title="Load ML Models"
                )

                if filename:
                    bot = self.bots[self.active_bot_id]
                    config = bot['config']

                    from ml_predictor import MLPredictor
                    ml_predictor = MLPredictor(config['symbol'], config)
                    ml_predictor.load_models(filename)

                    bot['ml_predictor'] = ml_predictor

                    self.ml_status_vars['model_loaded'].set("✅ Loaded")
                    self.ml_status_vars['last_trained'].set("Loaded from file")
                    self.ml_log_message(f"[SUCCESS] ✓ Models loaded from:  {filename}", "SUCCESS")
                    messagebox.showinfo("Success", "ML models loaded successfully!")

            except Exception as e:
                self.ml_log_message(f"[ERROR] {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Load error: {e}")


        def clear_ml_logs(self):
            """Clear ML training logs"""
            try: 
                if hasattr(self, 'ml_log_text'):
                    self.ml_log_text.delete('1.0', tk.END)
                    self.ml_log_message("[INFO] Logs cleared")
            except Exception as e:
                pass


        def ml_log_message(self, message, level="INFO"):
            """Add message to ML training log"""
            try:
                if hasattr(self, 'ml_log_text'):
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    log_entry = f"[{timestamp}] {message}\n"
                    self.ml_log_text.insert(tk.END, log_entry, level)
                    self.ml_log_text.see(tk.END)
            except Exception as e:
                pass

        def reset_circuit_breaker(self):
            """Reset circuit breaker manually"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return

                bot = self.bots[self.active_bot_id]

                if bot['risk_manager']:
                    bot['risk_manager'].circuit_breaker_triggered = False
                    self.circuit_breaker_status.set("✅ INACTIVE - Trading Allowed")
                    self.circuit_breaker_reason.set("Manually reset")
                    self.add_risk_event(f"{self.active_bot_id} circuit breaker manually reset", "INFO")
                    self.log_message(f"✓ {self.active_bot_id} circuit breaker reset", "SUCCESS")

            except Exception as e:
                self.log_message(f"Reset circuit breaker error: {e}", "ERROR")


        def manual_trigger_cb(self):
            """Manually trigger circuit breaker"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return

                bot = self.bots[self.active_bot_id]

                if bot['risk_manager']:
                    bot['risk_manager'].circuit_breaker_triggered = True
                    self.circuit_breaker_status.set("🚨 ACTIVE - Trading Halted")
                    self.circuit_breaker_reason.set("Manually triggered")
                    self.add_risk_event(f"⚠️ {self.active_bot_id} circuit breaker manually triggered", "WARNING")
                    self.log_message(f"⚠️ {self.active_bot_id} circuit breaker triggered", "WARNING")

            except Exception as e:
                self.log_message(f"Manual trigger error: {e}", "ERROR")

        def calculate_rsi(self, prices, period=14):
            """Calculate RSI"""
            import pandas as pd
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))

        def calculate_atr(self, df, period=14):
            """Calculate ATR"""
            import pandas as pd
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = ranges.max(axis=1)
            return true_range.rolling(period).mean()


        def clear_risk_events(self):
            """Clear risk events log"""
            try:
                if hasattr(self, 'risk_events_text'):
                    self.risk_events_text.delete('1.0', tk.END)
                    self.add_risk_event("Risk events log cleared", "INFO")
            except Exception as e:
                pass

        
        def load_ml_models_folder(self):
            """Load trained ML models from saved folder - hasil training sebelumnya"""
            try:
                # ✅ FIX: Get from active bot
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return
                
                bot = self.bots[self.active_bot_id]
                config = bot['config']
                symbol = config['symbol']
                
                # Ask user to select folder dengan saved models
                folder_path = filedialog.askdirectory(
                    title=f"Select Saved Models Folder for {self.active_bot_id}",
                    initialdir=os.getcwd()
                )
                
                if not folder_path:
                    return
                
                self.log_ml_message(f"[{self.active_bot_id}] Loading models from: {folder_path}", "INFO")
                
                # Check if folder contains required files
                required_files = ['direction_model.pkl', 'confidence_model.pkl', 'scaler.pkl']
                missing_files = []
                
                for file in required_files: 
                    file_path = os.path.join(folder_path, file)
                    if not os.path.exists(file_path):
                        missing_files.append(file)
                
                if missing_files: 
                    error_msg = f"Missing files: {', '.join(missing_files)}"
                    self.log_ml_message(f"[ERROR] {error_msg}", "ERROR")
                    messagebox.showerror("Error", error_msg)
                    return
                
                # ✅ Import ML predictor
                from ml_predictor import MLPredictor
                
                self.log_ml_message(f"[{self.active_bot_id}] Initializing ML Predictor for {symbol}...", "INFO")
                ml_predictor = MLPredictor(symbol, config)
                
                # ✅ Load models from folder
                self.log_ml_message(f"[{self.active_bot_id}] Loading trained models...", "INFO")
                success = ml_predictor.load_models(folder_path)
                
                if success and ml_predictor.is_trained:
                    # ✅ Store ML predictor di bot
                    bot['ml_predictor'] = ml_predictor
                    
                    self.log_ml_message(f"[SUCCESS] ✅ All models loaded successfully for {self.active_bot_id}!", "SUCCESS")
                    self.log_ml_message(f"  Bot: {self.active_bot_id}", "INFO")
                    self.log_ml_message(f"  Symbol: {symbol}", "INFO")
                    self.log_ml_message(f"  Models loaded from: {folder_path}", "INFO")
                    self.log_ml_message(f"  Model Status: READY FOR USE", "SUCCESS")
                    self.log_ml_message(f"  ✓ direction_model.pkl", "INFO")
                    self.log_ml_message(f"  ✓ confidence_model.pkl", "INFO")
                    self.log_ml_message(f"  ✓ scaler.pkl", "INFO")
                    
                    # Update UI status
                    self.update_ml_status_display()
                    
                    messagebox.showinfo("Success", 
                        f"✅ Models loaded successfully!\n\n"
                        f"Bot: {self.active_bot_id}\n"
                        f"Symbol: {symbol}\n\n"
                        f"Models siap digunakan untuk:\n"
                        f"• Backtest dengan ML prediction\n"
                        f"• Live trading\n"
                        f"• Strategy validation"
                    )
                else:
                    self.log_ml_message(f"[ERROR] Failed to load models or models not ready", "ERROR")
                    messagebox.showerror("Error", "Failed to load models or models are not valid")
                
            except Exception as e: 
                error_msg = f"Load models error: {str(e)}"
                self.log_ml_message(f"[ERROR] {error_msg}", "ERROR")
                messagebox.showerror("Error", error_msg)
        
        def display_model_info(self, save_dir, accuracy, samples, bot_name=None, symbol=None):
            """Display loaded model information with FULL METRICS"""
            try:
                # ✅ FIX: Get actual training results from bot
                bot = self.bots.get(self.active_bot_id)
                
                # Build metrics display
                metrics_text = ""
                
                if bot and bot.get('ml_predictor'):
                    ml = bot['ml_predictor']
                    
                    # Check if training stats exist
                    if hasattr(ml, 'training_stats') and ml.training_stats:
                        stats = ml.training_stats
                        model_type = stats.get('model_type', 'Unknown')
                        metrics_text = f"""
        📈 Direction Model ({model_type}):
        • Training Accuracy: {stats.get('direction_train_acc', 0)*100:.2f}%
        • Testing Accuracy:   {stats.get('direction_test_acc', 0)*100:.2f}%

        📈 Confidence Model ({model_type}):
        • Training Accuracy: {stats.get('confidence_train_acc', 0)*100:.2f}%
        • Testing Accuracy:  {stats.get('confidence_test_acc', 0)*100:.2f}%

        📦 Training Samples: {stats.get('train_samples', 0):,}
        📦 Testing Samples:   {stats.get('test_samples', 0):,}
        """
                    else:
                        # Fallback to generic display
                        metrics_text = f"""
        📈 Direction Predictor:  ✓ Trained
        📈 Confidence Model:    ✓ Trained
        📐 Feature Scaler:      ✓ Ready

        📊 Average Accuracy:  {accuracy*100:.1f}%
        📦 Training Samples: {samples:,}
        """
                else:
                    metrics_text = f"""
        📈 Direction Predictor: ✓ Trained
        📈 Confidence Model:    ✓ Trained
        📐 Feature Scaler:      ✓ Ready

        📊 Average Accuracy: {accuracy*100:.1f}%
        📦 Training Samples: {samples:,}
        """
                
                # ✅ ADD:  Bot info
                bot_info = f"🤖 Bot: {bot_name}\n📊 Symbol: {symbol}\n\n" if bot_name and symbol else ""
                
                status_text = f"""
        ╔══════════════════════════════════════╗
        ║   TRAINING COMPLETED SUCCESSFULLY    ║
        ╚══════════════════════════════════════╝

        {bot_info}{metrics_text}
        📁 Saved to: {save_dir}
        🕐 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Status: Models ready for prediction 🚀

        💡 Next steps: 
        1.Enable "ML Predictions" in Control Panel
        2.Start trading to use ML predictions

        ⚠️ Note: Each bot has independent ML models
        """
                
                if hasattr(self, 'ml_status_text'):
                    self.ml_status_text.delete(1.0, tk.END)
                    self.ml_status_text.insert(tk.END, status_text)
                else:
                    self.log_message("⚠️ ml_status_text not found", "WARNING")
                
            except Exception as e:
                self.log_message(f"Display model info error: {e}", "ERROR")
                import traceback
                traceback.print_exc()

        def update_ml_status_display(self):
            """Update ML status display when bot changes"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    return
                
                bot = self.bots[self.active_bot_id]
                symbol = bot['config']['symbol']
                enable_ml = bot['config'].get('enable_ml', False)
                
                # Check if bot has trained ML models
                if bot.get('ml_predictor') and bot['ml_predictor'].is_trained:
                    ml = bot['ml_predictor']
                    
                    # Status based on enable_ml setting
                    if enable_ml:
                        ml_status_line = "🤖 ML Status:       ✅ ENABLED & TRAINED (Active)"
                        ml_status_color = "#00e676"  # Green
                    else:
                        ml_status_line = "🤖 ML Status:       ⚠️  TRAINED but DISABLED"
                        ml_status_color = "#ffb74d"  # Orange
                    
                    # ✅ FIX: Get training stats if available
                    metrics_text = ""
                    if hasattr(ml, 'training_stats') and ml.training_stats:
                        stats = ml.training_stats
                        model_type = stats.get('model_type', 'ML')
                        metrics_text = f"""
        📈 Direction Model ({model_type}): 
        • Training:   {stats.get('direction_train_acc', 0)*100:.2f}%
        • Testing:   {stats.get('direction_test_acc', 0)*100:.2f}%

        📈 Confidence Model ({model_type}): 
        • Training:  {stats.get('confidence_train_acc', 0)*100:.2f}%
        • Testing:   {stats.get('confidence_test_acc', 0)*100:.2f}%

        📊 Samples:  Train={stats.get('train_samples', 0):,}, Test={stats.get('test_samples', 0):,}
        """
                    else:
                        metrics_text = """
        📈 Direction Model:  ✓ Trained
        📈 Confidence Model: ✓ Trained
        """
                    
                    status_text = f"""
        ╔══════════════════════════════════════╗
        ║   ML MODELS STATUS                   ║
        ╚══════════════════════════════════════╝

        🤖 Bot: {self.active_bot_id}
        📊 Symbol: {symbol}
        {ml_status_line}

        {metrics_text}
        {("✅ Ready for prediction!" if enable_ml else "⚠️  Enable ML in Control Panel to use predictions")}

        💡 This bot has its own trained models
        independent from other bots.
        """
                else:
                    if enable_ml:
                        # ML enabled but not trained
                        status_text = f"""
        ╔══════════════════════════════════════╗
        ║   ML MODELS STATUS                   ║
        ╚══════════════════════════════════════╝

        🤖 Bot: {self.active_bot_id}
        📊 Symbol: {symbol}

        ⚠️  ML PREDICTION ENABLED BUT NOT TRAINED!

        🚨 WARNING: All trading signals will be REJECTED
           until the model is trained!

        To train models immediately:  
        1. Click "🧠 Train Models" button
        2. Wait for training to complete
        3. Models will be ready for trading

        ⏰ Training typically takes 5-15 minutes
           depending on data availability.

        Each bot has independent ML models.
        """
                    else:
                        # ML not enabled
                        status_text = f"""
        ╔══════════════════════════════════════╗
        ║   ML MODELS STATUS                   ║
        ╚══════════════════════════════════════╝

        🤖 Bot: {self.active_bot_id}
        📊 Symbol: {symbol}

        ⚫ ML Prediction DISABLED

        No trained models for this bot.

        To enable ML Prediction:  
        1. Go to 'Control Panel' tab
        2. Check "Enable ML Predictions"
        3. Go to 'ML Training' tab
        4. Click "🧠 Train Models"
        5. Wait for training to complete
        6. Start trading

        Note: When ML is enabled, ALL trading
        decisions will be assisted by ML results!

        Each bot has independent ML models.
        """
                
                if hasattr(self, 'ml_status_text'):
                    self.ml_status_text.delete(1.0, tk.END)
                    self.ml_status_text.insert(tk.END, status_text)
                
            except Exception as e:
                self.log_message(f"Update ML status error: {e}", "ERROR")

        def reset_risk_display(self):
            """Reset risk displays to zero"""
            try:
                if hasattr(self, 'risk_vars'):
                    self.risk_vars['current_exposure'].set("$0.00")
                    self.risk_vars['position_count'].set("0")
                    self.risk_vars['daily_pnl'].set("$0.00")
                    self.risk_vars['daily_pnl_pct'].set("0.0%")
                    self.risk_vars['daily_trades'].set("0")
                    self.risk_vars['trades_pct'].set("0.0%")
                    self.risk_vars['drawdown'].set("0.0%")
                    self.risk_vars['max_drawdown_today'].set("0.0%")  # ✅ NEW: Reset max drawdown today
                    self.risk_vars['risk_level'].set("LOW")
            except Exception as e:
                pass

        def update_ml_status(self):
            """Update ML status display after loading models"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    return
                
                bot = self.bots[self.active_bot_id]
                
                if bot.get('ml_predictor') and bot['ml_predictor'].is_trained:
                    ml = bot['ml_predictor']
                    
                    # Build status text
                    status_text = f"""
        ╔══════════════════════════════════════╗
        ║   ML MODELS LOADED SUCCESSFULLY      ║
        ╚══════════════════════════════════════╝

        📊 Direction Model: ✓ Loaded
        📊 Confidence Model: ✓ Loaded  
        📊 Scaler:  ✓ Loaded

        🕐 Loaded at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Status: Ready for prediction 🚀

        💡 Next steps: 
        1.Enable "ML Predictions" in Control Panel
        2.Start trading to use ML predictions
        """
                    
                    if hasattr(self, 'ml_status_text'):
                        self.ml_status_text.delete(1.0, tk.END)
                        self.ml_status_text.insert(tk.END, status_text)
                    
                    self.log_ml_message("✓ ML status display updated", "SUCCESS")
                else:
                    self.log_ml_message("⚠️ No trained models found in bot", "WARNING")
                    
            except Exception as e:
                self.log_ml_message(f"Update ML status error: {e}", "ERROR")

        def update_pc_performance(self):
            """Update PC performance metrics (called every 1 second) - FIXED VERSION"""
            try:
                import psutil
                
                # === CPU ===
                try: 
                    cpu_pct = psutil.cpu_percent(interval=0.1)
                    if hasattr(self, 'cpu_label') and self.cpu_label.winfo_exists():
                        self.cpu_label.config(text=f"CPU: {cpu_pct:.1f}%")
                except Exception as e: 
                    if hasattr(self, 'cpu_label'):
                        self.cpu_label.config(text="CPU: Error")
                
                # === RAM (FIXED FORMATTING) ===
                try:
                    ram = psutil.virtual_memory()
                    ram_used_gb = ram.used / (1024**3)
                    ram_total_gb = ram.total / (1024**3)
                    ram_percent = ram.percent
                    
                    if hasattr(self, 'ram_label') and self.ram_label.winfo_exists():
                        # Build string safely without f-string interpolation issues
                        ram_text = "RAM: {:.1f}% ({:.1f}/{:.1f} GB)".format(
                            ram_percent, ram_used_gb, ram_total_gb
                        )
                        self.ram_label.config(text=ram_text)
                except Exception as e: 
                    if hasattr(self, 'ram_label'):
                        self.ram_label.config(text="RAM: Error")
                    print(f"RAM Error: {e}")  # Debug print
                
                # === GPU ===
                try: 
                    import GPUtil
                    gpus = GPUtil.getGPUs()
                    if hasattr(self, 'gpu_label') and self.gpu_label.winfo_exists():
                        if gpus:
                            gpu = gpus[0]
                            gpu_load = gpu.load * 100
                            gpu_temp = gpu.temperature
                            gpu_text = "GPU: {:.1f}% ({}°C)".format(gpu_load, int(gpu_temp))
                            self.gpu_label.config(text=gpu_text)
                        else: 
                            self.gpu_label.config(text="GPU: Not found")
                except ImportError:
                    if hasattr(self, 'gpu_label'):
                        self.gpu_label.config(text="GPU: N/A")
                except Exception:  
                    if hasattr(self, 'gpu_label'):
                        self.gpu_label.config(text="GPU: Error")
                
                # === NETWORK (DEBUG VERSION) ===
                try:  
                    if hasattr(self, 'net_label') and self.net_label.winfo_exists():
                        if self._prev_net_counters is None:  
                            # First run - initialize counters
                            self._prev_net_counters = psutil.net_io_counters()
                            self._prev_net_time = datetime.now()
                            self.net_label.config(text="Network:  Starting...")
                        else:
                            current_counters = psutil.net_io_counters()
                            current_time = datetime.now()
                            
                            time_diff = (current_time - self._prev_net_time).total_seconds()
                            
                            if time_diff > 0.5:  # Only update if > 0.5 seconds passed
                                # Calculate bytes difference
                                bytes_sent_diff = current_counters.bytes_sent - self._prev_net_counters.bytes_sent
                                bytes_recv_diff = current_counters.bytes_recv - self._prev_net_counters.bytes_recv
                                
                                # Convert to KB/s
                                sent_speed_kbs = (bytes_sent_diff / 1024) / time_diff
                                recv_speed_kbs = (bytes_recv_diff / 1024) / time_diff
                                
                                # Format display safely
                                if (sent_speed_kbs + recv_speed_kbs) > 1024:
                                    sent_mbs = sent_speed_kbs / 1024
                                    recv_mbs = recv_speed_kbs / 1024
                                    net_text = "Net: {:.2f} {:.2f} MB/s".format(recv_mbs, sent_mbs)
                                else:  
                                    net_text = "Net: {:.1f} {:.1f} KB/s".format(recv_speed_kbs, sent_speed_kbs)
                                
                                self.net_label.config(text=net_text)
                                print(f"✅ Network Update: {net_text}")  # Debug print
                                
                                # Update previous values
                                self._prev_net_counters = current_counters
                                self._prev_net_time = current_time
                except Exception as e:
                    error_msg = f"Network:  Error - {type(e).__name__}"
                    if hasattr(self, 'net_label'):
                        self.net_label.config(text=error_msg)
                    print(f"❌ Network Error Details: {e}")  # Debug print
                    import traceback
                    traceback.print_exc()  # Print full traceback

                # === DISK (DEBUG VERSION) ===
                try: 
                    disk = psutil.disk_usage('/')
                    disk_used_gb = disk.used / (1024**3)
                    disk_total_gb = disk.total / (1024**3)
                    disk_percent = disk.percent
                    
                    if hasattr(self, 'disk_label') and self.disk_label.winfo_exists():
                        # Build string safely
                        disk_text = "Disk: {:.1f} ({:.0f}/{:.0f} GB)".format(
                            disk_percent, disk_used_gb, disk_total_gb
                        )
                        self.disk_label.config(text=disk_text)
                        print(f"✅ Disk Update: {disk_text}")  # Debug print
                except Exception as e:
                    error_msg = f"Disk: Error - {type(e).__name__}"
                    if hasattr(self, 'disk_label'):
                        self.disk_label.config(text=error_msg)
                    print(f"❌ Disk Error Details: {e}")  # Debug print
                    import traceback
                    traceback.print_exc()  # Print full traceback
                
            except ImportError:
                # psutil not installed
                if hasattr(self, 'cpu_label'):
                    self.cpu_label.config(text="CPU: Install psutil")
                if hasattr(self, 'ram_label'):
                    self.ram_label.config(text="RAM: Install psutil")
                if hasattr(self, 'net_label'):
                    self.net_label.config(text="Network: Install psutil")
                if hasattr(self, 'disk_label'):
                    self.disk_label.config(text="Disk: Install psutil")
            except Exception as e:
                # Log error but don't crash
                print(f"PC Performance Update Error: {e}")
            
            finally:
                # Schedule next update (every 1 second)
                if hasattr(self, 'root') and self.root.winfo_exists():
                    self.root.after(1000, self.update_pc_performance)

        def manual_close_all_positions(self):
            """Manually close all positions for active bot"""
            try:
                if not self.active_bot_id or self.active_bot_id not in self.bots:
                    messagebox.showwarning("Warning", "Please select a bot first!")
                    return

                # Initialize MT5 if not already initialized
                if not mt5.initialize():
                    messagebox.showerror("Error", "Failed to initialize MT5 connection!")
                    return

                bot = self.bots[self.active_bot_id]
                magic = bot['config'].get('magic_number', 2026002)
                
                # Confirm with user
                response = messagebox.askyesno(
                    "Confirm Close Positions",
                    f"Close ALL positions for {self.active_bot_id}?\n\n"
                    f"Magic Number: {magic}\n"
                    f"This will close all open positions with this magic number."
                )
                
                if not response:
                    return
                
                # Get positions
                positions = mt5.positions_get(symbol=bot['config']['symbol'])
                
                if not positions:
                    messagebox.showinfo("Info", f"No open positions found for {self.active_bot_id}")
                    return
                
                # Count positions with this magic number
                our_positions = [p for p in positions if p.magic == magic]
                
                if len(our_positions) == 0:
                    messagebox.showinfo("Info", f"No positions with magic {magic} found")
                    return
                
                # Close positions
                closed = 0
                total_profit = 0.0
                
                for position in our_positions:
                    close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
                    
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": position.symbol,
                        "volume": position.volume,
                        "type": close_type,
                        "position": position.ticket,
                        "price": price,
                        "deviation": 20,
                        "magic": magic,
                        "comment": f"{self.active_bot_id}_MANUAL_CLOSE",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_FOK,
                    }
                    
                    result = mt5.order_send(request)
                    
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        closed += 1
                        total_profit += position.profit
                        self.log_message(f"✓ Closed position #{position.ticket}:  ${position.profit:.2f}", "SUCCESS")
                        
                        # Send telegram notification for manual close (include account info)
                        try:
                            account_info = mt5.account_info()
                            if account_info:
                                balance = account_info.balance
                                equity = account_info.equity
                                free_margin = account_info.margin_free
                                margin = account_info.margin
                                margin_level = (equity / margin) * 100 if margin and margin > 0 else 0
                                self.log_message(f"Account info fetched: Balance={balance:.2f}, Equity={equity:.2f}, Free Margin={free_margin:.2f}, Margin Level={margin_level:.2f}%", "INFO")
                            else:
                                self.log_message("MT5 account_info() returned None", "WARNING")
                                balance = equity = free_margin = margin_level = None
                        except Exception as e:
                            self.log_message(f"Failed to get account info: {e}", "ERROR")
                            balance = equity = free_margin = margin_level = None

                        # Use GUI's telegram signal method for proper bot_id handling
                        self.send_telegram_signal(
                            bot_id=self.active_bot_id,
                            signal_type="close_position",
                            symbol=position.symbol,
                            ticket=position.ticket,
                            profit=position.profit,
                            volume=position.volume,
                            balance=balance,
                            equity=equity,
                            free_margin=free_margin,
                            margin_level=margin_level
                        )
                
                # Send summary notification for clear all positions
                if closed > 0:
                    try:
                        # Get updated account info after closing all positions
                        account_info = mt5.account_info()
                        if account_info:
                            balance = account_info.balance
                            equity = account_info.equity
                            free_margin = account_info.margin_free
                            margin = account_info.margin
                            margin_level = (equity / margin) * 100 if margin and margin > 0 else 0
                        
                        # Get total volume traded today
                        try:
                            bot = self.bots.get(self.active_bot_id)
                            if bot and 'risk_manager' in bot:
                                total_volume_today = bot['risk_manager'].get_daily_volume_from_db()
                            else:
                                total_volume_today = 0.0
                        except Exception as e:
                            logger.debug(f"Could not get total volume for telegram: {e}")
                            total_volume_today = 0.0
                        
                        self.send_telegram_signal(
                            bot_id=self.active_bot_id,
                            signal_type="clear_all_positions",
                            closed_count=closed,
                            total_profit=total_profit,
                            balance=balance,
                            equity=equity,
                            free_margin=free_margin,
                            margin_level=margin_level,
                            total_volume_today=total_volume_today
                        )
                    except Exception as e:
                        self.log_message(f"Failed to send clear all positions telegram: {e}", "ERROR")
                
                # Show summary
                messagebox.showinfo(
                    "Positions Closed",
                    f"✓ Closed {closed} positions for {self.active_bot_id}\n\n"
                    f"Total P&L: ${total_profit:.2f}"
                )
                
                self.log_message(f"✓ Manually closed {closed} positions | Total P&L: ${total_profit:.2f}", "SUCCESS")
                
            except Exception as e:
                self.log_message(f"Manual close error: {e}", "ERROR")
                messagebox.showerror("Error", f"Failed to close positions:\n{e}")


# ============================================
# MAIN ENTRY POINT - WITH MANDATORY LICENSE CHECK
# ============================================

if __name__ == "__main__":
    """
    MAIN PROGRAM EXECUTION
    
    ⚠️ CRITICAL: License validation is MANDATORY
    Program CANNOT start without valid license
    No exceptions, no bypass, no continue without license
    """
    
    import traceback
    
    try:
        # Step 1: MANDATORY License Validation (MUST PASS)
        # This is the FIRST thing that runs - before any other code
        try:
            from license_validator import validate_license_or_exit
            
            print("\n" + "="*70)
            print("🔐 ACTIVATING LICENSE VALIDATION")
            print("="*70)
            
            # validate_license_or_exit() will:
            # - Check if license is valid
            # - If not valid, show activation dialog
            # - If still not valid, EXIT THE PROGRAM
            # - It never returns False, it always exits on failure
            validate_license_or_exit()
            
        except ImportError:
            # If license_validator cannot be imported, try old method
            print("⚠️ License validator not available, trying legacy check...")
            if LICENSE_SYSTEM_AVAILABLE:
                if not enforce_license_on_startup():
                    print("❌ License verification failed. Exiting application.")
                    sys.exit(1)
            else:
                print("❌ License system not available. Cannot proceed.")
                sys.exit(1)
        
        except SystemExit:
            # License validation called sys.exit() - let it exit
            raise
        
        # Step 2: GUI Initialization (only reached if license is valid)
        print("\n✅ License validation passed - Initializing GUI...\n")
        
        root = tk.Tk()
        app = HFTProGUI(root)
        
        # Setup global exception handler
        def handle_exception(exc_type, exc_value, exc_traceback):
            """Global exception handler - redirect to GUI logs"""
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            
            # Log to GUI if available
            try:
                if hasattr(app, 'log_message'):
                    app.log_message(f"UNCAUGHT EXCEPTION:\n{error_msg}", "ERROR")
            except:
                pass
        
        sys.excepthook = handle_exception
        
        # Step 3: Start GUI event loop
        print("🚀 Starting GUI event loop...")
        root.mainloop()
        
    except SystemExit as e:
        # License validation or other critical failure
        print(f"🛑 Program exit: {e}")
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ APPLICATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
    
    except KeyboardInterrupt:
        print("\n⚠️ Program interrupted by user")
    
    finally:
        print("\n🛑 Program terminated.")