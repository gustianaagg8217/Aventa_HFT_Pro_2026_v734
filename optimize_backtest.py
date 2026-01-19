"""
Parameter Optimization for XAUUSD Backtest
Menemukan setingan terbaik dengan grid search
"""

import MetaTrader5 as mt5
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from itertools import product
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BacktestOptimizer:
    def __init__(self):
        self.results = []
        self.best_configs = []
        
    def run_single_backtest(self, config, start_date, end_date):
        """Run single backtest with given config"""
        try:
            from strategy_backtester import StrategyBacktester
            
            backtester = StrategyBacktester(config, initial_balance=500)
            results = backtester.run_backtest(start_date, end_date)
            
            if results:
                return results
            return None
        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return None
    
    def optimize(self, start_date, end_date):
        """Run optimization with grid search"""
        
        # Parameter ranges to test
        ema_fast_periods = [5, 7, 9, 12]
        ema_slow_periods = [15, 21, 28, 35]
        rsi_periods = [5, 7, 9, 14]
        atr_periods = [10, 14, 20]
        take_profit_pips = [3.0, 4.0, 5.0, 6.0, 8.0]
        stop_loss_pips = [5.0, 7.0, 10.0]
        
        total_combinations = (len(ema_fast_periods) * len(ema_slow_periods) * 
                             len(rsi_periods) * len(atr_periods) * 
                             len(take_profit_pips) * len(stop_loss_pips))
        
        logger.info(f"Total combinations to test: {total_combinations}")
        logger.info(f"Testing period: {start_date.date()} to {end_date.date()}")
        
        count = 0
        # Create combinations
        combinations = list(product(
            ema_fast_periods, ema_slow_periods, rsi_periods, atr_periods,
            take_profit_pips, stop_loss_pips
        ))
        
        for i, (ema_fast, ema_slow, rsi_period, atr_period, tp_pips, sl_pips) in enumerate(combinations):
            if ema_fast >= ema_slow:  # Skip invalid combinations
                continue
            
            count += 1
            
            # Create config
            config = {
                'symbol': 'XAUUSD',
                'magic_number': 12345,
                'default_volume': 0.01,
                'ema_fast_period': ema_fast,
                'ema_slow_period': ema_slow,
                'rsi_period': rsi_period,
                'atr_period': atr_period,
                'take_profit_pips': tp_pips,
                'stop_loss_pips': sl_pips,
                'max_floating_loss_pips': 15.0,
                'max_duration_minutes': 1440,
                'commission_per_trade': 0.0,
                'slippage_pips': 0.5
            }
            
            # Run backtest
            results = self.run_single_backtest(config, start_date, end_date)
            
            if results and results.get('total_trades', 0) > 0:
                # Calculate metrics
                metrics = {
                    'config': config,
                    'total_trades': results.get('total_trades', 0),
                    'wins': results.get('wins', 0),
                    'losses': results.get('losses', 0),
                    'win_rate': results.get('win_rate', 0),
                    'total_pnl': results.get('total_pnl', 0),
                    'profit_factor': results.get('profit_factor', 0),
                    'max_drawdown': results.get('max_drawdown', 0),
                    'best_trade': results.get('best_trade', 0),
                    'worst_trade': results.get('worst_trade', 0),
                    'avg_trade': results.get('avg_trade', 0),
                    'sharpe_ratio': results.get('sharpe_ratio', 0),
                    'recovery_factor': results.get('recovery_factor', 0),
                    'avg_duration': results.get('avg_duration', 0)
                }
                
                self.results.append(metrics)
                
                # Progress
                progress = (count / len([c for c in combinations if c[0] < c[1]])) * 100
                if count % 5 == 0:
                    logger.info(f"Progress: {count} tested | Best P&L: ${max([r['total_pnl'] for r in self.results]):.2f}")
        
        return self.results
    
    def get_best_configs(self, top_n=10, metric='total_pnl'):
        """Get top N configurations by metric"""
        if not self.results:
            logger.warning("No results to analyze")
            return []
        
        # Sort by metric
        sorted_results = sorted(self.results, key=lambda x: x.get(metric, 0), reverse=True)
        
        # Filter by valid trades
        valid_results = [r for r in sorted_results if r['total_trades'] >= 10]
        
        self.best_configs = valid_results[:top_n]
        return self.best_configs
    
    def print_results(self, top_n=10):
        """Print best configurations"""
        best = self.get_best_configs(top_n)
        
        if not best:
            logger.warning("No valid configurations found")
            return
        
        print("\n" + "="*150)
        print("TOP 10 BEST CONFIGURATIONS FOR XAUUSD")
        print("="*150)
        
        for rank, result in enumerate(best, 1):
            config = result['config']
            print(f"\n🏆 RANK #{rank}")
            print("-" * 150)
            print(f"EMA: {config['ema_fast_period']}/{config['ema_slow_period']} | "
                  f"RSI: {config['rsi_period']} | "
                  f"ATR: {config['atr_period']} | "
                  f"TP: {config['take_profit_pips']}pips | "
                  f"SL: {config['stop_loss_pips']}pips")
            print(f"├─ Total Trades: {result['total_trades']} | Wins: {result['wins']} | Losses: {result['losses']}")
            print(f"├─ Win Rate: {result['win_rate']:.1f}% | Profit Factor: {result['profit_factor']:.2f}")
            print(f"├─ Total P&L: ${result['total_pnl']:.2f} | Avg Trade: ${result['avg_trade']:.2f}")
            print(f"├─ Best Trade: ${result['best_trade']:.2f} | Worst Trade: ${result['worst_trade']:.2f}")
            print(f"├─ Max Drawdown: {result['max_drawdown']:.2f}% | Sharpe Ratio: {result['sharpe_ratio']:.3f}")
            print(f"└─ Avg Duration: {result['avg_duration']:.0f} min | Recovery Factor: {result['recovery_factor']:.2f}")
        
        print("\n" + "="*150)
    
    def export_results(self, filename='optimization_results.json'):
        """Export results to JSON"""
        if not self.best_configs:
            self.get_best_configs(10)
        
        export_data = []
        for result in self.best_configs:
            config = result['config']
            export_data.append({
                'ema_fast': config['ema_fast_period'],
                'ema_slow': config['ema_slow_period'],
                'rsi_period': config['rsi_period'],
                'atr_period': config['atr_period'],
                'take_profit_pips': config['take_profit_pips'],
                'stop_loss_pips': config['stop_loss_pips'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'total_pnl': result['total_pnl'],
                'profit_factor': result['profit_factor'],
                'max_drawdown': result['max_drawdown'],
                'sharpe_ratio': result['sharpe_ratio']
            })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Results exported to {filename}")


def main():
    # Date range
    end_date = datetime(2026, 1, 19)
    start_date = datetime(2025, 12, 20)
    
    # Initialize optimizer
    optimizer = BacktestOptimizer()
    
    # Run optimization
    logger.info("Starting parameter optimization...")
    optimizer.optimize(start_date, end_date)
    
    # Print results
    optimizer.print_results(top_n=10)
    
    # Export results
    optimizer.export_results('optimization_results.json')
    
    logger.info("Optimization complete!")


if __name__ == '__main__':
    main()
