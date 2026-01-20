"""
Aventa HFT Pro 2026 - Advanced Risk Management System
Sophisticated risk controls and portfolio management
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
# Add these imports
from trade_database import TradeDatabase

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Real-time risk metrics"""
    current_exposure: float
    position_count: int
    daily_pnl: float
    daily_trades: int
    daily_volume: float
    win_rate: float
    avg_profit: float
    avg_loss: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    risk_level: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'


@dataclass
class TradeRecord:
    """Individual trade record"""
    timestamp: datetime
    symbol: str
    trade_type: str
    volume: float
    open_price: float
    close_price: float
    profit: float
    duration: float
    reason: str


class RiskManager:
    """Advanced risk management for HFT"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Risk limits
        self.max_daily_loss = config.get('max_daily_loss', 1000)
        self.max_daily_trades = config.get('max_daily_trades', 500)
        self.max_daily_volume = config.get('max_daily_volume', 10.0)
        self.max_position_size = config.get('max_position_size', 1.0)
        self.max_positions = config.get('max_positions', 3)
        self.max_drawdown_pct = config.get('max_drawdown_pct', 10)
        
        # Position sizing
        self.risk_per_trade = config.get('risk_per_trade', 0.01)  # 1% of account
        self.use_kelly_criterion = False  # DISABLED for HFT stability
        
        # Trading state
        self.trade_history: List[TradeRecord] = []
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_volume = 0.0
        self.peak_balance = 0.0
        self.current_drawdown = 0.0
        
        # Circuit breakers
        self.trading_enabled = True
        self.circuit_breaker_triggered = False
        self.last_reset_date = datetime.now().date()
        
        # Statistics
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0
        self.total_loss = 0.0

        # Last circuit breaker reason
        self.last_circuit_reason = None

    # ✅ NEW: Add database persistence
        db_path = config.get('db_path', 'trades.db')
        self.db = TradeDatabase(db_path)
        self.bot_id = config.get('_bot_id', 'default_bot')
    
    def reset_daily_stats(self, current_account_balance: float = 0.0):
        """Reset daily statistics"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            logger.info(f"Resetting daily stats. Yesterday PnL: {self.daily_pnl:.2f}")
            
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.daily_volume = 0.0
            # ✅ FIX: Set peak_balance to current account balance (not 0.0)
            # This ensures drawdown calculation is based on today's starting balance
            if current_account_balance > 0:
                self.peak_balance = current_account_balance
                logger.info(f"✓ Daily peak balance reset to current: ${self.peak_balance:.2f}")
            else:
                self.peak_balance = 0.0
            self.current_drawdown = 0.0  # Reset current drawdown
            self.last_reset_date = today
            
            # Reset circuit breaker if new day
            if self.circuit_breaker_triggered:
                logger.info("Circuit breaker reset for new trading day")
                self.circuit_breaker_triggered = False
                self.trading_enabled = True
    
    def check_risk_limits(self, account_balance: float = 0.0) -> Tuple[bool, str]:
        """
        Check if trading is allowed based on risk limits
        Returns: (allowed, reason)
        """
        # ✅ FIX: Pass account_balance to reset_daily_stats
        self.reset_daily_stats(account_balance)
        
        # Check circuit breaker
        if self.circuit_breaker_triggered:
            return False, "Circuit breaker triggered - trading halted"
        
        # Check daily loss limit
        if self.daily_pnl <= -self.max_daily_loss:
            self.trigger_circuit_breaker("Daily loss limit reached")
            return False, f"Daily loss limit reached: {self.daily_pnl:.2f}"
        
        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached: {self.daily_trades}/{self.max_daily_trades}"
        
        # Check daily volume limit
        if self.daily_volume >= self.max_daily_volume:
            return False, f"Daily volume limit reached: {self.daily_volume:.2f}/{self.max_daily_volume:.2f}"
        
        # Check drawdown
        if self.current_drawdown >= self.max_drawdown_pct:
            self.trigger_circuit_breaker(f"Max drawdown exceeded: {self.current_drawdown:.2f}%")
            return False, f"Max drawdown exceeded: {self.current_drawdown:.2f}%"
        
        return True, "OK"
    
    def trigger_circuit_breaker(self, reason: str):
        """Trigger emergency circuit breaker (no UI)"""
        logger.critical(f"🚨 CIRCUIT BREAKER TRIGGERED: {reason}")
        self.circuit_breaker_triggered = True
        self.trading_enabled = False
        self.last_circuit_reason = reason

    def calculate_position_size(self, 
                                account_balance: float,
                                entry_price: float,
                                stop_loss: float,
                                signal_confidence: float = 1.0) -> float:
        """
        Calculate optimal position size based on risk parameters
        """
        # Risk amount per trade
        risk_amount = account_balance * self.risk_per_trade
        
        # Calculate position size based on stop loss distance
        price_risk = abs(entry_price - stop_loss)
        if price_risk == 0:
            return 0.01  # Minimum size
        
        # Basic position size
        position_size = risk_amount / price_risk
        
        # Apply Kelly Criterion if enabled
        if self.use_kelly_criterion and len(self.trade_history) > 30:
            kelly_factor = self.calculate_kelly_criterion()
            position_size *= kelly_factor
        
        # Adjust by signal confidence
        position_size *= signal_confidence
        
        # Apply limits
        position_size = max(0.01, min(position_size, self.max_position_size))
        
        # Round to valid lot size
        position_size = round(max(0.01, position_size), 2)
        return position_size
    
    def calculate_kelly_criterion(self) -> float:
        """
        Calculate Kelly Criterion for position sizing
        Kelly % = (Win% * Avg Win / Avg Loss) - Loss% / (Avg Win / Avg Loss)
        """
        if self.wins + self.losses == 0:
            return 1.0
        
        win_rate = self.wins / (self.wins + self.losses)
        loss_rate = 1 - win_rate
        
        if self.losses == 0 or self.total_loss == 0:
            return 1.0
        
        avg_win = self.total_profit / max(self.wins, 1)
        avg_loss = abs(self.total_loss) / max(self.losses, 1)
        
        if avg_loss == 0:
            return 1.0
        
        win_loss_ratio = avg_win / avg_loss
        
        kelly_pct = (win_rate * win_loss_ratio - loss_rate) / win_loss_ratio
        
        # Use fractional Kelly (25% of full Kelly for safety)
        kelly_pct = max(0.1, min(kelly_pct * 0.25, 1.0))
        
        return kelly_pct
    
    def validate_trade(self, 
                      trade_type: str,
                      volume: float,
                      current_positions: int,
                      account_balance: float = 0.0) -> Tuple[bool, str]:
        """
        Validate if trade should be executed
        Returns: (allowed, reason)
        """
        # ✅ FIX: Pass account_balance for drawdown reset
        # Check risk limits
        allowed, reason = self.check_risk_limits(account_balance)
        if not allowed:
            return False, reason
        
        # Check position limit
        if current_positions >= self.max_positions:
            logger.warning(
                f"MAX POSITION LIMIT HIT: {current_positions}/{self.max_positions}"
            )
            return False, f"Max positions reached: {current_positions}/{self.max_positions}"
        
        # Check volume
        if volume > self.max_position_size:
            return False, f"Volume exceeds limit: {volume} > {self.max_position_size}"
        
        if volume < 0.01:
            return False, "Volume too small"
        
        return True, "OK"
    
    def record_trade(self, trade: TradeRecord):
        """Record completed trade for statistics"""
        self.trade_history.append(trade)
        
        # Update daily stats
        self.daily_pnl += trade.profit
        self.daily_trades += 1
        self.daily_volume += trade.volume
        
        # Update win/loss stats
        if trade.profit > 0:
            self.wins += 1
            self.total_profit += trade.profit
        elif trade.profit < 0:
            self.losses += 1
            self.total_loss += trade.profit
        
        # Note: Drawdown is now calculated in get_risk_metrics based on actual account balance
        
        # Log trade
        status = "WIN" if trade.profit > 0 else "LOSS"
        logger.info(f"Trade recorded: {status} | "
                   f"Profit: {trade.profit:.2f} | "
                   f"Daily PnL: {self.daily_pnl:.2f} | "
                   f"Trades today: {self.daily_trades} | "
                   f"Volume today: {self.daily_volume:.2f}")
        
        # ✅ NEW:  Persist to database
        try:
            self.db.record_trade(self.bot_id, {
                'timestamp': trade.timestamp.timestamp(),
                'symbol': trade.symbol,
                'trade_type': trade.trade_type,
                'volume': trade.volume,
                'open_price': trade.open_price,
                'close_price':  trade.close_price,
                'profit': trade.profit,
                'duration': trade.duration,
                'reason': trade.reason,
                'magic_number':  self.config.get('magic_number')
            })
        except Exception as e:
            logger.error(f"Failed to persist trade: {e}")
    
    def calculate_dynamic_stop_loss(self,
                                   entry_price: float,
                                   direction: str,
                                   volatility: float,
                                   spread: float) -> float:
        """Calculate dynamic stop loss based on market conditions"""
        
        # Base SL distance (2x ATR or volatility)
        sl_distance = max(volatility * 2, spread * 3)
        
        # Adjust based on configuration
        sl_multiplier = self.config.get('sl_multiplier', 1.0)
        sl_distance *= sl_multiplier
        
        # Calculate SL price
        if direction == 'BUY':
            stop_loss = entry_price - sl_distance
        else:
            stop_loss = entry_price + sl_distance
        
        return stop_loss
    
    def calculate_dynamic_take_profit(self,
                                     entry_price: float,
                                     stop_loss: float,
                                     direction: str,
                                     signal_strength: float) -> float:
        """Calculate dynamic take profit based on risk-reward"""
        
        # Base risk-reward ratio
        base_rr = self.config.get('risk_reward_ratio', 2.0)
        
        # Adjust RR based on signal strength
        rr_ratio = base_rr * signal_strength
        
        # Calculate TP distance
        sl_distance = abs(entry_price - stop_loss)
        tp_distance = sl_distance * rr_ratio
        
        # Calculate TP price
        if direction == 'BUY':
            take_profit = entry_price + tp_distance
        else:
            take_profit = entry_price - tp_distance
        
        return take_profit
    
    def should_trail_stop(self, 
                         entry_price: float,
                         current_price: float,
                         stop_loss: float,
                         direction: str) -> Optional[float]:
        """
        Determine if stop loss should be trailed
        Returns new SL price if trailing is needed, None otherwise
        """
        if not self.config.get('use_trailing_stop', True):
            return None
        
        trail_start_pct = self.config.get('trail_start_pct', 0.5)  # Start trailing at 50% of TP
        trail_distance_pct = self.config.get('trail_distance_pct', 0.3)  # Trail at 30% of profit
        
        if direction == 'BUY':
            profit_pct = (current_price - entry_price) / entry_price
            
            if profit_pct > trail_start_pct * 0.01:
                new_sl = current_price * (1 - trail_distance_pct * 0.01)
                
                if new_sl > stop_loss:
                    return new_sl
        
        else:  # SELL
            profit_pct = (entry_price - current_price) / entry_price
            
            if profit_pct > trail_start_pct * 0.01:
                new_sl = current_price * (1 + trail_distance_pct * 0.01)
                
                if new_sl < stop_loss:
                    return new_sl
        
        return None
    
    def get_risk_metrics(self, account_balance: float, mt5_positions=None) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics
        
        Drawdown Formula:
        Current Drawdown = (Floating Loss / Initial Balance) * 100
        Where:
            - Floating Loss = Peak Balance - Current Balance
            - Initial Balance = Starting balance at day beginning
            
        Example:
            - Peak Balance: $1000
            - Current Balance: $980  
            - Floating Loss: $1000 - $980 = $20
            - Current Drawdown: ($20 / $1000) * 100 = 2.0%
        """
        # Update daily peak balance for drawdown calculation
        if self.peak_balance == 0.0:
            # Initialize peak balance at start of day
            self.peak_balance = account_balance
        elif account_balance > self.peak_balance:
            # Update peak balance if current balance is higher
            self.peak_balance = account_balance
        
        # Calculate daily drawdown based on account balance
        # Formula: Current Drawdown = (Floating - Balance) / Balance * 100
        # Where: Floating = Equity - Balance (floating profit/loss)
        # And: Balance = account balance
        if self.peak_balance > 0:
            # Floating P&L = current equity - balance
            # When equity drops below balance, floating becomes negative (drawdown)
            floating_pnl = (self.peak_balance - account_balance)  # Loss from peak
            
            # Drawdown percentage = Floating Loss / Peak Balance * 100
            self.current_drawdown = (floating_pnl / self.peak_balance) * 100
            
            # Ensure drawdown is never negative (can't have positive drawdown)
            self.current_drawdown = max(0.0, self.current_drawdown)
        else:
            self.current_drawdown = 0.0
        
        # Calculate position exposure and count from MT5
        current_exposure = 0.0
        position_count = 0
        
        if mt5_positions:
            magic = self.config.get('magic_number', 2026002)
            for pos in mt5_positions:
                if pos.magic == magic:
                    # Exposure = volume * current_price
                    current_exposure += pos.volume * pos.price_current
                    position_count += 1
        
        # Calculate metrics
        if len(self.trade_history) == 0:
            win_rate = 0
            avg_profit = 0
            avg_loss = 0
            profit_factor = 0
        else:
            win_rate = self.wins / (self.wins + self.losses) if (self.wins + self.losses) > 0 else 0
            avg_profit = self.total_profit / max(self.wins, 1)
            avg_loss = abs(self.total_loss) / max(self.losses, 1)
            
            if abs(self.total_loss) > 0:
                profit_factor = self.total_profit / abs(self.total_loss)
            else:
                profit_factor = float('inf') if self.total_profit > 0 else 0
        
        # Calculate Sharpe ratio (simplified)
        if len(self.trade_history) > 10:
            returns = [t.profit / account_balance for t in self.trade_history[-100:] if account_balance > 0]
            if returns:
                sharpe_ratio = np.mean(returns) / (np.std(returns) + 1e-10) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        # Determine risk level
        if self.circuit_breaker_triggered:
            risk_level = 'CRITICAL'
        elif self.current_drawdown > self.max_drawdown_pct * 0.8:
            risk_level = 'HIGH'
        elif abs(self.daily_pnl) > self.max_daily_loss * 0.7:
            risk_level = 'HIGH'
        elif abs(self.daily_pnl) > self.max_daily_loss * 0.5:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return RiskMetrics(
            current_exposure=current_exposure,  # Now calculated from MT5 positions
            position_count=position_count,  # Now calculated from MT5 positions
            daily_pnl=self.daily_pnl,
            daily_trades=self.daily_trades,
            daily_volume=self.daily_volume,
            win_rate=win_rate,
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            max_drawdown=self.current_drawdown,
            sharpe_ratio=sharpe_ratio,
            risk_level=risk_level
        )
    
    def get_trading_summary(self) -> Dict:
        """Get comprehensive trading summary"""
        total_trades = self.wins + self.losses

        # ✅ NEW: Add database stats
        try:
            db_stats = self.db.get_daily_stats(self.bot_id)
            summary.update({
                'db_total_trades': db_stats.get('total_trades', 0),
                'db_win_rate': db_stats.get('win_rate', 0),
                'db_total_pnl': db_stats.get('total_pnl', 0)
            })
        except Exception as e:
            logger.error(f"Failed to get DB stats:  {e}")
        
        return summary

        """"     
        return {
            'total_trades': total_trades,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': self.wins / max(total_trades, 1),
            'total_profit': self.total_profit,
            'total_loss': self.total_loss,
            'net_profit': self.total_profit + self.total_loss,
            'profit_factor': self.total_profit / abs(self.total_loss) if self.total_loss != 0 else 0,
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'current_drawdown': self.current_drawdown,
            'circuit_breaker_triggered': self.circuit_breaker_triggered,
            'trading_enabled': self.trading_enabled,
        }
        """   
    
    
    def export_trade_history(self, filename: str = "trade_history.csv"):
        """Export trade history to CSV"""
        if len(self.trade_history) == 0:
            logger.warning("No trades to export")
            return False
        
        try:
            df = pd.DataFrame([
                {
                    'timestamp': t.timestamp,
                    'symbol': t.symbol,
                    'type': t.trade_type,
                    'volume': t.volume,
                    'open_price': t.open_price,
                    'close_price': t.close_price,
                    'profit': t.profit,
                    'duration': t.duration,
                    'reason': t.reason
                }
                for t in self.trade_history
            ])
            
            df.to_csv(filename, index=False)
            logger.info(f"✓ Trade history exported to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting trade history: {e}")
            return False


if __name__ == "__main__":
    # Example usage
    config = {
        'max_daily_loss': 1000,
        'max_daily_trades': 500,
        'max_position_size': 1.0,
        'max_positions': 3,
        'max_drawdown_pct': 10,
        'risk_per_trade': 0.01,
        'use_kelly_criterion': True,
        'risk_reward_ratio': 2.0,
        'sl_multiplier': 1.0,
        'use_trailing_stop': True,
    }
    
    risk_manager = RiskManager(config)
    
    # Simulate some trades
    for i in range(10):
        trade = TradeRecord(
            timestamp=datetime.now(),
            symbol="EURUSD",
            trade_type="BUY" if i % 2 == 0 else "SELL",
            volume=0.01,
            open_price=1.1000,
            close_price=1.1010 if i % 3 != 0 else 1.0990,
            profit=10 if i % 3 != 0 else -10,
            duration=60,
            reason="Test trade"
        )
        risk_manager.record_trade(trade)
    
    # Get summary
    summary = risk_manager.get_trading_summary()
    print("\n=== Trading Summary ===")
    for key, value in summary.items():
        print(f"{key}: {value}")
