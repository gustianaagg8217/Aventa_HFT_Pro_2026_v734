"""
Aventa HFT Pro 2026 - Ultra Low Latency Trading Engine
Advanced High-Frequency Trading System for MetaTrader 5
Created: December 2025
"""

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import time
import threading
import logging
from queue import Queue, PriorityQueue
import json
# Add these imports at the top
from thread_safety import rate_limit
from account_cache import AccountCache
from performance_utils import cache_with_ttl

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ✅ ADD THIS:  Import fast indicators
try:
    from fast_indicators import (
        ema_fast, 
        rsi_fast, 
        atr_fast, 
        momentum_fast,
        bollinger_bands_fast
    )
    FAST_INDICATORS_AVAILABLE = True
    logger.info("✓ Fast indicators (Numba) loaded successfully")
except ImportError: 
    FAST_INDICATORS_AVAILABLE = False
    logger.warning("⚠️ Fast indicators not available - using slower pandas methods")


@dataclass
class TickData:
    """Ultra-fast tick data structure"""
    timestamp: float
    bid: float
    ask: float
    last: float
    volume: int
    spread: float
    
    def __post_init__(self):
        self.mid_price = (self.bid + self.ask) / 2


@dataclass
class OrderFlowData:
    """Order flow analysis data"""
    timestamp: float
    buy_volume: float
    sell_volume: float
    delta: float
    cumulative_delta: float
    imbalance_ratio: float


@dataclass
class Signal:
    """Trading signal with priority"""
    timestamp: float
    signal_type: str  # 'BUY', 'SELL', 'CLOSE'
    strength: float
    price: float
    stop_loss: float
    take_profit: float
    volume: float
    reason: str
    
    def __lt__(self, other):
        return self.timestamp < other.timestamp


class UltraLowLatencyEngine:
    """Core HFT engine with microsecond precision"""
    
    def __init__(self, symbol: str, config:  Dict, risk_manager=None, ml_predictor=None, telegram_callback=None):
        # ========================================
        # STEP 1: Initialize critical dependencies FIRST
        # ========================================
        from account_cache import AccountCache
        self.account_cache = AccountCache(ttl=1.0)
        
        # ========================================
        # STEP 2: Basic attributes
        # ========================================
        self.symbol = symbol
        self.config = config
        self.risk_manager = risk_manager
        self.ml_predictor = ml_predictor
        self.telegram_callback = telegram_callback
        
        # ========================================
        # STEP 3: Data structures
        # ========================================
        self.tick_buffer = deque(maxlen=10000)
        self.orderflow_buffer = deque(maxlen=5000)
        self.signal_queue = PriorityQueue(maxsize=1000)
        
        # ========================================
        # STEP 4: Market data
        # ========================================
        self.last_tick:  Optional[TickData] = None
        self.last_bid = 0.0
        self.last_ask = 0.0
        self.symbol_point = 0.0
        self.stops_level = 0
        
        # ========================================
        # STEP 5: Order flow tracking
        # ========================================
        self.cumulative_delta = 0.0
        self.volume_profile = {}
        
        # ========================================
        # STEP 6: Performance metrics
        # ========================================
        self.latency_samples = deque(maxlen=1000)
        self.execution_times = deque(maxlen=1000)
        
        # ========================================
        # STEP 7: State
        # ========================================
        self.is_running = False
        self.position_type = None
        self.position_volume = 0.0
        self.position_price = 0.0
        
        # ========================================
        # STEP 8: Threading
        # ========================================
        self.data_thread = None
        self.execution_thread = None
        self.analysis_thread = None
        
        # ========================================
        # STEP 9: Trading controls
        # ========================================
        self.last_trade_time = 0.0
        self.min_trade_interval = self.config.get("min_trade_interval", 0.3)
        
        # ========================================
        # STEP 10: Performance tracking
        # ========================================
        # ✅ FIX: Get ACTUAL current equity, not hardcoded 10000
        account_info = mt5.account_info()
        if account_info:
            initial_equity = account_info.equity
        else:
            # Fallback: try account_cache
            account_snapshot = self.account_cache.get_info()
            initial_equity = account_snapshot.equity if account_snapshot else 0.0
        
        # Ensure we have a valid starting equity
        if initial_equity <= 0:
            logger.warning("⚠️ Cannot determine initial equity, using config value")
            initial_equity = config.get('initial_balance', 10000.0)
        
        self.peak_equity = initial_equity
        logger.info(f"✓ Initial peak_equity set to ACTUAL current: ${self.peak_equity:.2f}")
        self.signals_generated = 0
        
        # ✅ FIX: Also initialize risk_manager.peak_balance with current balance
        if self.risk_manager:
            account_info = mt5.account_info()
            if account_info:
                self.risk_manager.peak_balance = account_info.balance
                logger.info(f"✓ Risk Manager peak_balance initialized to: ${self.risk_manager.peak_balance:.2f}")
        
        # Daily reset tracking
        self.last_reset_date = datetime.now().date()
        
        # ========================================
        # STEP 11: Bot-specific stats
        # ========================================
        self.bot_trades_today = 0
        self.bot_wins = 0
        self.bot_losses = 0
        self.bot_daily_pnl = 0.0
        
        # ========================================
        # STEP 12: Bot-specific accounting
        # ========================================
        self.bot_initial_balance = config.get('initial_balance', 10000.0)
        self.bot_balance = self.bot_initial_balance
        self.bot_equity = self.bot_initial_balance
        self.bot_peak_balance = self.bot_initial_balance
        
        self.bot_closed_pnl = 0.0
        self.bot_last_sync_time = time.time()

    @staticmethod
    def get_filling_mode(mode_str: str):
        """Convert filling mode string to MT5 constant"""
        mode_map = {
            'FOK': mt5.ORDER_FILLING_FOK,    # Fill or Kill
            'IOC': mt5.ORDER_FILLING_IOC,    # Immediate or Cancel
            'RETURN': mt5.ORDER_FILLING_RETURN  # Return/Market
        }
        mode_upper = mode_str.upper()
        if mode_upper not in mode_map:
            logger.warning(f"⚠️ Mode pengisian '{mode_str}' nggak didukung, pakai FOK aja ya.")
        return mode_map.get(mode_upper, mt5.ORDER_FILLING_FOK)

    def is_trading_session_allowed(self) -> bool:
        """Check if current time is within allowed trading sessions"""
        if not self.config.get('trading_sessions_enabled', True):
            return True  # No restrictions if disabled
        
        from datetime import datetime
        
        # Get current GMT time
        now_gmt = datetime.utcnow()
        current_hour = now_gmt.hour
        current_minute = now_gmt.minute
        current_time_minutes = current_hour * 60 + current_minute
        
        sessions_allowed = []
        
        # Check London Session (08:00-16:30 GMT)
        if self.config.get('london_session_enabled', True):
            london_start = self._time_to_minutes(self.config.get('london_start', '08:00'))
            london_end = self._time_to_minutes(self.config.get('london_end', '16:30'))
            if london_start <= current_time_minutes <= london_end:
                sessions_allowed.append('LONDON')
        
        # Check NY Session (13:00-21:00 GMT)
        if self.config.get('ny_session_enabled', True):
            ny_start = self._time_to_minutes(self.config.get('ny_start', '13:00'))
            ny_end = self._time_to_minutes(self.config.get('ny_end', '21:00'))
            if ny_start <= current_time_minutes <= ny_end:
                sessions_allowed.append('NY')
        
        # Check Asia Session (22:00-08:00 GMT next day)
        if self.config.get('asia_session_enabled', False):
            asia_start = self._time_to_minutes(self.config.get('asia_start', '22:00'))
            asia_end = self._time_to_minutes(self.config.get('asia_end', '08:00'))
            # Asia session crosses midnight
            if current_time_minutes >= asia_start or current_time_minutes <= asia_end:
                sessions_allowed.append('ASIA')
        
        is_allowed = len(sessions_allowed) > 0
        
        if not is_allowed:
            # Only log once per hour to avoid spam
            if not hasattr(self, '_last_session_log_time'):
                self._last_session_log_time = 0
            
            current_time = time.time()
            if current_time - self._last_session_log_time > 3600:  # Log every hour
                logger.debug(f"⏰ Outside trading sessions at {now_gmt.strftime('%H:%M GMT')}")
                self._last_session_log_time = current_time
        
        return is_allowed
    
    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert HH:MM string to minutes since midnight"""
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            return hours * 60 + minutes
        except:
            return 0
        
    def initialize(self) -> bool:
        """Initialize MT5 connection"""
        try:

            # ✅ CAPTURE INITIAL BALANCE FOR THIS BOT
            account = mt5.account_info()
            if account:
                self.bot_initial_balance = account.balance
                self.bot_peak_balance = account.balance
                logger.info(f"✓ Bot initial balance:  ${self.bot_initial_balance:.2f}")

            # Get MT5 path from config, use default if not provided
            mt5_path = self.config.get('mt5_path', 'C:\\Program Files\\XM Global MT5 - Copy\\terminal64.exe')
            
            if not mt5.initialize(mt5_path):
                logger.error(f"MT5 initialization failed: {mt5.last_error()}")
                logger.error(f"MT5 path: {mt5_path}")
                logger.error(f"  -> Check if MT5 is installed at this location")
                logger.error(f"  -> Update MT5 path in GUI settings if needed")
                return False
            
            # Check symbol
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                logger.error(f"Symbol {self.symbol} not found")
                return False
            
            if not symbol_info.visible:
                if not mt5.symbol_select(self.symbol, True):
                    logger.error(f"Failed to select {self.symbol}")
                    return False
            
            logger.info(f"✓ MT5 berhasil nyambung ke {self.symbol}")
            logger.info(f"  Lokasi MT5: {mt5_path}")
            logger.info(f"  Spread: {symbol_info.spread} poin")
            logger.info(f"  Ukuran tick: {symbol_info.trade_tick_size}")
            logger.info(f"  Nilai tick: {symbol_info.trade_tick_value}")
            logger.info(f"  Point: {symbol_info.point}")
            logger.info(f"  Batas stop: {symbol_info.trade_stops_level} poin")
            logger.info(f"  Mode pengisian: {self.config.get('filling_mode', 'FOK')}")
            logger.info(f"  SL Multiplier: {self.config.get('sl_multiplier', 2.0)}x ATR")
            
            # TP Mode logging
            tp_mode = self.config.get('tp_mode', 'RiskReward')
            if tp_mode == 'FixedDollar':
                tp_amount = self.config.get('tp_dollar_amount', 0.5)
                logger.info(f"  Mode TP: Dollar Tetap (${tp_amount:.2f} per posisi)")
            else:
                logger.info(f"  Mode TP: Risk:Reward (1:{self.config.get('risk_reward_ratio', 2.0)})")
            
            # Store symbol info
            self.symbol_point = symbol_info.point
            self.stops_level = symbol_info.trade_stops_level

            # ✅ ADD THIS: Warmup fast indicators (JIT compilation)
            if FAST_INDICATORS_AVAILABLE: 
                logger.info("🔥 Warming up fast indicators (JIT compilation)...")
                try:
                    # Create dummy data for warmup
                    dummy_data = np.random.random(100) * 2600.0  # Gold-like prices
                    
                    # Warmup all fast indicators (triggers JIT compilation)
                    from fast_indicators import ema_fast, rsi_fast, atr_fast, momentum_fast
                    _ = ema_fast(dummy_data, 7)
                    _ = ema_fast(dummy_data, 21)
                    _ = rsi_fast(dummy_data, 7)
                    _ = atr_fast(dummy_data, dummy_data * 1.001, dummy_data * 0.999, 14)
                    _ = momentum_fast(dummy_data, 5)
                    
                    logger.info("✓ Fast indicators warmed up - JIT compilation complete")
                except Exception as e: 
                    logger.warning(f"⚠️ Warmup failed: {e} - will compile on first use")
            
            # Calculate actual spread in price terms
            spread_price = symbol_info.spread * symbol_info.point
            logger.info(f"  Spread (harga): {spread_price:.5f}")
            
            # Show configured max spread
            max_spread = self.config.get('max_spread', 2.0)
            logger.info(f"  Setting Spread Maksimal: {max_spread:.5f}")
            
            # Calculate minimum SL/TP distance based on stops level
            min_distance = self.stops_level * self.symbol_point
            logger.info(f"  Jarak minimal SL/TP: {min_distance:.5f} ({self.stops_level} poin)")
            
            if spread_price > max_spread:
                logger.warning(f"  ⚠️ Spread sekarang ({spread_price:.5f}) lebih gede dari batas ({max_spread:.5f})")
                logger.warning(f"     Bot nggak bakal entry dulu sampai spread-nya turun!")
                logger.warning(f"     Coba naikin setting 'Max Spread' kalau mau lebih longgar")
            else:
                logger.info(f"  ✓ Spread aman buat trading")
            
            return True
        
            
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def reset_daily_stats(self):
        """Reset daily statistics for this bot"""
        from datetime import datetime
        
        today = datetime.now().date()
        if today > self.last_reset_date:
            logger.info(f"Resetting daily stats for bot - Previous day: {self.last_reset_date}")
            
            # Get current account equity for daily peak reset
            current_equity = self.get_account_equity()
            if current_equity > 0:
                self.peak_equity = current_equity
                logger.info(f"✓ Daily peak equity reset to current: ${self.peak_equity:.2f}")
                
                # ✅ FIX: Also reset risk_manager's peak_balance with current account balance
                if self.risk_manager:
                    account_info = mt5.account_info()
                    if account_info:
                        self.risk_manager.reset_daily_stats(account_info.balance)
                        logger.info(f"✓ Risk Manager peak_balance reset to: ${account_info.balance:.2f}")
            else:
                # Fallback to initial balance if can't get current equity
                self.peak_equity = self.bot_initial_balance
                logger.info(f"✓ Daily peak equity reset to initial: ${self.peak_equity:.2f}")
            
            # Reset bot-specific daily stats
            self.bot_trades_today = 0
            self.bot_daily_pnl = 0.0
            
            self.last_reset_date = today
            logger.info("✓ Daily stats reset complete for bot")
        else:
            logger.debug("Daily stats already reset for today")
    
    def get_tick_ultra_fast(self) -> Optional[TickData]:
        """Ultra-fast tick retrieval with microsecond timestamps"""
        start_time = time.perf_counter()
        
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                return None
            
            tick_data = TickData(
                timestamp=tick.time + tick.time_msc / 1000.0,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                spread=(tick.ask - tick.bid)
            )
            
            # Track latency
            latency = (time.perf_counter() - start_time) * 1000000  # microseconds
            self.latency_samples.append(latency)
            
            return tick_data
            
        except Exception as e:
            logger.error(f"Tick retrieval error: {e}")
            return None
    
    def calculate_order_flow(self, tick: TickData) -> OrderFlowData:
        """Advanced order flow analysis"""
        if self.last_tick is None:
            self.last_tick = tick
            return None
        
        # Determine aggressor
        price_change = tick.last - self.last_tick.last
        volume_delta = 0.0
        
        if price_change > 0:
            # Buy aggressor
            buy_volume = tick.volume
            sell_volume = 0
            volume_delta = tick.volume
        elif price_change < 0:
            # Sell aggressor
            buy_volume = 0
            sell_volume = tick.volume
            volume_delta = -tick.volume
        else:
            # Use bid/ask to determine
            if tick.last >= tick.mid_price:
                buy_volume = tick.volume
                sell_volume = 0
                volume_delta = tick.volume
            else:
                buy_volume = 0
                sell_volume = tick.volume
                volume_delta = -tick.volume
        
        self.cumulative_delta += volume_delta
        
        # Calculate imbalance
        total_volume = buy_volume + sell_volume
        if total_volume > 0:
            imbalance_ratio = (buy_volume - sell_volume) / total_volume
        else:
            imbalance_ratio = 0.0
        
        orderflow = OrderFlowData(
            timestamp=tick.timestamp,
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            delta=volume_delta,
            cumulative_delta=self.cumulative_delta,
            imbalance_ratio=imbalance_ratio
        )
        
        self.last_tick = tick
        return orderflow
    
    def calculate_tick_range_avg(self, prices, period: int):
        """
        Tick Range Average (TRA)
        Pengganti ATR untuk HFT (lebih cepat & relevan)
        """
        if len(prices) < period + 1:
            return None
        diffs = [abs(prices[i] - prices[i-1]) for i in range(-period, 0)]
        return sum(diffs) / len(diffs)

    def analyze_microstructure(self) -> Dict:
        """Analyze market microstructure for HFT opportunities (OPTIMIZED)"""
        if len(self.tick_buffer) < 100:
            return {}

        recent_ticks = list(self.tick_buffer)[-100:]

        # Get config parameters
        ema_fast_period = self.config.get('ema_fast_period', 7)
        ema_slow_period = self.config.get('ema_slow_period', 21)
        rsi_period = self.config.get('rsi_period', 7)
        rsi_overbought = self.config.get('rsi_overbought', 68)
        rsi_oversold = self.config.get('rsi_oversold', 32)
        atr_period = self.config.get('atr_period', 14)
        momentum_period = self.config.get('momentum_period', 5)

        # Spread analysis
        spreads = [t.spread for t in recent_ticks]
        avg_spread = np.mean(spreads)
        spread_volatility = np.std(spreads)

        # Price momentum (ultra-short term)
        prices = np.array([t.mid_price for t in recent_ticks])
        price_change = prices[-1] - prices[0]
        price_velocity = price_change / len(prices)

        # Order flow imbalance
        if len(self.orderflow_buffer) > 0:
            recent_flow = list(self.orderflow_buffer)[-50:]
            avg_delta = np.mean([f.delta for f in recent_flow])
            cumul_delta = recent_flow[-1].cumulative_delta if recent_flow else 0
        else:
            avg_delta = 0
            cumul_delta = 0

        # Volatility estimation
        returns = np.diff(prices)
        volatility = np.std(returns) if len(returns) > 0 else 0

        # === OPTIMIZED INDICATOR CALCULATIONS ===
        use_fast = FAST_INDICATORS_AVAILABLE and len(prices) >= max(ema_slow_period, rsi_period, atr_period)
        
        if use_fast:
            # Use Numba-optimized calculations (ULTRA-FAST)
            try:
                # Import inside try block to catch any issues
                from fast_indicators import ema_fast, rsi_fast, atr_fast, momentum_fast
                
                # EMA
                ema_fast_values = ema_fast(prices, ema_fast_period)
                ema_slow_values = ema_fast(prices, ema_slow_period)
                ema_fast_current = float(ema_fast_values[-1])
                ema_slow_current = float(ema_slow_values[-1])
                
                # RSI
                rsi_values = rsi_fast(prices, rsi_period)
                rsi = float(rsi_values[-1])
                
                # ATR (using actual high/low if available, else approximate)
                if hasattr(recent_ticks[0], 'high') and hasattr(recent_ticks[0], 'low'):
                    high_prices = np.array([t.high for t in recent_ticks])
                    low_prices = np.array([t.low for t in recent_ticks])
                else:
                    # Approximate from mid_price
                    high_prices = prices * 1.0001
                    low_prices = prices * 0.9999
                
                atr_values = atr_fast(high_prices, low_prices, prices, atr_period)
                atr = float(atr_values[-1])
                
                # Momentum
                momentum_values = momentum_fast(prices, momentum_period)
                momentum = float(momentum_values[-1])
                
                # Track that we used fast method (for debugging)
                if not hasattr(self, '_fast_indicator_count'):
                    self._fast_indicator_count = 0
                self._fast_indicator_count += 1
                
            except Exception as e:
                # Only log first few errors to avoid spam
                if not hasattr(self, '_fallback_error_logged'):
                    logger.warning(f"⚠️ Fast indicator failed, using pandas fallback: {e}")
                    self._fallback_error_logged = True
                
                # Fallback to pandas
                ema_fast_current, ema_slow_current, rsi, atr, momentum = self._calculate_indicators_pandas(
                    prices, ema_fast_period, ema_slow_period, rsi_period, atr_period, momentum_period
                )
        else:
            # Use pandas from the start if conditions not met
            ema_fast_current, ema_slow_current, rsi, atr, momentum = self._calculate_indicators_pandas(
                prices, ema_fast_period, ema_slow_period, rsi_period, atr_period, momentum_period
            )

        return {
            'avg_spread': avg_spread,
            'spread_volatility': spread_volatility,
            'price_velocity': price_velocity,
            'price_change': price_change,
            'avg_delta': avg_delta,
            'cumulative_delta': cumul_delta,
            'volatility': volatility,
            'tick_count': len(recent_ticks),
            'ema_fast':  ema_fast_current,
            'ema_slow': ema_slow_current,
            'rsi': rsi,
            'atr': atr,
            'momentum': momentum,
        }


    def _calculate_indicators_pandas(self, prices, ema_fast_period, ema_slow_period, 
                                    rsi_period, atr_period, momentum_period):
        """Fallback pandas-based indicator calculation"""
        try:
            prices_series = pd.Series(prices)
            
            # EMA
            ema_fast_val = prices_series.ewm(span=ema_fast_period, adjust=False).mean().iloc[-1]
            ema_slow_val = prices_series.ewm(span=ema_slow_period, adjust=False).mean().iloc[-1]
            
            # RSI
            delta = prices_series.diff()
            up = delta.clip(lower=0)
            down = -1 * delta.clip(upper=0)
            roll_up = up.rolling(rsi_period).mean()
            roll_down = down.rolling(rsi_period).mean()
            rs = roll_up / (roll_down + 1e-9)
            rsi_val = 100.0 - (100.0 / (1.0 + rs.iloc[-1]))
            
            # ATR (simplified)
            atr_val = prices_series.rolling(atr_period).std().iloc[-1]
            
            # Momentum
            momentum_val = prices_series.iloc[-1] - prices_series.iloc[-momentum_period]
            
            return ema_fast_val, ema_slow_val, rsi_val, atr_val, momentum_val
            
        except Exception as e:
            logger.error(f"Pandas indicator calculation failed: {e}")
            return np.nan, np.nan, np.nan, np.nan, np.nan
    
    def generate_signal(self, microstructure: Dict) -> Optional[Signal]:
        """Generate trading signal based on microstructure analysis
        
        IMPORTANT: If ML Prediction is ENABLED, ALL signals MUST be assisted by ML results!
        ML is mandatory when enable_ml=True, not optional.
        """
        if not microstructure:
            return None
        
        current_tick = self.last_tick
        if current_tick is None:
            return None
        
        # ============================================
        # CHECK IF ML IS ENABLED AND WARN IF NOT READY
        # ============================================
        enable_ml = self.config.get('enable_ml', False)
        ml_ready = self.ml_predictor is not None and self.ml_predictor.is_trained
        
        if enable_ml and not ml_ready:
            # ML is enabled but not ready - log warning once
            if not hasattr(self, '_ml_not_ready_logged'):
                logger.warning(f"⚠️  ML Prediction ENABLED but model NOT YET TRAINED!")
                logger.warning(f"    Training is required before signals use ML assistance.")
                logger.warning(f"    Please train the model first using the ML Training tab.")
                self._ml_not_ready_logged = True
        
        # Signal generation parameters
        min_delta_threshold = self.config.get('min_delta_threshold', 100)
        min_velocity_threshold = self.config.get('min_velocity_threshold', 0.00001)
        spread_threshold = self.config.get('max_spread', 0.0001)
        
        # Check spread condition with rate-limited logging
        if microstructure['avg_spread'] > spread_threshold:
            self.log_spread_reject(microstructure['avg_spread'], spread_threshold)
            return None
        
        signal_strength = 0.0
        signal_type = None
        reason = []
        
        # --- Ambil indikator dari microstructure ---
        ema_fast = microstructure.get('ema_fast', np.nan)
        ema_slow = microstructure.get('ema_slow', np.nan)
        rsi = microstructure.get('rsi', np.nan)
        atr_val = microstructure.get('atr', np.nan)
        momentum_val = microstructure.get('momentum', np.nan)
        price = current_tick.mid_price if current_tick else np.nan
        rsi_overbought = self.config.get('rsi_overbought', 70)
        rsi_oversold = self.config.get('rsi_oversold', 30)

        # --- Order flow signal ---
        if microstructure['cumulative_delta'] > min_delta_threshold:
            # Tambah filter EMA, RSI, Momentum untuk BUY
            if (
                not np.isnan(ema_fast) and not np.isnan(ema_slow) and not np.isnan(rsi) and not np.isnan(momentum_val)
                and price > ema_fast > ema_slow
                and rsi < rsi_overbought
                and momentum_val > 0
            ):
                signal_strength += 0.4
                signal_type = 'BUY'
                reason.append(f"Delta+ & EMA/RSI/Mom OK: Δ={microstructure['cumulative_delta']:.0f}, EMAf={ema_fast:.2f}, EMAs={ema_slow:.2f}, RSI={rsi:.1f}, Mom={momentum_val:.5f}")
            else:
                reason.append(f"Delta+ but filter fail: EMA/RSI/Mom")
        elif microstructure['cumulative_delta'] < -min_delta_threshold:
            # Tambah filter EMA, RSI, Momentum untuk SELL
            if (
                not np.isnan(ema_fast) and not np.isnan(ema_slow) and not np.isnan(rsi) and not np.isnan(momentum_val)
                and price < ema_fast < ema_slow
                and rsi > rsi_oversold
                and momentum_val < 0
            ):
                signal_strength += 0.4
                signal_type = 'SELL'
                reason.append(f"Delta- & EMA/RSI/Mom OK: Δ={microstructure['cumulative_delta']:.0f}, EMAf={ema_fast:.2f}, EMAs={ema_slow:.2f}, RSI={rsi:.1f}, Mom={momentum_val:.5f}")
            else:
                reason.append(f"Delta- but filter fail: EMA/RSI/Mom")

        # --- Momentum signal (tambahan, tetap pakai price_velocity untuk penguat) ---
        if microstructure['price_velocity'] > min_velocity_threshold:
            signal_strength += 0.3
            if signal_type is None:
                signal_type = 'BUY'
            elif signal_type == 'BUY':
                signal_strength += 0.1
            reason.append(f"Positive momentum: {microstructure['price_velocity']:.6f}")
        elif microstructure['price_velocity'] < -min_velocity_threshold:
            signal_strength += 0.3
            if signal_type is None:
                signal_type = 'SELL'
            elif signal_type == 'SELL':
                signal_strength += 0.1
            reason.append(f"Negative momentum: {microstructure['price_velocity']:.6f}")
        
        # Volatility check
        if microstructure['volatility'] > self.config.get('max_volatility', 0.001):
            signal_strength *= 0.5
            reason.append("High volatility - reduced confidence")
        
        # ============================================
        # ML PREDICTION (MANDATORY IF enable_ml=True)
        # ============================================
        if enable_ml:
            # ML is ENABLED - MUST use ML to assist decision
            if ml_ready:
                # Model is trained and ready
                try:
                    # Prepare features for ML prediction
                    features = self.ml_predictor.prepare_realtime_features(current_tick, microstructure)
                    ml_direction_num, ml_confidence = self.ml_predictor.predict(features)
                    
                    # Convert ML direction: 1 = BUY, 0/-1 = SELL
                    ml_direction = 'BUY' if ml_direction_num == 1 else 'SELL'
                    
                    # Enhance signal strength based on ML prediction
                    if signal_type and ml_direction == signal_type:
                        # ML agrees with technical signal - boost confidence significantly
                        signal_strength = min(1.0, signal_strength + (ml_confidence * 0.4))
                        reason.append(f"✅ ML AGREED: {ml_direction} confidence {ml_confidence:.2f}")
                    elif signal_type and ml_direction != signal_type:
                        # ML disagrees - reduce confidence significantly
                        signal_strength *= (1.0 - ml_confidence * 0.4)
                        reason.append(f"⚠️  ML DISAGREED: Technical {signal_type} vs ML {ml_direction} ({ml_confidence:.2f})")
                    elif not signal_type and ml_confidence > 0.6:
                        # No technical signal but strong ML signal - ACCEPT ML signal
                        signal_type = ml_direction
                        signal_strength = ml_confidence * 0.8  # ML-driven signal, use higher confidence
                        reason.append(f"📊 ML SIGNAL ONLY: {ml_direction} confidence {ml_confidence:.2f}")
                    else:
                        # Weak technical signal or weak ML confidence
                        reason.append(f"📊 ML analyzed: {ml_direction} ({ml_confidence:.2f}) - no override")
                        
                except Exception as e:
                    logger.error(f"❌ ML prediction ERROR: {e}")
                    reason.append(f"ML ERROR: {str(e)}")
            else:
                # ML enabled but model not trained - reject signal with warning
                reason.append("⚠️  ML ENABLED but MODEL NOT TRAINED - signal rejected")
                # Return None to reject all signals until ML is trained
                if not hasattr(self, '_ml_training_required_logged'):
                    logger.error(f"🚨 SIGNAL REJECTION: ML enabled but model not trained!")
                    logger.error(f"   Please train ML model first via ML Training tab!")
                    self._ml_training_required_logged = True
                return None
        else:
            # ML is not enabled - use technical signals only
            reason.append("ML Prediction DISABLED")
        
        # Check if we should close position
        if self.position_type is not None:
            if self.position_type == 'BUY' and signal_type == 'SELL' and signal_strength > 0.6:
                return Signal(
                    timestamp=time.time(),
                    signal_type='CLOSE',
                    strength=signal_strength,
                    price=current_tick.bid,
                    stop_loss=0,
                    take_profit=0,
                    volume=self.position_volume,
                    reason="Reversal signal detected"
                )
            elif self.position_type == 'SELL' and signal_type == 'BUY' and signal_strength > 0.6:
                return Signal(
                    timestamp=time.time(),
                    signal_type='CLOSE',
                    strength=signal_strength,
                    price=current_tick.ask,
                    stop_loss=0,
                    take_profit=0,
                    volume=self.position_volume,
                    reason="Reversal signal detected"
                )
        
        # Generate new signal
        min_strength = self.config.get('min_signal_strength', 0.6)
        
        if signal_type and signal_strength >= min_strength:
            # Calculate SL/TP with minimum distance based on stops level
            atr = microstructure['volatility'] * 10
            
            # Get SL multiplier from config (default 2.0)
            sl_multiplier = self.config.get('sl_multiplier', 2.0)
            
            # Calculate minimum distance based on stops level
            min_distance = self.stops_level * self.symbol_point if self.stops_level > 0 else 0.5
            
            # Ensure SL distance is at least min_distance + some buffer
            sl_distance = max(
                atr * sl_multiplier,  # Use configurable multiplier
                microstructure['avg_spread'] * 5,
                min_distance * 1.2  # 20% buffer above minimum
            )
            
            # Calculate TP based on mode
            tp_mode = self.config.get('tp_mode', 'RiskReward')
            
            if tp_mode == 'FixedDollar':
                # TP based on dollar amount
                tp_dollar = self.config.get('tp_dollar_amount', 0.5)
                volume = self.config.get('default_volume', 0.01)
                
                # Get symbol info for calculation
                symbol_info = mt5.symbol_info(self.symbol)
                if symbol_info and symbol_info.trade_contract_size > 0:
                    # For commodities/metals: Profit = price_diff × volume × contract_size
                    # Therefore: price_diff = profit / (volume × contract_size)
                    contract_size = symbol_info.trade_contract_size
                    tp_distance_raw = tp_dollar / (volume * contract_size)
                    
                    # Ensure TP distance meets minimum required distance
                    if tp_distance_raw < min_distance:
                        tp_distance = min_distance * 1.2  # Use min distance with buffer
                        actual_profit = tp_distance * volume * contract_size
                        logger.warning(f"TP target ${tp_dollar:.2f} too small (needs {tp_distance_raw:.5f}).Using min distance {tp_distance:.5f} (≈${actual_profit:.2f})")
                    else:
                        tp_distance = tp_distance_raw
                        logger.debug(f"TP Mode: FixedDollar (${tp_dollar:.2f}) = {tp_distance:.5f} price distance")
                else:
                    # Fallback to risk:reward if symbol info unavailable
                    tp_distance = sl_distance * self.config.get('risk_reward_ratio', 2.0)
                    logger.warning(f"Failed to get symbol info, using Risk:Reward")
            else:
                # TP based on Risk:Reward ratio (default)
                tp_distance = sl_distance * self.config.get('risk_reward_ratio', 2.0)
            
            if signal_type == 'BUY':
                price = current_tick.ask
                sl = price - sl_distance
                tp = price + tp_distance
            else:
                price = current_tick.bid
                sl = price + sl_distance
                tp = price - tp_distance
            
            logger.debug(f"SL/TP: distance={sl_distance:.5f} (min={min_distance:.5f}), TP distance={tp_distance:.5f}")
            
            # Increment signals generated counter
            self.signals_generated += 1
            
            return Signal(
                timestamp=time.time(),
                signal_type=signal_type,
                strength=signal_strength,
                price=price,
                stop_loss=sl,
                take_profit=tp,
                volume=self.config.get('default_volume', 0.01),
                reason=" | ".join(reason)
            )
        elif signal_type:
            # Signal exists but not strong enough - log occasionally
            if np.random.random() < 0.1:  # Log 10% of weak signals
                logger.warning(f"⚠️ WEAK SIGNAL: {signal_type} | Strength: {signal_strength:.2f} < {min_strength:.2f}")
                logger.warning(f"   Thresholds: Delta={min_delta_threshold} | Velocity={min_velocity_threshold:.6f}")
                logger.warning(f"   Actuals: Delta={microstructure['cumulative_delta']:.0f} | Velocity={microstructure['price_velocity']:.6f}")
        else:
            # No signal type at all - log very occasionally to show thresholds
            if np.random.random() < 0.01:  # 1% of the time
                logger.info(f"🔍 No signal criteria met.Need: Delta>{min_delta_threshold} OR Velocity>{min_velocity_threshold:.6f}")
                logger.info(f"   Current: Delta={microstructure['cumulative_delta']:.0f} | Velocity={microstructure['price_velocity']:.6f}")
        
        return None
    
    def verify_position_exists(self) -> bool:
        """Check if position actually exists in MT5"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None:
                return False
            
            # Check if any position matches our magic number
            magic = self.config.get('magic_number', 2026002)
            for pos in positions:
                if pos.magic == magic:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking position: {e}")
            return False
    
    def execute_signal(self, signal: Signal) -> bool:
        """Execute trading signal with ultra-low latency"""
        start_time = time.perf_counter()
        
        try:
            # ✅ CHECK: Only execute signals within allowed trading sessions
            if not self.is_trading_session_allowed():
                logger.debug(f"⏰ Signal blocked: Outside trading sessions - {signal.signal_type}")
                return False
            
            # For multi-position support, only verify positions exist (don't block new signals)
            if self.position_type and signal.signal_type != 'CLOSE':
                # Verify positions still exist in MT5
                if not self.verify_position_exists():
                    logger.info(f"🔄 All positions closed (SL/TP hit) - Resetting internal state")
                    self.position_type = None
                    self.position_volume = 0.0
                    self.position_price = 0.0
            
            if signal.signal_type == 'CLOSE':
                result = self.close_position()
            elif signal.signal_type == 'BUY':
                result = self.open_position('BUY', signal)
            elif signal.signal_type == 'SELL':
                result = self.open_position('SELL', signal)
            else:
                return False
            
            # Track execution time
            exec_time = (time.perf_counter() - start_time) * 1000  # milliseconds
            self.execution_times.append(exec_time)
            
            if result:
                logger.info(f"✓ Executed {signal.signal_type} | "
                          f"Price: {signal.price:.5f} | "
                          f"Strength: {signal.strength:.2f} | "
                          f"Time: {exec_time:.2f}ms | "
                          f"Reason: {signal.reason}")
            
            return result
            
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return False
    
    def get_total_floating_loss(self) -> float:
        """Calculate total floating loss from all open positions"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            if positions is None or len(positions) == 0:
                return 0.0
            
            magic = self.config.get('magic_number', 2026002)
            total_loss = 0.0
            
            for pos in positions:
                if pos.magic == magic and pos.profit < 0:
                    total_loss += abs(pos.profit)
            
            return total_loss
            
        except Exception as e:
            logger.error(f"Error calculating floating loss: {e}")
            return 0.0
    
    def get_total_floating_profit(self) -> float:
            """
            Calculate total floating profit (all positions, profit+loss) MINUS commission
            
            Returns:
                float: Net floating profit after deducting commission
            """
            try:
                positions = mt5.positions_get(symbol=self.symbol)
                if positions is None or len(positions) == 0:
                    return 0.0
                
                magic = self.config.get('magic_number', 2026002)
                total_profit = 0.0
                position_count = 0
                
                # Sum up all position profits
                for pos in positions:
                    if pos.magic == magic:
                        total_profit += pos.profit
                        position_count += 1
                
                # Deduct commission
                commission_per_trade = float(self.config.get('commission_per_trade', 0.0))
                total_commission = commission_per_trade * position_count
                
                # Net profit = gross profit - commission
                net_profit = total_profit - total_commission
                
                # Log occasionally for debugging (every 100th check)
                if hasattr(self, '_profit_check_counter'):
                    self._profit_check_counter += 1
                else:
                    self._profit_check_counter = 0
                
                if self._profit_check_counter % 100 == 0:
                    logger.debug(f"💰 Floating Profit:  Gross=${total_profit:.2f}, "
                                f"Commission=${total_commission:.2f} ({position_count} pos × ${commission_per_trade:.2f}), "
                                f"Net=${net_profit:.2f}")
                
                return net_profit
                
            except Exception as e: 
                logger.error(f"Error calculating floating profit: {e}")
                return 0.0
    
    def close_all_positions(self, reason:  str = "Target reached") -> int:
        """Close all positions with our magic number"""
        try:
            magic = self.config.get('magic_number', 2026002)
            positions = mt5.positions_get(symbol=self.symbol)
            
            if positions is None or len(positions) == 0:
                return 0
            
            closed_count = 0
            total_profit = 0.0
            total_commission = 0.0  # ✅ Tambahkan tracker komisi
            
            for position in positions:
                if position.magic != magic:
                    continue
                
                # Send close order for this position
                close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(self.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask

                filling_mode_str = self.config.get('filling_mode', 'FOK')
                filling_mode = self.get_filling_mode(filling_mode_str)

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": self.symbol,
                    "volume": position.volume,
                    "type": close_type,
                    "position": position.ticket,
                    "price": price,
                    "deviation": self.config.get('slippage', 20),
                    "magic": self.config.get('magic_number', 2026002),
                    "comment": "AvHFTPro2026_CLOSE",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": filling_mode,
                }

                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    closed_count += 1
                    total_profit += position.profit
                    
                    # ✅ Hitung komisi per posisi
                    commission_per_trade = self.config.get('commission_per_trade', 0.0)
                    total_commission += commission_per_trade
                    
                    logger.info(f"✓ Posisi #{position.ticket} berhasil ditutup: "
                            f"Profit=${position.profit:.2f} | "
                            f"Commission=${commission_per_trade:.2f}")
                    
                    if self.telegram_callback:
                        # Get account info right after position close
                        try:
                            account_info = mt5.account_info()
                            if account_info:
                                balance = account_info.balance
                                equity = account_info.equity
                                free_margin = account_info.margin_free
                                margin = account_info.margin
                                margin_level = (equity / margin) * 100 if margin and margin > 0 else 0
                                logger.info(f"Account info fetched for close: Balance={balance:.2f}, Equity={equity:.2f}, Free Margin={free_margin:.2f}, Margin Level={margin_level:.2f}%")
                            else:
                                logger.warning("MT5 account_info() returned None during position close")
                                balance = equity = free_margin = margin_level = None
                        except Exception as e:
                            logger.error(f"Failed to get account info during position close: {e}")
                            balance = equity = free_margin = margin_level = None

                        # Get total volume traded today
                        try:
                            total_volume_today = self.get_today_total_volume()
                            logger.info(f"Total volume today: {total_volume_today:.2f}")
                        except Exception as e:
                            logger.error(f"Failed to get total volume today: {e}")
                            total_volume_today = 0.0

                        self.telegram_callback(
                            signal_type="close_position",
                            symbol=self.symbol,
                            ticket=position.ticket,
                            profit=position.profit,
                            volume=position.volume,
                            balance=balance,
                            equity=equity,
                            free_margin=free_margin,
                            margin_level=margin_level,
                            total_volume_today=total_volume_today
                        )
            
            if closed_count > 0:
                # ✅ Hitung net profit (setelah komisi)
                net_profit = total_profit - total_commission
                
                logger.info(f"🎯 SEMUA POSISI DITUTUP: {closed_count} posisi berhasil ditutup")
                logger.info(f"   Gross Profit: ${total_profit:.2f}")
                logger.info(f"   Total Commission: ${total_commission:.2f}")
                logger.info(f"   NET PROFIT: ${net_profit:.2f} 💰")
                logger.info(f"   Alasan: {reason}")
                
                self.position_type = None
                self.position_volume = 0.0
                self.position_price = 0.0
            
            return closed_count
            
        except Exception as e:
            logger.error(f"Close all positions error: {e}")
            return 0
    
    def open_position(self, order_type: str, signal: Signal) -> bool:
        """Open new position"""
        # Check floating loss limit
        max_floating_loss = self.config.get('max_floating_loss', 500)
        current_floating_loss = self.get_total_floating_loss()
        
        if current_floating_loss >= max_floating_loss:
            logger.warning(f"⚠️ Floating loss udah mentok: ${current_floating_loss:.2f} >= ${max_floating_loss:.2f}")
            logger.warning(f"   Gak buka posisi baru, biar modal aman!")
            return False
        
        # Check max positions (only count positions with our magic number)
        max_positions = self.config.get('max_positions', 3)
        magic = self.config.get('magic_number', 2026002)
        positions = mt5.positions_get(symbol=self.symbol)
        
        # Count only positions with our magic number
        our_positions_count = 0
        if positions:
            for pos in positions:
                if pos.magic == magic:
                    our_positions_count += 1
        
        if our_positions_count >= max_positions:
            logger.warning(f"⚠️ Jumlah posisi udah maksimal: {our_positions_count}/{max_positions} (Magic: {magic})")
            return False

        # Enforcement: floating loss hard block
        floating_pnl = self.get_floating_pnl()
        max_floating_loss = self.config.get("max_floating_loss", 0)

        max_floating_profit = self.config.get("max_floating_profit", 0)
        if max_floating_profit > 0 and floating_pnl >= max_floating_profit:
            logger.warning(
                f"🎯 TAKE PROFIT TARGET HIT - CLOSING ALL POSITIONS"
            )
            self.close_all_positions()
            return

        logger.info(
            f"📈 Coba buka posisi {signal.signal_type}..."
            f"(Floating Loss: ${floating_pnl:.2f}/${max_floating_loss:.2f})"
        )

        # Enforcement: daily loss hard block
        daily_pnl = self.get_today_closed_pnl()
        max_daily_loss = self.config.get("max_daily_loss", 0)

        logger.info(
            f"📅 PnL hari ini: ${daily_pnl:.2f} / -${max_daily_loss:.2f}"
        )

        if max_daily_loss > 0 and daily_pnl <= -max_daily_loss:
            logger.warning(
                f"🚨 MAX DAILY LOSS HIT: {daily_pnl:.2f}/{max_daily_loss:.2f}"
            )
            if self.risk_manager:
                self.risk_manager.trigger_circuit_breaker(
                    f"Daily loss exceeded: {daily_pnl:.2f}"
                )
            return False

        # Enforcement: daily trade count hard block
        daily_trades = self.get_today_trade_count()
        max_daily_trades = self.config.get("max_daily_trades", 0)

        logger.info(
            f"📊 Trading hari ini: {daily_trades}/{max_daily_trades}"
        )

        if max_daily_trades > 0 and daily_trades >= max_daily_trades:
            logger.warning(
                f"🚨 MAX DAILY TRADES HIT: {daily_trades}/{max_daily_trades}"
            )
            # Hanya warning, tidak close all dan tidak trigger circuit breaker
            return False

        # Check daily volume limit
        daily_volume = self.get_today_total_volume()
        max_daily_volume = self.config.get("max_daily_volume", 0)

        if max_daily_volume > 0 and daily_volume >= max_daily_volume:
            logger.warning(
                f"🚨 MAX DAILY VOLUME HIT: {daily_volume:.2f}/{max_daily_volume:.2f}"
            )
            return False

        # Enforcement: max total position volume
        current_volume = self.get_total_position_volume()
        max_position_size = self.config.get("max_position_size", 0)

        if max_position_size > 0 and (current_volume + signal.volume) > max_position_size:
            logger.warning(
                f"🚫 MAX POSITION SIZE HIT: {current_volume + signal.volume:.2f}/{max_position_size:.2f} lots"
            )
            return False

        # Calculate real drawdown before entry
        # ✅ Reset daily stats if it's a new day
        self.reset_daily_stats()
        
        current_equity = self.get_account_equity()

        # ✅ DAILY DRAWDOWN CALCULATION (from today's peak only, not all-time peak)
        # peak_equity is reset to current equity at start of day, so this calculates daily DD
        drawdown_pct = 0.0
        if self.peak_equity > 0:
            drawdown_pct = ((self.peak_equity - current_equity) / self.peak_equity) * 100
        
        # ✅ UPDATE: Only update peak_equity if we're higher TODAY (daily peak tracking)
        # This ensures we calculate daily drawdown from today's highest point
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            logger.debug(f"New daily peak equity: ${self.peak_equity:.2f}")

        logger.info(
            f"📉 Daily Drawdown: {drawdown_pct:.2f}% (Today's Peak: ${self.peak_equity:.2f})"
        )

        # Enforcement: max daily drawdown
        max_dd = self.config.get("max_drawdown_pct", 0)

        if max_dd > 0 and drawdown_pct >= max_dd:
            logger.warning(
                f"🚨 MAX DAILY DRAWDOWN HIT: {drawdown_pct:.2f}% / {max_dd:.2f}%"
            )
            if self.risk_manager:
                self.risk_manager.trigger_circuit_breaker(
                    f"Daily Drawdown exceeded {drawdown_pct:.2f}%"
                )
            return False

        # Prepare request
        try:
            symbol_info = mt5.symbol_info(self.symbol)
            if symbol_info is None:
                return False
            
            # Validate TP distance before sending order
            min_required = self.stops_level * self.symbol_point if self.stops_level > 0 else 0.5
            tp_distance = abs(signal.price - signal.take_profit)
            sl_distance = abs(signal.price - signal.stop_loss)
            
            if tp_distance < min_required:
                logger.error(f"❌ TP distance too small: {tp_distance:.5f} < {min_required:.5f}")
                logger.error(f"   This should not happen! Check generate_signal() TP calculation")
                logger.error(f"   TP Mode: {self.config.get('tp_mode', 'RiskReward')}, Target: ${self.config.get('tp_dollar_amount', 0.5):.2f}")
                return False
            
            if sl_distance < min_required:
                logger.error(f"❌ SL distance too small: {sl_distance:.5f} < {min_required:.5f}")
                return False
            
            # Get filling mode from config
            filling_mode_str = self.config.get('filling_mode', 'FOK')
            filling_mode = self.get_filling_mode(filling_mode_str)
            
            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": signal.volume,
                "type": mt5.ORDER_TYPE_BUY if order_type == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": signal.price,
                "sl": signal.stop_loss,
                "tp": signal.take_profit,
                "deviation": self.config.get('slippage', 20),
                "magic": self.config.get('magic_number', 2026002),
                "comment": f"AvHFTPro2026_{order_type}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }

            # =============================
            # HARD SAFETY CHECK (FINAL FIX)
            # =============================

            # Cooldown anti spam HFT
            now = time.time()
            if now - self.last_trade_time < self.min_trade_interval:
                return False

            current_positions = self.get_current_positions_count()

            # ✅ FIX: Get current account balance for proper drawdown calculation
            account_info = mt5.account_info()
            account_balance = account_info.balance if account_info else 0.0

            allowed, reason = True, ""
            if self.risk_manager:
                allowed, reason = self.risk_manager.validate_trade(
                    trade_type=signal.signal_type,
                    volume=signal.volume,
                    current_positions=current_positions,
                    account_balance=account_balance
                )

            if not allowed:
                logger.warning(f"🚫 TRADE BLOCKED | {reason}")
                return False

            # =============================
            # EXECUTE ORDER
            # =============================
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                # ✅ INCREMENT BOT'S TRADE COUNTER
                self.bot_trades_today += 1
                
                self.last_trade_time = now
                self.position_type = order_type
                self.position_volume = signal.volume
                self.position_price = result.price
                
                logger.info(f"✓ Bot trade #{self.bot_trades_today} opened:  {order_type} @ {result.price:.5f}")
                
                # Send Telegram signal for open position
                if self.telegram_callback:
                    # Get account info for telegram signal
                    try:
                        account_info = mt5.account_info()
                        if account_info:
                            balance = account_info.balance
                            equity = account_info.equity
                            free_margin = account_info.margin_free
                            margin = account_info.margin
                            margin_level = (equity / margin) * 100 if margin and margin > 0 else 0
                            logger.info(f"Account info fetched for open: Balance={balance:.2f}, Equity={equity:.2f}, Free Margin={free_margin:.2f}, Margin Level={margin_level:.2f}%")
                        else:
                            logger.warning("MT5 account_info() returned None during position open")
                            balance = equity = free_margin = margin_level = None
                    except Exception as e:
                        logger.error(f"Failed to get account info during position open: {e}")
                        balance = equity = free_margin = margin_level = None
                    
                    # ✅ NEW: Get total volume traded today
                    try:
                        total_volume_today = self.get_today_total_volume()
                        logger.info(f"Total volume today: {total_volume_today:.2f}")
                    except Exception as e:
                        logger.error(f"Failed to get total volume today: {e}")
                        total_volume_today = 0.0
                    
                    self.telegram_callback(
                        signal_type="open_position",
                        symbol=self.symbol,
                        order_type=order_type,
                        volume=signal.volume,
                        price=signal.price,
                        sl=signal.stop_loss,
                        tp=signal.take_profit,
                        balance=balance,
                        equity=equity,
                        free_margin=free_margin,
                        margin_level=margin_level,
                        total_volume_today=total_volume_today
                    )
                
                return True
            else:
                logger.warning(f"Order gagal: {result.retcode} - {result.comment}")
                
                # Detailed error info for debugging
                if result.retcode == 10016:  # Invalid stops
                    logger.error(f"Invalid stops error details:")
                    logger.error(f"  Price: {signal.price:.5f}")
                    logger.error(f"  SL: {signal.stop_loss:.5f} (distance: {abs(signal.price - signal.stop_loss):.5f})")
                    logger.error(f"  TP: {signal.take_profit:.5f} (distance: {abs(signal.price - signal.take_profit):.5f})")
                    logger.error(f"  Min required distance: {self.stops_level * self.symbol_point:.5f} ({self.stops_level} points)")
                return False

        except Exception as e:
            logger.error(f"Open position error: {e}")
            return False
    
    def close_position(self) -> bool:
        """Close current position (only positions with our magic number)"""
        if self.position_type is None:
            return False
        
        try:
            magic = self.config.get('magic_number', 2026002)
            positions = mt5.positions_get(symbol=self.symbol)
            
            if positions is None or len(positions) == 0:
                self.position_type = None
                return False
            
            # Find first position with our magic number
            position = None
            for pos in positions:
                if pos.magic == magic:
                    position = pos
                    break
            
            if position is None:
                logger.warning(f"Nggak nemu posisi dengan magic number {magic}")
                self.position_type = None
                return False
            
            # Prepare close request
            close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(self.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(self.symbol).ask
            
            # Get filling mode from config
            filling_mode_str = self.config.get('filling_mode', 'FOK')
            filling_mode = self.get_filling_mode(filling_mode_str)
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": position.volume,
                "type": close_type,
                "position": position.ticket,
                "price": price,
                "deviation": self.config.get('slippage', 20),
                "magic": self.config.get('magic_number', 2026002),
                "comment": "AvHFTPro2026_CLOSE",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
            
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                profit = position.profit
                
                # ✅ UPDATE BOT-SPECIFIC WIN/LOSS
                if profit > 0:
                    self.bot_wins += 1
                elif profit < 0:
                    self.bot_losses += 1

                # ✅ UPDATE: Bot's own balance (isolated from other bots)
                self.bot_balance += profit
                self.bot_closed_pnl += profit
                # ✅ UPDATE BOT-SPECIFIC DAILY PNL
                self.bot_daily_pnl += profit
                
                logger.info(f"✓ Position closed:  Profit={profit:.2f} | Bot Balance:  ${self.bot_balance:.2f}")
                
                # Send Telegram signal for close position (include account info)
                if self.telegram_callback:
                    try:
                        account_info = mt5.account_info()
                        if account_info:
                            balance = account_info.balance
                            equity = account_info.equity
                            free_margin = account_info.margin_free
                            margin = account_info.margin
                            margin_level = (equity / margin) * 100 if margin and margin > 0 else 0
                            logger.info(f"Account info fetched for close: Balance={balance:.2f}, Equity={equity:.2f}, Free Margin={free_margin:.2f}, Margin Level={margin_level:.2f}%")
                        else:
                            logger.warning("MT5 account_info() returned None during position close")
                            balance = equity = free_margin = margin_level = None
                    except Exception as e:
                        logger.error(f"Failed to get account info during position close: {e}")
                        balance = equity = free_margin = margin_level = None

                    # Get total volume traded today
                    try:
                        total_volume_today = self.get_today_total_volume()
                        logger.info(f"Total volume today: {total_volume_today:.2f}")
                    except Exception as e:
                        logger.error(f"Failed to get total volume today: {e}")
                        total_volume_today = 0.0

                    self.telegram_callback(
                        signal_type="close_position",
                        symbol=self.symbol,
                        ticket=position.ticket,
                        profit=position.profit,
                        volume=position.volume,
                        balance=balance,
                        equity=equity,
                        free_margin=free_margin,
                        margin_level=margin_level,
                        total_volume_today=total_volume_today
                    )
                
                # Record trade to risk_manager
                if self.risk_manager:
                    from risk_manager import TradeRecord
                    trade_record = TradeRecord(
                        timestamp=datetime.now(),
                        symbol=self.symbol,
                        trade_type='CLOSE',
                        volume=position.volume,
                        open_price=position.price_open,
                        close_price=position.price_current,
                        profit=profit,
                        duration=0,
                        reason='Position closed from engine'
                    )
                    self.risk_manager.record_trade(trade_record)
                
                self.position_type = None
                self.position_volume = 0.0
                return True
            else:
                logger.warning(f"Gagal nutup posisi: {result.retcode} - {result.comment}")
                return False
                
        except Exception as e:
            logger.error(f"Close position error: {e}")
            return False
    
    def data_collection_loop(self):
        """Ultra-fast data collection thread"""
        logger.info("Thread pengambilan data mulai jalan!")
        
        while self.is_running:
            try:
                # Get tick data
                tick = self.get_tick_ultra_fast()
                if tick:
                    self.tick_buffer.append(tick)
                    
                    # Calculate order flow
                    orderflow = self.calculate_order_flow(tick)
                    if orderflow:
                        self.orderflow_buffer.append(orderflow)
                
                # Sleep for minimal time (adjust based on broker tick frequency)
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                logger.error(f"Data collection error: {e}")
                time.sleep(0.1)
    
    def analysis_loop(self):
        """Market analysis and signal generation thread"""
        logger.info("Thread analisa jalan, siap mantau market!")
        analysis_count = 0
        last_position_check = time.time()
        
        while self.is_running:
            try:
                # Periodic position sync check (every 5 seconds)
                current_time = time.time()
                if current_time - last_position_check > 5.0:
                    # Check position status and floating loss (only our magic number)
                    magic = self.config.get('magic_number', 2026002)
                    positions = mt5.positions_get(symbol=self.symbol)
                    
                    # Count only our positions
                    pos_count = 0
                    if positions:
                        for pos in positions:
                            if pos.magic == magic:
                                pos_count += 1
                    
                    floating_loss = self.get_total_floating_loss()
                    max_floating = self.config.get('max_floating_loss', 500)
                    
                    # Check floating profit target (total floating profit - commission)
                    floating_profit = self.get_total_floating_profit()  # ✅ Sudah NET (profit - commission)
                    max_profit_target = self.config.get('max_floating_profit', 0.5)

                    if pos_count > 0:
                        commission_per_trade = self.config.get('commission_per_trade', 0.0)
                        total_commission = commission_per_trade * pos_count
                        
                        # ✅ FIXED: Added .2f to max_floating
                        logger.info(f"📊 Status Posisi: {pos_count} posisi kebuka (Magic: {magic}) | "
                                    f"Profit (NET): ${floating_profit:.2f} | "
                                    f"Commission: ${total_commission:.2f} | "
                                    f"Rugi: ${floating_loss:.2f}/${max_floating:.2f}")  # ← FIXED!
                        
                        # ✅ UNIFIED CHECK: Gunakan config max_profit_target (hapus hardcoded $1)
                        if floating_profit >= max_profit_target:
                            logger.warning(f"🎯 Target profit tercapai: ${floating_profit:.2f} >= ${max_profit_target:.2f} (SETELAH KOMISI)")
                            logger.warning(f"   Total Commission Paid: ${total_commission:.2f}")
                            logger.warning(f"   Tutup semua posisi biar profitnya nggak ilang!")
                            closed = self.close_all_positions(reason=f"Profit_Target_{floating_profit:.2f}_net")
                            if closed > 0:
                                logger.info(f"✓ Berhasil nutup {closed} posisi")
                        # Reset state if no positions exist
                        if not self.verify_position_exists():
                            logger.info(f"🔄 Semua posisi udah ditutup - Reset ulang state")
                            self.position_type = None
                            self.position_volume = 0.0
                            self.position_price = 0.0
                    
                    last_position_check = current_time
                
                # Analyze market microstructure
                microstructure = self.analyze_microstructure()
                
                if microstructure:
                    analysis_count += 1
                    
                    # Generate signal
                    signal = self.generate_signal(microstructure)
                    
                    if signal:
                        # Add to signal queue
                        if not self.signal_queue.full():
                            self.signal_queue.put(signal)
                            logger.info(f"📊 SINYAL DIBUAT: {signal.signal_type} | "
                                      f"Kekuatan: {signal.strength:.2f} | "
                                      f"Harga: {signal.price:.5f} | "
                                      f"Alasan: {signal.reason}")
                        else:
                            logger.warning("Antrian sinyal penuh, skip dulu ya")
                    else:
                        # Log every 10 analyses with diagnostics
                        if analysis_count % 10 == 0:
                            logger.info(f"⏳ [{analysis_count}] Spread: {microstructure['avg_spread']:.5f} | "
                                      f"Delta: {microstructure['cumulative_delta']:.0f} | "
                                      f"Velocity: {microstructure['price_velocity']:.6f} | "
                                      f"Volatility: {microstructure['volatility']:.5f}")
                        # Log every 50 for summary
                        if analysis_count % 50 == 0:
                            logger.info(f"⏳ Analyzing market...({analysis_count} analyses, no strong signal yet)")
                else:
                    logger.debug("Waiting for sufficient tick data...")
                
                # Analysis frequency
                time.sleep(self.config.get('analysis_interval', 0.1))  # 100ms
                
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                time.sleep(1)
    
    def execution_loop(self):
        """Signal execution thread"""
        logger.info("Thread eksekusi sinyal udah nyala!")
        
        while self.is_running:
            try:
                # Get signal from queue
                if not self.signal_queue.empty():
                    signal = self.signal_queue.get(timeout=1)
                    
                    # Execute signal
                    self.execute_signal(signal)
                else:
                    time.sleep(0.01)  # 10ms
                    
            except Exception as e:
                logger.error(f"Execution loop error: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start HFT engine"""
        logger.info("=" * 60)
        logger.info("Mesin Aventa HFT Pro 2026 siap tempur!")
        logger.info("=" * 60)
        
        if not self.initialize():
            logger.error("Failed to initialize")
            return False
        
        self.is_running = True
        
        # Start threads
        self.data_thread = threading.Thread(target=self.data_collection_loop, daemon=True)
        self.analysis_thread = threading.Thread(target=self.analysis_loop, daemon=True)
        self.execution_thread = threading.Thread(target=self.execution_loop, daemon=True)
        
        self.data_thread.start()
        self.analysis_thread.start()
        self.execution_thread.start()
        
        logger.info("✓ Semua thread udah jalan semua!")
        logger.info(f"  Simbol: {self.symbol}")
        logger.info(f"  Interval analisa: {self.config.get('analysis_interval', 0.1)} detik")
        logger.info(f"  Volume default: {self.config.get('default_volume', 0.01)}")
        logger.info(f"  Kekuatan sinyal minimal: {self.config.get('min_signal_strength', 0.6)}")
        logger.info(f"  Risk/Reward: {self.config.get('risk_reward_ratio', 2.0)}")
        logger.info(f"  Floating Loss Maks: ${self.config.get('max_floating_loss', 500):.2f}")
        logger.info(f"  Target Take Profit: ${self.config.get('max_floating_profit', 0.5):.2f} (Close All)")
        logger.info("")
        logger.info("🔍 Nunggu sinyal trading...")
        logger.info("   Bot bakal entry kalau:")
        logger.info("   • Delta order flow lewat ambang")
        logger.info("   • Momentum harga kenceng")
        logger.info("   • Spread masih aman")
        logger.info("   • Kekuatan sinyal cukup")
        logger.info("")
        
        return True
    
    def stop(self):
        """Stop HFT engine (TIDAK MENUTUP POSISI!)"""
        logger.info("🛑 Stopping HFT engine...")
        self.is_running = False
        
        # Wait for threads to finish
        if self.data_thread:
            self.data_thread.join(timeout=5)
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
        if self.execution_thread:
            self.execution_thread.join(timeout=5)
        
        # ✅ FIX:  JANGAN tutup posisi ketika stop!
        # Posisi tetap terbuka dan bisa dikelola manual atau bot lain
        if self.position_type:
            magic = self.config.get('magic_number', 2026002)
            logger.info(f"⚠️ Bot stopped - {self.position_type} position remains open (Magic: {magic})")
            logger.info(f"   Volume: {self.position_volume} | Entry: {self.position_price:.5f}")
            logger.info(f"   💡 Manage position manually or restart bot to continue")
        
        # Shutdown MT5 connection (posisi tetap di server)
        mt5.shutdown()
        logger.info("✓ Engine stopped (positions remain active)")
    
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        trades, wins, losses, daily_pnl = self.get_today_trade_stats()
        win_rate = (wins / trades * 100) if trades > 0 else 0.0
        pos_type, pos_vol = self.get_current_position_info()

        return {
            "tick_latency_avg_us": np.mean(self.latency_samples) if self.latency_samples else 0,
            "tick_latency_max_us": max(self.latency_samples) if self.latency_samples else 0,
            "tick_latency_min_us": min(self.latency_samples) if self.latency_samples else 0,
            "execution_time_avg_ms": np.mean(self.execution_times) if self.execution_times else 0,
            "execution_time_max_ms": max(self.execution_times) if self.execution_times else 0,
            "ticks_processed": len(self.tick_buffer),
            "signals_generated": self.signals_generated,
            "trades_today": trades,
            "daily_pnl": daily_pnl,
            "win_rate": win_rate,
            "current_position": pos_type,
            "position_volume": pos_vol
        }
    
    def get_performance_snapshot(self):
        """Get bot-specific performance snapshot with ACTUAL MT5 floating P&L"""
        
        # ✅ GET TODAY'S STATS INCLUDING ACTUAL FLOATING P&L
        trades_today, bot_wins, bot_losses, daily_pnl_actual = self.get_today_trade_stats()
        total_trades = bot_wins + bot_losses
        win_rate = (bot_wins / total_trades * 100) if total_trades > 0 else 0.0
        
        # ✅ GET ONLY THIS BOT'S POSITIONS
        magic = self.config.get('magic_number', 2026002)
        positions = mt5.positions_get(symbol=self.symbol)
        
        bot_floating = 0.0
        bot_position_count = 0
        bot_position_type = "None"
        bot_position_volume = 0.0
        
        if positions:
            for pos in positions:
                if pos.magic == magic:  # ✅ ONLY THIS BOT! 
                    bot_floating += pos.profit
                    bot_position_count += 1
                    if bot_position_count == 1:  # First position
                        bot_position_type = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
                        bot_position_volume = pos.volume
        
        # ✅ GET GLOBAL ACCOUNT BALANCE (shared)
        account = mt5.account_info()
        global_balance = account.balance if account else 0.0
        
        # ✅ CALCULATE BOT-SPECIFIC EQUITY
        # Equity = Global Balance + This Bot's Floating P&L
        bot_equity = global_balance + bot_floating
        
        # ✅ CALCULATE BOT-SPECIFIC DRAWDOWN
        if bot_equity > self.bot_peak_balance:
            self.bot_peak_balance = bot_equity
        
        bot_drawdown = 0.0
        if self.bot_peak_balance > 0:
            bot_drawdown = ((self.bot_peak_balance - bot_equity) / self.bot_peak_balance) * 100

        return {
            # ✅ BOT-SPECIFIC TRADING STATS WITH ACTUAL FLOATING P&L
            "trades_today": trades_today,
            "wins":  bot_wins,
            "losses": bot_losses,
            "win_rate": win_rate,
            "daily_pnl": daily_pnl_actual,  # ✅ NOW INCLUDES FLOATING FROM OPEN POSITIONS
            "current_position": bot_position_type,
            "position_volume": bot_position_volume,
            
            # Signals
            "signals_generated": self.signals_generated,
            
            # Performance
            "tick_latency_avg": np.mean(self.latency_samples) if self.latency_samples else 0,
            "tick_latency_max": max(self.latency_samples) if self.latency_samples else 0,
            "exec_time_avg": np.mean(self.execution_times) if self.execution_times else 0,
            "exec_time_max": max(self.execution_times) if self.execution_times else 0,
            "ticks_processed": len(self.tick_buffer),
            
            # ✅ BOT-SPECIFIC ACCOUNT METRICS
            "balance": global_balance,  # Global (shared across all bots)
            "equity": bot_equity,       # Bot-specific (balance + this bot's floating)
            "floating":  bot_floating,   # Only this bot's floating P&L
            "drawdown": bot_drawdown    # Bot-specific drawdown
        }

    def get_current_positions_count(self):
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return 0
        return len(positions)

    def get_floating_pnl(self):
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return 0.0

        floating = 0.0
        for p in positions:
            floating += p.profit  # profit MT5 sudah termasuk swap & commission
        return floating

    @cache_with_ttl(ttl_seconds=0.5)  # Cache 500ms
    def get_today_closed_pnl(self):
        from datetime import datetime, time, timezone
        import pytz

        # Ambil timezone server MT5
        tick_info = mt5.symbol_info_tick(self.symbol)
        if tick_info is not None and hasattr(tick_info, 'time'):
            server_time = tick_info.time
            server_dt = datetime.fromtimestamp(server_time)
            local_dt = datetime.now()
            offset = local_dt - server_dt
            now = datetime.now()
            day_start = datetime.combine(now.date(), time.min)
            day_start_server = day_start - offset
            now_server = now - offset
            deals = mt5.history_deals_get(day_start_server, now_server)
        else:
            # Fallback: gunakan waktu lokal tanpa konversi jika info tick tidak tersedia
            now = datetime.now()
            day_start = datetime.combine(now.date(), time.min)
            deals = mt5.history_deals_get(day_start, now)
        if deals is None:
            return 0.0

        pnl = 0.0
        magic = self.config.get('magic_number', 2026002)
        for d in deals:
            # ✅ FILTER BY MAGIC NUMBER - only count this bot's P&L
            if d.magic == magic:
                pnl += d.profit  # sudah termasuk commission & swap

        return pnl

    @cache_with_ttl(ttl_seconds=1.0)  # Cache 1 second
    def get_today_trade_count(self):
        from datetime import datetime, time, timezone
        import pytz

        tick_info = mt5.symbol_info_tick(self.symbol)
        if tick_info is not None and hasattr(tick_info, 'time'):
            server_time = tick_info.time
            server_dt = datetime.fromtimestamp(server_time)
            local_dt = datetime.now()
            offset = local_dt - server_dt
            now = datetime.now()
            day_start = datetime.combine(now.date(), time.min)
            day_start_server = day_start - offset
            now_server = now - offset
            deals = mt5.history_deals_get(day_start_server, now_server)
        else:
            # Fallback: gunakan waktu lokal tanpa konversi jika info tick tidak tersedia
            now = datetime.now()
            day_start = datetime.combine(now.date(), time.min)
            deals = mt5.history_deals_get(day_start, now)
        if deals is None:
            return 0

        trade_count = 0
        magic = self.config.get('magic_number', 2026002)
        for d in deals:
            # ✅ FILTER BY MAGIC NUMBER - only count this bot's trades
            if d.magic == magic and d.entry == mt5.DEAL_ENTRY_IN:
                trade_count += 1

        return trade_count

    def get_today_total_volume(self):
        """Get total volume traded today for this bot"""
        from datetime import datetime, time

        now = datetime.now()
        day_start = datetime.combine(now.date(), time.min)
        deals = mt5.history_deals_get(day_start, now)

        if deals is None:
            return 0.0

        total_volume = 0.0
        magic = self.config.get('magic_number', 2026002)

        for deal in deals:
            if deal.magic == magic and deal.entry == mt5.DEAL_ENTRY_IN:
                total_volume += deal.volume

        return total_volume

    def get_today_trade_stats(self):
        """
        Calculate today's trading statistics including ACTUAL floating P&L
        
        Daily P&L = Realized P&L (closed trades) + Unrealized P&L (floating from open positions)
        This ensures Daily P&L reflects ACTUAL MT5 floating actual, not just accumulated trades
        """
        from datetime import datetime, time, timezone
        import pytz

        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            # Return default values or raise a warning if tick data is unavailable
            return 0, 0, 0, 0.0
        server_time = tick.time
        server_dt = datetime.fromtimestamp(server_time)
        local_dt = datetime.now()
        offset = local_dt - server_dt

        now = datetime.now()
        day_start = datetime.combine(now.date(), time.min)

        day_start_server = day_start - offset
        now_server = now - offset

        deals = mt5.history_deals_get(day_start_server, now_server)
        if not deals:
            # Still need to calculate floating from open positions even if no closed trades
            realized_pnl = 0.0
        else:
            realized_pnl = 0.0

        trades = 0
        wins = 0
        losses = 0

        magic = self.config.get('magic_number', 2026002)

        if deals:
            for d in deals:
                # ✅ FILTER BY MAGIC NUMBER - only count this bot's trades
                if d.magic != magic:
                    continue
                    
                realized_pnl += d.profit
                if d.entry == mt5.DEAL_ENTRY_IN:
                    trades += 1
                if d.profit > 0:
                    wins += 1
                elif d.profit < 0:
                    losses += 1

        # ✅ GET CURRENT FLOATING P&L FROM OPEN POSITIONS
        # This ensures Daily P&L reflects ACTUAL floating actual from MT5
        floating_pnl = 0.0
        positions = mt5.positions_get(symbol=self.symbol)
        if positions:
            for pos in positions:
                if pos.magic == magic:  # Only this bot's positions
                    floating_pnl += pos.profit
        
        # ✅ TOTAL DAILY P&L = Realized (closed trades) + Unrealized (floating from open positions)
        total_daily_pnl = realized_pnl + floating_pnl

        return trades, wins, losses, total_daily_pnl

    def get_total_position_volume(self):
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None:
            return 0.0

        total_volume = 0.0
        for p in positions:
            total_volume += p.volume

        return total_volume

    def get_account_equity(self):
        """Get account equity (cached)"""
        snapshot = self.account_cache.get_info()
        return snapshot.equity if snapshot else 0.0
    
    def get_account_balance(self):
        """Get account balance (cached)"""
        snapshot = self.account_cache.get_info()
        return snapshot.balance if snapshot else 0.0
    
    # ✅ ADD rate limiting to logging
    @rate_limit(seconds=5)
    def log_spread_reject(self, spread, threshold):
        """Rate-limited spread rejection logging"""
        logger.warning(f"⚠️ SPREAD REJECT: {spread:.5f} > {threshold:.5f}")

    def get_current_position_info(self):
        positions = mt5.positions_get(symbol=self.symbol)
        if not positions:
            return "None", 0.0

        p = positions[0]
        pos_type = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
        return pos_type, p.volume

    def get_performance_snapshot(self):
        """Get comprehensive performance snapshot for GUI display"""
        try:
            # Get account info
            account_info = self.account_cache.get_info()
            
            # Get today's trade statistics from MT5 history (more accurate)
            trades_today, wins, losses, daily_pnl = self.get_today_trade_stats()
            
            # Calculate win rate
            total_trades = wins + losses
            win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
            
            # Get current position
            position_type, position_volume = self.get_current_position_info()
            
            # Calculate floating P&L
            floating_pnl = 0.0
            positions = mt5.positions_get(symbol=self.symbol)
            if positions:
                for pos in positions:
                    floating_pnl += pos.profit
            
            # Calculate latency metrics
            latency_avg = sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0
            latency_max = max(self.latency_samples) if self.latency_samples else 0
            
            # Calculate execution time metrics
            exec_avg = sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0
            exec_max = max(self.execution_times) if self.execution_times else 0
            
            return {
                'trades_today': trades_today,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'daily_pnl': daily_pnl,
                'signals_generated': self.signals_generated,
                'current_position': position_type,
                'position_volume': position_volume,
                'balance': account_info.balance if account_info else 0.0,
                'equity': account_info.equity if account_info else 0.0,
                'floating': floating_pnl,
                'tick_latency_avg': latency_avg,
                'tick_latency_max': latency_max,
                'exec_time_avg': exec_avg,
                'exec_time_max': exec_max,
                'ticks_processed': len(self.tick_buffer)
            }
        except Exception as e:
            logger.error(f"Error getting performance snapshot: {e}")
            return {
                'trades_today': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0.0,
                'daily_pnl': 0.0,
                'signals_generated': 0,
                'current_position': 'None',
                'position_volume': 0.0,
                'balance': 0.0,
                'equity': 0.0,
                'floating': 0.0,
                'tick_latency_avg': 0,
                'tick_latency_max': 0,
                'exec_time_avg': 0,
                'exec_time_max': 0,
                'ticks_processed': 0
            }


if __name__ == "__main__":
    # Example configuration
    config = {
        'magic_number': 2026002,
        'default_volume': 0.01,
        'min_delta_threshold': 50,
        'min_velocity_threshold': 0.00001,
        'max_spread': 0.0002,
        'max_volatility': 0.001,
        'min_signal_strength': 0.6,
        'risk_reward_ratio': 2.0,
        'analysis_interval': 0.1,
        'slippage': 20
    }
    
    # Create engine
    engine = UltraLowLatencyEngine(symbol="EURUSD", config=config)
    
    try:
        # Start engine
        if engine.start():
            # Run for demo
            logger.info("Engine running...Press Ctrl+C to stop")
            
            while True:
                time.sleep(10)
                
                # Print performance stats
                stats = engine.get_performance_stats()
                logger.info(f"Performance: "
                          f"Latency={stats['tick_latency_avg_us']:.1f}μs | "
                          f"ExecTime={stats['execution_time_avg_ms']:.2f}ms | "
                          f"Ticks={stats['ticks_processed']}")
                
    except KeyboardInterrupt:
        logger.info("\nShutdown requested by user")
    finally:
        engine.stop()
