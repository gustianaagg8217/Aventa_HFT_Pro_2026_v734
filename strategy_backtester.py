"""
Strategy Backtester
Backtests trading strategy with historical data
"""

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StrategyBacktester:

    def __init__(self, config, initial_balance=10000, ml_predictor=None):
        """Initialize backtester with ISOLATED config and balance"""
        import copy

        # ✅ CRITICAL: Deep copy config untuk isolasi penuh
        self.config = copy.deepcopy(config)

        # ✅ ML PREDICTOR INTEGRATION
        self.ml_predictor = ml_predictor
        self.use_ml = ml_predictor is not None and hasattr(ml_predictor, 'is_trained') and ml_predictor.is_trained

        # ✅ CRITICAL: Use GUI initial_balance (NEVER use account balance!)
        self.initial_balance = float(initial_balance)
        self.balance = float(initial_balance)
        self.equity = float(initial_balance)

        # ✅ VALIDATE CONFIG
        self._validate_config()

        self.trades = []
        self.open_position = None

        # Performance tracking
        self.equity_curve = []
        self.peak_equity = float(initial_balance)
        self.max_drawdown = 0

        # ✅ ADD COMMISSION AND SLIPPAGE
        self.commission_per_trade = self.config.get('commission_per_trade', 0.0)
        self.slippage_pips = self.config.get('slippage_pips', 0.0)

        # ✅ ADD SYMBOL INFO
        self.symbol_info = None
        self.pip_value = 0.0
        self.pip_size = 0.00001  # Default for most forex pairs

        # ✅ INITIALIZE PIP_VALUE BASED ON SYMBOL AND VOLUME
        # For proper calculation: pip_value = volume * pip_size * contract_size
        # Standard forex contract: 100,000 units per lot
        volume = self.config.get('default_volume', 0.01)
        self.pip_value = volume * 100000 * self.pip_size  # For standard forex
        
        # For precious metals like GOLD/XAUUSD: 1 pip = $0.01 per 0.01 lot
        if 'XAU' in self.config.get('symbol', '').upper() or 'GOLD' in self.config.get('symbol', '').upper():
            self.pip_value = 0.01 * (volume / 0.01)
        # For crypto (typically uses tinycore): adjust as needed
        elif any(crypto in self.config.get('symbol', '').upper() for crypto in ['BTC', 'ETH']):
            self.pip_value = 1.0 * volume  # Simplified for crypto

        logger.info(f"Backtester initialized for {self.config.get('symbol', 'UNKNOWN')} with ${self.initial_balance:,.2f}")

    def _validate_config(self):
        """Validate configuration parameters"""
        required_params = ['symbol', 'default_volume', 'magic_number']
        for param in required_params:
            if param not in self.config:
                raise ValueError(f"Missing required config parameter: {param}")

        # Validate volume
        volume = self.config.get('default_volume', 0.01)
        if volume <= 0:
            raise ValueError("Volume must be positive")

        # Validate symbol
        symbol = self.config.get('symbol', '')
        if not symbol:
            raise ValueError("Symbol cannot be empty")

    def _get_symbol_info(self):
        """Get symbol information from MT5"""
        try:
            symbol = self.config['symbol']
            info = mt5.symbol_info(symbol)
            if info is None:
                raise ValueError(f"Symbol {symbol} not found in MT5")

            self.symbol_info = info

            # Calculate pip value and size
            if symbol.endswith('JPY') or 'JPY' in symbol:
                self.pip_size = 0.001  # JPY pairs have 3 decimal places
            else:
                self.pip_size = 0.00001  # Most forex pairs have 5 decimal places

            # Pip value calculation (simplified)
            # For forex: pip_value = volume * pip_size * contract_size / current_price
            contract_size = 100000  # Standard lot size
            volume = self.config.get('default_volume', 0.01)
            current_price = info.ask if hasattr(info, 'ask') else 1.0

            self.pip_value = volume * self.pip_size * contract_size / current_price

            logger.info(f"Symbol {symbol}: pip_size={self.pip_size}, pip_value=${self.pip_value:.4f}")

        except Exception as e:
            logger.error(f"Failed to get symbol info: {e}")
            # Fallback values
            self.pip_size = 0.00001
            self.pip_value = 0.01 * self.config.get('default_volume', 0.01)

    def get_available_symbols(self):
        """Get list of available trading symbols from MT5"""
        try:
            if mt5.terminal_info() is None:
                if not mt5.initialize():
                    return []
            
            symbols = mt5.symbols_get()
            return [s.name for s in symbols] if symbols else []
        except Exception as e:
            logger.error(f"Failed to get available symbols: {e}")
            return []
    
    def find_symbol_in_mt5(self, requested_symbol):
        """
        Find symbol in MT5 with case-insensitive and partial matching
        Returns the actual symbol name in MT5 if found, otherwise None
        """
        try:
            if mt5.terminal_info() is None:
                if not mt5.initialize():
                    return None
            
            available_symbols = self.get_available_symbols()
            
            if not available_symbols:
                logger.warning("No symbols found in MT5")
                return None
            
            # Exact match (case insensitive)
            for sym in available_symbols:
                if sym.upper() == requested_symbol.upper():
                    logger.info(f"✓ Found exact match: {requested_symbol} → {sym}")
                    return sym
            
            # Partial match (case insensitive) - match by main name
            requested_upper = requested_symbol.upper().split('.')[0]  # Get base name (e.g., GOLD from GOLD.H1)
            for sym in available_symbols:
                sym_base = sym.upper().split('.')[0]
                if sym_base == requested_upper:
                    logger.info(f"✓ Found partial match: {requested_symbol} → {sym}")
                    return sym
            
            logger.warning(f"Symbol {requested_symbol} not found in MT5")
            logger.info(f"Available symbols (first 30): {', '.join(available_symbols[:30])}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding symbol: {e}")
            return None
        
    def run_backtest(self, start_date, end_date, progress_callback=None, cancel_check=None):
        """Run backtest on historical data with ISOLATED MT5 connection"""
        try:
            # ✅ VALIDATE DATES
            if start_date >= end_date:
                raise ValueError("Start date must be before end date")

            days_diff = (end_date - start_date).days
            if days_diff < 1:
                raise ValueError("Date range must be at least 1 day")
            if days_diff > 365:
                raise ValueError("Date range cannot exceed 1 year for performance")

            # ✅ ISOLATED MT5 INITIALIZATION (independent for each bot)
            # Check if MT5 is already initialized
            if mt5.terminal_info() is None:
                # MT5 not initialized yet, initialize it
                if not mt5.initialize():
                    raise Exception("MT5 initialization failed - Check Terminal connection")
                logger.info("✓ MT5 initialized for Strategy Tester")
            else:
                logger.info("✓ Using existing MT5 connection for Strategy Tester")

            # ✅ GET SYMBOL INFO FIRST
            self._get_symbol_info()

            requested_symbol = self.config['symbol']

            # ✅ IMPROVED SYMBOL VALIDATION - Find symbol with case-insensitive matching
            symbol = self.find_symbol_in_mt5(requested_symbol)
            
            if not symbol:
                # Symbol not found even with fuzzy matching
                available = self.get_available_symbols()
                available_sample = ', '.join(available[:20]) if available else "None"
                raise Exception(
                    f"Symbol '{requested_symbol}' not found in MT5. "
                    f"Available (first 20): {available_sample}"
                )
            
            logger.info(f"Using symbol from MT5: {symbol}")

            if progress_callback:
                progress_callback(5, "Validating data availability...")

            # Get historical data with validation
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_date, end_date)

            if rates is None or len(rates) == 0:
                raise Exception(f"No historical data for {symbol} in date range")

            if len(rates) < 100:  # Minimum data requirement
                raise Exception(f"Insufficient data: {len(rates)} bars (minimum 100 required)")

            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')

            # ✅ ADD VOLUME COLUMN (MT5 returns tick_volume, real_volume - we'll use tick_volume as volume)
            if 'tick_volume' in df.columns and 'volume' not in df.columns:
                df['volume'] = df['tick_volume']
            elif 'real_volume' in df.columns and 'volume' not in df.columns:
                df['volume'] = df['real_volume']
            elif 'volume' not in df.columns:
                # Fallback: create synthetic volume if neither exists
                logger.warning("Neither tick_volume nor real_volume found. Creating synthetic volume.")
                df['volume'] = 1.0  # Minimum volume for all bars

            # ✅ DATA QUALITY CHECKS
            if df.isnull().any().any():
                raise Exception("Historical data contains null values")

            # Check for data gaps (more than 1 hour gaps)
            time_diffs = df['time'].diff().dt.total_seconds() / 3600
            max_gap = time_diffs.max()
            if max_gap > 2:  # More than 2 hours gap
                logger.warning(f"Data gap detected: {max_gap:.1f} hours")

            if progress_callback:
                progress_callback(15, f"Loaded {len(df)} bars, calculating indicators...")

            # Calculate indicators
            df = self.calculate_indicators(df)

            # ✅ VALIDATE INDICATORS
            required_indicators = ['ema_fast', 'ema_slow', 'rsi', 'atr']
            for indicator in required_indicators:
                if indicator not in df.columns:
                    raise Exception(f"Indicator {indicator} not calculated")

            if progress_callback:
                progress_callback(30, "Running simulation...")

            total_bars = len(df)

            # ✅ ADAPTIVE PROGRESS REPORTING
            progress_interval = max(1, total_bars // 100)  # Update every 1% progress

            for i in range(50, total_bars):  # Start after indicator warmup
                # Check cancel
                if cancel_check and cancel_check():
                    logger.info("Backtest cancelled by user")
                    return None

                # Progress update
                if i % progress_interval == 0:
                    progress_pct = 30 + (i / total_bars * 65)
                    if progress_callback:
                        progress_callback(progress_pct, f"Processing bar {i}/{total_bars}")

                current_bar = df.iloc[i]

                # ✅ VALIDATE CURRENT BAR
                if pd.isnull(current_bar[['open', 'high', 'low', 'close', 'volume']]).any():
                    continue  # Skip invalid bars

                # Check for exit signal
                if self.open_position:
                    self.check_exit(current_bar, i, df)

                # Check for entry signal
                if not self.open_position:
                    self.check_entry(current_bar, i, df)

                # Update equity curve
                self.update_equity(current_bar)

            # Close any open position at end
            if self.open_position:
                final_bar = df.iloc[-1]
                self.close_position(final_bar, "End of backtest")

            # Calculate results
            if progress_callback:
                progress_callback(95, "Calculating results...")

            results = self.calculate_results()

            if progress_callback:
                progress_callback(100, "Complete!")

            logger.info(f"Backtest completed: {len(self.trades)} trades, P&L: ${results.get('total_pnl', 0):.2f}")

            return results

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            raise Exception(f"Backtest failed: {e}")
        finally:
            mt5.shutdown()
    
    def calculate_indicators(self, df):
        """Calculate technical indicators with validation"""
        try:
            # ✅ VALIDATE INPUT DATA
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")

            # EMA
            ema_fast = self.config.get('ema_fast_period', 7)
            ema_slow = self.config.get('ema_slow_period', 21)

            if ema_fast <= 0 or ema_slow <= 0:
                raise ValueError("EMA periods must be positive")
            if ema_fast >= ema_slow:
                raise ValueError("Fast EMA period must be less than slow EMA period")

            df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
            df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()

            # RSI
            rsi_period = self.config.get('rsi_period', 7)
            if rsi_period <= 0:
                raise ValueError("RSI period must be positive")

            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # Handle RSI NaN values
            df['rsi'] = df['rsi'].fillna(50)  # Neutral RSI for initial values

            # ATR
            atr_period = self.config.get('atr_period', 14)
            if atr_period <= 0:
                raise ValueError("ATR period must be positive")

            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(atr_period).mean()

            # Handle ATR NaN values
            df['atr'] = df['atr'].fillna(df['atr'].mean())

            # Momentum
            momentum_period = self.config.get('momentum_period', 5)
            if momentum_period <= 0:
                raise ValueError("Momentum period must be positive")

            df['momentum'] = df['close'].diff(momentum_period)

            # Volatility (20-period standard deviation)
            df['volatility'] = df['close'].rolling(20).std() / df['close'].rolling(20).mean()
            df['volatility'] = df['volatility'].fillna(0)

            # ✅ VALIDATE INDICATORS
            if df[['ema_fast', 'ema_slow', 'rsi', 'atr']].isnull().any().any():
                raise ValueError("Indicator calculation produced NaN values")

            logger.info(f"Indicators calculated: EMA({ema_fast},{ema_slow}), RSI({rsi_period}), ATR({atr_period})")

            return df

        except Exception as e:
            logger.error(f"Indicator calculation error: {e}")
            raise
    
    def check_entry(self, bar, index, df):
        """Check for entry signal with ML integration"""
        try:
            # Get signal strength
            signal_strength, signal_type = self.calculate_signal(bar, index, df)

            min_signal = self.config.get('min_signal_strength', 0.45)

            if abs(signal_strength) >= min_signal:
                # ✅ ML PREDICTION CHECK
                ml_prediction = ''
                ml_confidence = 0.0
                
                if self.use_ml:
                    try:
                        # Prepare features for ML
                        features = {
                            'returns': bar.get('returns', 0),
                            'momentum_5': bar.get('momentum_5', 0),
                            'momentum_10': bar.get('momentum_10', 0),
                            'rsi': bar.get('rsi', 50),
                            'volatility': bar.get('volatility', 0),
                        }
                        
                        # Get ML prediction
                        direction, confidence = self.ml_predictor.predict(features)
                        
                        if direction is not None:
                            ml_prediction = 'BUY' if direction == 1 else 'SELL'
                            ml_confidence = confidence * 100
                            
                            # Check if ML agrees with signal
                            if ml_prediction != signal_type:
                                # ML disagrees, reduce confidence or skip
                                ml_confidence_threshold = self.config.get('ml_confidence_threshold', 60)
                                if ml_confidence < ml_confidence_threshold:
                                    return  # Skip this entry if ML confidence is low
                    except Exception as e:
                        logger.warning(f"ML prediction error: {e}")

                # ✅ IMPROVED SPREAD CHECK
                spread = bar['spread'] * self.pip_size  # Convert to price units
                max_spread_pct = self.config.get('max_spread_pct', 0.001)  # 0.1% of price
                max_spread_price = bar['close'] * max_spread_pct

                if spread > max_spread_price:
                    return  # Spread too wide

                # ✅ IMPROVED VOLATILITY CHECK
                max_volatility = self.config.get('max_volatility', 0.005)
                if bar['volatility'] > max_volatility:
                    return  # Too volatile

                # ✅ CHECK MINIMUM VOLUME
                min_volume = self.config.get('min_volume', 0)
                if bar['volume'] < min_volume:
                    return  # Insufficient volume

                # ✅ AVOID ENTRIES NEAR SESSION EDGES (optional)
                hour = bar['time'].hour
                if self.config.get('avoid_session_edges', False):
                    if hour < 2 or hour > 21:  # Avoid 22:00-02:00
                        return

                # Calculate entry price with slippage
                slippage = self.slippage_pips * self.pip_size
                if signal_type == 'BUY':
                    entry_price = bar['close'] + slippage
                else:
                    entry_price = bar['close'] - slippage

                # Open position
                self.open_position = {
                    'type': signal_type,
                    'entry_price': entry_price,
                    'entry_time': bar['time'],
                    'entry_bar': index,
                    'sl': self.calculate_sl(bar, signal_type),
                    'tp': self.calculate_tp(bar, signal_type),
                    'volume': self.config.get('default_volume', 0.01),
                    'commission': self.commission_per_trade,
                    'ml_prediction': ml_prediction,
                    'ml_confidence': ml_confidence
                }

                logger.debug(f"Opened {signal_type} position at {entry_price:.5f} (ML: {ml_prediction} {ml_confidence:.1f}%)")

        except Exception as e:
            logger.error(f"Entry check error: {e}")

    def check_exit(self, bar, index, df):
        """Check for exit signal with improved logic"""
        try:
            if not self.open_position:
                return

            pos = self.open_position
            current_price = bar['close']

            # ✅ IMPROVED PROFIT CALCULATION
            profit = self.calculate_profit(current_price)

            # Check SL with slippage consideration
            sl_triggered = False
            if pos['type'] == 'BUY':
                sl_triggered = current_price <= pos['sl']
            else:  # SELL
                sl_triggered = current_price >= pos['sl']

            if sl_triggered:
                self.close_position(bar, "Stop Loss")
                return

            # Check TP
            tp_triggered = False
            if pos['type'] == 'BUY':
                tp_triggered = current_price >= pos['tp']
            else:  # SELL
                tp_triggered = current_price <= pos['tp']

            if tp_triggered:
                self.close_position(bar, "Take Profit")
                return

            # ✅ IMPROVED FLOATING LOSS CHECK
            max_loss = self.config.get('max_floating_loss', 5.0)
            if profit < -max_loss:
                self.close_position(bar, "Max Floating Loss")
                return

            # ✅ IMPROVED TP TARGET CHECK
            tp_target = self.config.get('max_floating_profit', 0.5)
            if profit >= tp_target:
                self.close_position(bar, "TP Target Reached")
                return

            # ✅ TIME-BASED EXIT (optional)
            max_duration_hours = self.config.get('max_trade_duration_hours', 24)
            if max_duration_hours > 0:
                duration_hours = (bar['time'] - pos['entry_time']).total_seconds() / 3600
                if duration_hours >= max_duration_hours:
                    self.close_position(bar, "Max Duration")
                    return

        except Exception as e:
            logger.error(f"Exit check error: {e}")
    
    def calculate_signal(self, bar, index, df):
        """Calculate signal strength with validation"""
        try:
            strength = 0
            signal_type = None

            # ✅ VALIDATE REQUIRED INDICATORS
            required = ['ema_fast', 'ema_slow', 'rsi', 'momentum']
            for indicator in required:
                if pd.isnull(bar[indicator]):
                    return 0, None  # Invalid bar, skip

            # EMA crossover (strongest signal)
            if bar['ema_fast'] > bar['ema_slow']:
                strength += 0.3
                signal_type = 'BUY'
            elif bar['ema_fast'] < bar['ema_slow']:
                strength += 0.3
                signal_type = 'SELL'

            # RSI confirmation
            rsi_ob = self.config.get('rsi_overbought', 68)
            rsi_os = self.config.get('rsi_oversold', 32)

            if bar['rsi'] < rsi_os and signal_type != 'SELL':
                strength += 0.2
                signal_type = 'BUY'
            elif bar['rsi'] > rsi_ob and signal_type != 'BUY':
                strength += 0.2
                signal_type = 'SELL'

            # Momentum confirmation
            if bar['momentum'] > 0 and signal_type != 'SELL':
                strength += 0.1
                signal_type = 'BUY'
            elif bar['momentum'] < 0 and signal_type != 'BUY':
                strength += 0.1
                signal_type = 'SELL'

            # Adjust strength for SELL signals (negative)
            if signal_type == 'SELL':
                strength = -strength

            return strength, signal_type

        except Exception as e:
            logger.error(f"Signal calculation error at bar {index}: {e}")
            return 0, None
    
    def calculate_sl(self, bar, signal_type):
        """Calculate stop loss with proper pip conversion"""
        try:
            atr = bar['atr']
            sl_mult = self.config.get('sl_multiplier', 50.0)

            if sl_mult <= 0:
                raise ValueError("SL multiplier must be positive")

            # Calculate SL distance in price units
            sl_distance = atr * sl_mult

            if signal_type == 'BUY':
                sl_price = bar['close'] - sl_distance
            else:
                sl_price = bar['close'] + sl_distance

            # Ensure SL is not too close (minimum distance)
            min_sl_pips = self.config.get('min_sl_pips', 5)
            min_sl_distance = min_sl_pips * self.pip_size

            if abs(sl_price - bar['close']) < min_sl_distance:
                if signal_type == 'BUY':
                    sl_price = bar['close'] - min_sl_distance
                else:
                    sl_price = bar['close'] + min_sl_distance

            return sl_price

        except Exception as e:
            logger.error(f"SL calculation error: {e}")
            # Fallback SL
            if signal_type == 'BUY':
                return bar['close'] * 0.99  # 1% below
            else:
                return bar['close'] * 1.01  # 1% above

    def calculate_tp(self, bar, signal_type):
        """Calculate take profit with proper pip conversion"""
        try:
            tp_mode = self.config.get('tp_mode', 'FixedDollar')

            if tp_mode == 'FixedDollar':
                tp_dollar = self.config.get('tp_dollar_amount', 0.8)
                if tp_dollar <= 0:
                    raise ValueError("TP dollar amount must be positive")

                # Convert dollar amount to pip distance
                tp_pips = tp_dollar / self.pip_value
                tp_distance = tp_pips * self.pip_size

            elif tp_mode == 'RiskReward':
                # Use risk-reward ratio based on SL distance
                sl_distance = abs(bar['close'] - self.calculate_sl(bar, signal_type))
                rr_ratio = self.config.get('risk_reward_ratio', 2.0)
                if rr_ratio <= 0:
                    raise ValueError("Risk-reward ratio must be positive")

                tp_distance = sl_distance * rr_ratio

            else:
                raise ValueError(f"Unknown TP mode: {tp_mode}")

            # Calculate TP price
            if signal_type == 'BUY':
                tp_price = bar['close'] + tp_distance
            else:
                tp_price = bar['close'] - tp_distance

            return tp_price

        except Exception as e:
            logger.error(f"TP calculation error: {e}")
            # Fallback TP
            if signal_type == 'BUY':
                return bar['close'] * 1.005  # 0.5% above
            else:
                return bar['close'] * 0.995  # 0.5% below
    
    def calculate_profit(self, current_price):
        """Calculate current profit for open position"""
        if not self.open_position:
            return 0

        try:
            pos = self.open_position
            volume = pos.get('volume', self.config.get('default_volume', 0.01))

            if pos['type'] == 'BUY':
                pips = (current_price - pos['entry_price']) / self.pip_size
            else:
                pips = (pos['entry_price'] - current_price) / self.pip_size

            # Calculate profit using proper pip value
            profit = pips * self.pip_value

            # Subtract commission if applicable
            commission = pos.get('commission', 0)
            if commission > 0:
                profit -= commission

            return profit

        except Exception as e:
            logger.error(f"Profit calculation error: {e}")
            return 0
    
    def close_position(self, bar, reason):
        """Close open position with commission and slippage"""
        if not self.open_position:
            return

        try:
            pos = self.open_position

            # Apply slippage to exit price
            slippage = self.slippage_pips * self.pip_size
            if pos['type'] == 'BUY':
                exit_price = bar['close'] - slippage  # Worse price for exit
            else:
                exit_price = bar['close'] + slippage

            # Calculate final profit
            profit = self.calculate_profit(exit_price)

            # Apply commission for closing
            commission = pos.get('commission', 0)
            if commission > 0:
                profit -= commission
                self.balance -= commission

            # Update balance
            self.balance += profit

            # Record trade
            duration = bar['time'] - pos['entry_time']
            duration_min = int(duration.total_seconds() / 60)

            trade = {
                'entry_time': pos['entry_time'],
                'exit_time': bar['time'],
                'type': pos['type'],
                'entry_price': pos['entry_price'],
                'exit_price': exit_price,
                'profit': profit,
                'duration': f"{duration_min} min",
                'reason': reason,
                'volume': pos.get('volume', self.config.get('default_volume', 0.01)),
                'commission': commission * 2,  # Total commission (entry + exit)
                'symbol': self.config.get('symbol', 'UNKNOWN'),
                'ml_prediction': pos.get('ml_prediction', ''),
                'ml_confidence': pos.get('ml_confidence', 0)
            }

            self.trades.append(trade)
            self.open_position = None

            logger.debug(f"Closed {pos['type']} position: P&L ${profit:.2f}, reason: {reason}")

        except Exception as e:
            logger.error(f"Position close error: {e}")
            # Force close with basic calculation
            pos = self.open_position
            profit = self.calculate_profit(bar['close'])
            self.balance += profit
            self.trades.append({
                'entry_time': pos['entry_time'],
                'exit_time': bar['time'],
                'type': pos['type'],
                'entry_price': pos['entry_price'],
                'exit_price': bar['close'],
                'profit': profit,
                'duration': "Error",
                'reason': f"Error: {reason}",
                'volume': pos.get('volume', 0.01),
                'commission': 0,
                'symbol': self.config.get('symbol', 'UNKNOWN'),
                'ml_prediction': pos.get('ml_prediction', ''),
                'ml_confidence': pos.get('ml_confidence', 0)
            })
            self.open_position = None
    
    def update_equity(self, bar):
        """Update equity curve with validation"""
        try:
            current_equity = self.balance

            if self.open_position:
                floating_profit = self.calculate_profit(bar['close'])
                if not pd.isnull(floating_profit) and not np.isinf(floating_profit):
                    current_equity += floating_profit

            # Ensure equity is valid
            if pd.isnull(current_equity) or np.isinf(current_equity):
                current_equity = self.balance  # Fallback to closed balance

            self.equity = current_equity

            # Add to equity curve with validation
            if not pd.isnull(bar['time']):
                self.equity_curve.append({'time': bar['time'], 'equity': current_equity})

            # Update drawdown with safe division
            if current_equity > self.peak_equity:
                self.peak_equity = current_equity

            if self.peak_equity > 0:
                drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
                if drawdown > 0 and drawdown < 100 and not np.isinf(drawdown):
                    if drawdown > self.max_drawdown:
                        self.max_drawdown = drawdown

        except Exception as e:
            logger.error(f"Equity update error: {e}")
            # Continue with last known equity
    
    def calculate_results(self):
        """Calculate comprehensive backtest results"""
        total_trades = len(self.trades)

        logger.info(f"Calculating results for {total_trades} trades")

        if total_trades == 0:
            return {
                'total_trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'net_pnl': 0,
                'gross_profit': 0,
                'gross_loss': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'sharpe_ratio': 0,
                'sortino_ratio': 0,
                'calmar_ratio': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_trade': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'avg_duration': "0 min",
                'total_commission': 0,
                'return_pct': 0,
                'annualized_return': 0,
                'trades': []
            }

        # Calculate basic metrics
        wins = sum(1 for t in self.trades if t['profit'] > 0)
        losses = total_trades - wins
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

        # P&L calculations
        total_pnl = self.balance - self.initial_balance
        gross_profit = sum(t['profit'] for t in self.trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in self.trades if t['profit'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')

        # Trade statistics
        profits = [t['profit'] for t in self.trades]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        avg_trade = np.mean(profits) if profits else 0

        winning_trades = [t['profit'] for t in self.trades if t['profit'] > 0]
        losing_trades = [t['profit'] for t in self.trades if t['profit'] < 0]

        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0

        # Commission
        total_commission = sum(t.get('commission', 0) for t in self.trades)

        # Return percentage
        return_pct = (total_pnl / self.initial_balance) * 100 if self.initial_balance > 0 else 0

        # Duration statistics
        durations = []
        for t in self.trades:
            try:
                if isinstance(t['duration'], str) and 'min' in t['duration']:
                    durations.append(int(t['duration'].split()[0]))
                else:
                    durations.append(0)
            except:
                durations.append(0)

        avg_duration = f"{int(np.mean(durations))} min" if durations else "0 min"

        # Risk metrics
        max_drawdown_pct = self.max_drawdown if not np.isinf(self.max_drawdown) else 0

        # Sharpe ratio (annualized) with safe division
        sharpe_ratio = 0
        if len(self.equity_curve) > 1:
            try:
                equity_returns = np.diff([e['equity'] for e in self.equity_curve])
                equity_returns = equity_returns[~np.isnan(equity_returns)]  # Remove NaN
                equity_returns = equity_returns[~np.isinf(equity_returns)]  # Remove inf

                if len(equity_returns) > 1:
                    mean_ret = np.mean(equity_returns)
                    std_ret = np.std(equity_returns)
                    if std_ret > 0:
                        sharpe_ratio = (mean_ret / std_ret) * np.sqrt(252)
                        if np.isinf(sharpe_ratio) or np.isnan(sharpe_ratio):
                            sharpe_ratio = 0
            except Exception as e:
                logger.debug(f"Sharpe calculation error: {e}")
                sharpe_ratio = 0

        # Sortino ratio (downside deviation) with safe division
        sortino_ratio = 0
        if len(self.equity_curve) > 1:
            try:
                equity_returns = np.diff([e['equity'] for e in self.equity_curve])
                equity_returns = equity_returns[~np.isnan(equity_returns)]
                equity_returns = equity_returns[~np.isinf(equity_returns)]

                if len(equity_returns) > 1:
                    mean_ret = np.mean(equity_returns)
                    downside_returns = equity_returns[equity_returns < 0]

                    if len(downside_returns) > 0:
                        downside_std = np.std(downside_returns)
                        if downside_std > 0:
                            sortino_ratio = (mean_ret / downside_std) * np.sqrt(252)
                            if np.isinf(sortino_ratio) or np.isnan(sortino_ratio):
                                sortino_ratio = 0
                    else:
                        sortino_ratio = float('inf') if mean_ret > 0 else 0
            except Exception as e:
                logger.debug(f"Sortino calculation error: {e}")
                sortino_ratio = 0

        # Calmar ratio (return / max drawdown)
        calmar_ratio = 0
        if max_drawdown_pct > 0 and not np.isinf(max_drawdown_pct):
            calmar_ratio = abs(return_pct / max_drawdown_pct) if return_pct != 0 else 0
            if np.isinf(calmar_ratio) or np.isnan(calmar_ratio):
                calmar_ratio = 0

        # Annualized return
        annualized_return = return_pct  # Simple return for now

        # Expected payoff
        expectancy = 0
        if total_trades > 0:
            if avg_win > 0 or avg_loss != 0:
                expectancy = (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)

        # ✅ ML ANALYSIS METRICS
        ml_trades = sum(1 for t in self.trades if t.get('ml_prediction', ''))
        ml_accuracy = 0
        ml_predicted_wins = 0
        ml_predicted_losses = 0
        ml_avg_confidence = 0
        
        if ml_trades > 0:
            # Calculate ML prediction accuracy
            ml_correct = 0
            for t in self.trades:
                if t.get('ml_prediction', ''):
                    ml_pred = t.get('ml_prediction', '')
                    actual_type = t.get('type', '')
                    if ml_pred == actual_type and t['profit'] > 0:
                        ml_correct += 1
                    elif ml_pred != actual_type and t['profit'] < 0:
                        ml_correct += 1
            
            ml_accuracy = (ml_correct / ml_trades * 100) if ml_trades > 0 else 0
            
            # Count ML predicted wins/losses
            ml_predicted_wins = sum(1 for t in self.trades if t.get('ml_prediction', '') and t['profit'] > 0)
            ml_predicted_losses = sum(1 for t in self.trades if t.get('ml_prediction', '') and t['profit'] <= 0)
            
            # Average confidence
            confidences = [t.get('ml_confidence', 0) for t in self.trades if t.get('ml_confidence', 0) > 0]
            ml_avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0

        results = {
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'net_pnl': total_pnl - total_commission,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'profit_factor': profit_factor,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'best_trade': best_trade,
            'worst_trade': worst_trade,
            'avg_trade': avg_trade,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'expectancy': expectancy,
            'avg_duration': avg_duration,
            'total_commission': total_commission,
            'return_pct': return_pct,
            'annualized_return': annualized_return,
            'ml_trades': ml_trades,
            'ml_accuracy': ml_accuracy,
            'ml_predicted_wins': ml_predicted_wins,
            'ml_predicted_losses': ml_predicted_losses,
            'ml_avg_confidence': ml_avg_confidence,
            'trades': self.trades,
            'equity_curve': self.equity_curve,
            'symbol': self.config.get('symbol', 'UNKNOWN'),
            'initial_balance': self.initial_balance,
            'final_balance': self.balance
        }

        logger.info(f"Results calculated: P&L ${total_pnl:.2f}, Win Rate {win_rate:.1f}%, Sharpe {sharpe_ratio:.2f}")

        return results