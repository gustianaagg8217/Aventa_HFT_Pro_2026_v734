"""
Strategy Backtester
Backtests trading strategy with historical data
"""

import MetaTrader5 as mt5
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import deque
import time


class StrategyBacktester:
    
    def __init__(self, config, initial_balance=10000):
        """Initialize backtester with ISOLATED config and balance"""
        import copy
        
        # ✅ CRITICAL:  Deep copy config untuk isolasi penuh
        self.config = copy.deepcopy(config)
        
        # ✅ CRITICAL: Use GUI initial_balance (NEVER use account balance!)
        self.initial_balance = float(initial_balance)
        self.balance = float(initial_balance)
        self.equity = float(initial_balance)
        
        self.trades = []
        self.open_position = None
        
        # Performance tracking
        self.equity_curve = []
        self.peak_equity = float(initial_balance)
        self.max_drawdown = 0
        
        # ✅ DEBUG LOG (remove after testing)
        print(f"\n{'='*60}")
        print(f"🔧 BACKTESTER INITIALIZED (ISOLATED)")
        print(f"{'='*60}")
        print(f"Symbol: {self.config.get('symbol', 'N/A')}")
        print(f"Initial Balance: ${self.initial_balance:,.2f}")
        print(f"Magic Number: {self.config.get('magic_number', 'N/A')}")
        print(f"Volume:  {self.config.get('default_volume', 'N/A')}")
        print(f"{'='*60}\n")
        
    def run_backtest(self, start_date, end_date, progress_callback=None, cancel_check=None):
        """Run backtest on historical data"""
        try:
            # Initialize MT5
            if not mt5.initialize():
                raise Exception("MT5 initialization failed")
            
            symbol = self.config['symbol']
            
            # Get historical data
            if progress_callback:
                progress_callback(10, "Fetching historical data...")
            
            # Get M1 data
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, start_date, end_date)
            
            if rates is None or len(rates) == 0:
                raise Exception(f"No historical data for {symbol}")
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            if progress_callback:
                progress_callback(20, f"Loaded {len(df)} bars")
            
            # Calculate indicators
            if progress_callback:
                progress_callback(30, "Calculating indicators...")
            
            df = self.calculate_indicators(df)
            
            # Run simulation
            if progress_callback: 
                progress_callback(40, "Running simulation...")
            
            total_bars = len(df)
            
            for i in range(50, total_bars):  # Start after indicator warmup
                # Check cancel
                if cancel_check and cancel_check():
                    return None
                
                # Progress update every 100 bars
                if i % 100 == 0:
                    progress_pct = 40 + (i / total_bars * 50)
                    if progress_callback:
                        progress_callback(progress_pct, f"Processing bar {i}/{total_bars}")
                
                current_bar = df.iloc[i]
                
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
            
            return results
            
        except Exception as e: 
            raise Exception(f"Backtest error: {e}")
        finally:
            mt5.shutdown()
    
    def calculate_indicators(self, df):
        """Calculate technical indicators"""
        # EMA
        ema_fast = self.config.get('ema_fast_period', 7)
        ema_slow = self.config.get('ema_slow_period', 21)
        df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
        
        # RSI
        rsi_period = self.config.get('rsi_period', 7)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # ATR
        atr_period = self.config.get('atr_period', 14)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['atr'] = true_range.rolling(atr_period).mean()
        
        # Momentum
        momentum_period = self.config.get('momentum_period', 5)
        df['momentum'] = df['close'].diff(momentum_period)
        
        # Volatility
        df['volatility'] = df['close'].rolling(20).std() / df['close'].rolling(20).mean()
        
        return df
    
    def check_entry(self, bar, index, df):
        """Check for entry signal"""
        try:
            # Get signal strength
            signal_strength, signal_type = self.calculate_signal(bar, index, df)
            
            min_signal = self.config.get('min_signal_strength', 0.45)
            
            if abs(signal_strength) >= min_signal:
                # Check spread
                spread = bar['spread'] * 0.00001  # Convert to decimal
                max_spread = self.config.get('max_spread', 0.12)
                
                if spread <= max_spread:
                    # Check volatility
                    if bar['volatility'] <= self.config.get('max_volatility', 0.005):
                        # Open position
                        self.open_position = {
                            'type': signal_type,
                            'entry_price': bar['close'],
                            'entry_time': bar['time'],
                            'entry_bar': index,
                            'sl': self.calculate_sl(bar, signal_type),
                            'tp': self.calculate_tp(bar, signal_type),
                        }
                        
        except Exception as e:
            pass
    
    def check_exit(self, bar, index, df):
        """Check for exit signal"""
        try:
            if not self.open_position:
                return
            
            pos = self.open_position
            current_price = bar['close']
            
            # Check SL
            if pos['type'] == 'BUY':
                if current_price <= pos['sl']: 
                    self.close_position(bar, "Stop Loss")
                    return
                elif current_price >= pos['tp']: 
                    self.close_position(bar, "Take Profit")
                    return
            else:  # SELL
                if current_price >= pos['sl']: 
                    self.close_position(bar, "Stop Loss")
                    return
                elif current_price <= pos['tp']:
                    self.close_position(bar, "Take Profit")
                    return
            
            # Check max floating loss
            profit = self.calculate_profit(current_price)
            max_loss = self.config.get('max_floating_loss', 5.0)
            
            if profit < -max_loss:
                self.close_position(bar, "Max Floating Loss")
                return
            
            # Check TP target
            tp_target = self.config.get('max_floating_profit', 0.5)
            if profit >= tp_target:
                self.close_position(bar, "TP Target Reached")
                return
            
        except Exception as e:
            pass
    
    def calculate_signal(self, bar, index, df):
        """Calculate signal strength"""
        strength = 0
        signal_type = None
        
        # EMA crossover
        if bar['ema_fast'] > bar['ema_slow']:
            strength += 0.3
            signal_type = 'BUY'
        elif bar['ema_fast'] < bar['ema_slow']:
            strength += 0.3
            signal_type = 'SELL'
        
        # RSI
        rsi_ob = self.config.get('rsi_overbought', 68)
        rsi_os = self.config.get('rsi_oversold', 32)
        
        if bar['rsi'] < rsi_os:
            strength += 0.2
            signal_type = 'BUY'
        elif bar['rsi'] > rsi_ob: 
            strength += 0.2
            signal_type = 'SELL'
        
        # Momentum
        if bar['momentum'] > 0:
            strength += 0.1
            if signal_type != 'SELL':
                signal_type = 'BUY'
        elif bar['momentum'] < 0:
            strength += 0.1
            if signal_type != 'BUY':
                signal_type = 'SELL'
        
        # Adjust for SELL
        if signal_type == 'SELL':
            strength = -strength
        
        return strength, signal_type
    
    def calculate_sl(self, bar, signal_type):
        """Calculate stop loss"""
        atr = bar['atr']
        sl_mult = self.config.get('sl_multiplier', 50.0)
        sl_distance = atr * sl_mult * 0.00001  # Convert to price
        
        if signal_type == 'BUY': 
            return bar['close'] - sl_distance
        else: 
            return bar['close'] + sl_distance
    
    def calculate_tp(self, bar, signal_type):
        """Calculate take profit"""
        tp_mode = self.config.get('tp_mode', 'FixedDollar')
        
        if tp_mode == 'FixedDollar':
            tp_dollar = self.config.get('tp_dollar_amount', 0.8)
            volume = self.config.get('default_volume', 0.01)
            # For GOLD:  1 pip = $0.01 per 0.01 lot
            pip_value = 0.01 * (volume / 0.01)
            tp_pips = tp_dollar / pip_value
            tp_distance = tp_pips * 0.00001
            
            if signal_type == 'BUY':
                return bar['close'] + tp_distance
            else:
                return bar['close'] - tp_distance
        else:  # RiskReward
            sl_distance = abs(bar['close'] - self.calculate_sl(bar, signal_type))
            rr_ratio = self.config.get('risk_reward_ratio', 2.0)
            tp_distance = sl_distance * rr_ratio
            
            if signal_type == 'BUY': 
                return bar['close'] + tp_distance
            else: 
                return bar['close'] - tp_distance
    
    def calculate_profit(self, current_price):
        """Calculate current profit for open position"""
        if not self.open_position:
            return 0
        
        pos = self.open_position
        volume = self.config.get('default_volume', 0.01)
        
        if pos['type'] == 'BUY': 
            pips = (current_price - pos['entry_price']) / 0.00001
        else:
            pips = (pos['entry_price'] - current_price) / 0.00001
        
        # For GOLD: 1 pip = $0.01 per 0.01 lot
        pip_value = 0.01 * (volume / 0.01)
        profit = pips * pip_value
        
        return profit
    
    def close_position(self, bar, reason):
        """Close open position"""
        if not self.open_position:
            return
        
        pos = self.open_position
        exit_price = bar['close']
        profit = self.calculate_profit(exit_price)
        
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
            'reason': reason
        }
        
        self.trades.append(trade)
        self.open_position = None
    
    def update_equity(self, bar):
        """Update equity curve"""
        current_equity = self.balance
        
        if self.open_position:
            current_equity += self.calculate_profit(bar['close'])
        
        self.equity = current_equity
        self.equity_curve.append({'time': bar['time'], 'equity': current_equity})
        
        # Update drawdown
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        drawdown = ((self.peak_equity - current_equity) / self.peak_equity) * 100
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown
    
    def calculate_results(self):
        """Calculate backtest results"""
        total_trades = len(self.trades)
        
        # ✅ DEBUG LOG
        print(f"\n{'='*60}")
        print(f"📊 BACKTEST RESULTS CALCULATION")
        print(f"{'='*60}")
        print(f"Total Trades: {total_trades}")
        print(f"Starting Balance: ${self.initial_balance:,.2f}")
        print(f"Final Balance:  ${self.balance:,.2f}")
        print(f"Net P&L: ${self.balance - self.initial_balance:,.2f}")
        print(f"{'='*60}\n")
        
        if total_trades == 0:
            return {
                'total_trades':  0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'best_trade': 0,
                'worst_trade': 0,
                'avg_trade': 0,
                'avg_duration': "0 min",
                'trades':  []
            }
        
        # Calculate metrics
        wins = sum(1 for t in self.trades if t['profit'] > 0)
        losses = total_trades - wins
        win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
        
        # ✅ FIX:  P&L harus berdasarkan balance change (bukan sum trades)
        total_pnl = self.balance - self.initial_balance
        
        gross_profit = sum(t['profit'] for t in self.trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in self.trades if t['profit'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        profits = [t['profit'] for t in self.trades]
        best_trade = max(profits) if profits else 0
        worst_trade = min(profits) if profits else 0
        avg_trade = np.mean(profits) if profits else 0
        
        # Sharpe ratio (simplified)
        returns = np.diff([e['equity'] for e in self.equity_curve])
        sharpe_ratio = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 0 and np.std(returns) > 0 else 0
        
        # Average duration
        durations = [int(t['duration'].split()[0]) for t in self.trades]
        avg_duration = f"{int(np.mean(durations))} min" if durations else "0 min"
        
        return {
            'total_trades':  total_trades,
            'wins': wins,
            'losses':  losses,
            'win_rate': win_rate,
            'total_pnl': total_pnl,  # ✅ Dari balance change
            'profit_factor': profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'best_trade':  best_trade,
            'worst_trade': worst_trade,
            'avg_trade': avg_trade,
            'avg_duration': avg_duration,
            'trades': self.trades
        }