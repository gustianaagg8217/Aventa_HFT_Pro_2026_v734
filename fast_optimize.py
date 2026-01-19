"""
Fast Backtest Parameter Optimization
Tests multiple configurations to find the best settings
"""

import pandas as pd
import json
import logging
from datetime import datetime, timedelta
from itertools import product
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FastBacktestOptimizer:
    def __init__(self, symbol='XAUUSD', initial_balance=500):
        self.symbol = symbol
        self.initial_balance = initial_balance
        self.results = []
        self.best_configs = []
        
    def run_backtest_with_config(self, config, start_date, end_date):
        """Run backtest with given configuration"""
        try:
            import MetaTrader5 as mt5
            from strategy_backtester import StrategyBacktester
            
            # Create backtester with config
            backtester = StrategyBacktester(config, initial_balance=self.initial_balance)
            results = backtester.run_backtest(start_date, end_date)
            
            return results
        except Exception as e:
            logger.debug(f"Backtest failed for config: {e}")
            return None
    
    def optimize(self, start_date, end_date, verbose=True):
        """Run optimization with grid search"""
        
        # Parameter ranges - smaller for faster testing
        ema_fast_periods = [5, 7, 9]
        ema_slow_periods = [15, 21, 28]
        rsi_periods = [7, 14]
        atr_periods = [10, 14]
        take_profit_pips = [3.0, 5.0, 8.0]
        stop_loss_pips = [5.0, 10.0]
        
        total_combinations = (len(ema_fast_periods) * len(ema_slow_periods) * 
                             len(rsi_periods) * len(atr_periods) * 
                             len(take_profit_pips) * len(stop_loss_pips))
        
        logger.info(f"Total combinations to test: {total_combinations}")
        logger.info(f"Testing period: {start_date.date()} to {end_date.date()}")
        logger.info(f"Symbol: {self.symbol}")
        
        count = 0
        valid_configs = 0
        
        # Create combinations
        combinations = list(product(
            ema_fast_periods, ema_slow_periods, rsi_periods, atr_periods,
            take_profit_pips, stop_loss_pips
        ))
        
        for i, (ema_fast, ema_slow, rsi_period, atr_period, tp_pips, sl_pips) in enumerate(combinations):
            # Skip invalid combinations
            if ema_fast >= ema_slow:
                continue
            
            count += 1
            
            # Create config
            config = {
                'symbol': self.symbol,
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
            results = self.run_backtest_with_config(config, start_date, end_date)
            
            if results and results.get('total_trades', 0) >= 10:
                valid_configs += 1
                
                # Calculate key metrics
                metrics = {
                    'rank': 0,  # Will be set later
                    'ema_fast': ema_fast,
                    'ema_slow': ema_slow,
                    'rsi_period': rsi_period,
                    'atr_period': atr_period,
                    'take_profit_pips': tp_pips,
                    'stop_loss_pips': sl_pips,
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
            
            # Progress logging
            if verbose and count % 3 == 0:
                best_pnl = max([r['total_pnl'] for r in self.results]) if self.results else 0
                logger.info(f"Progress: {count}/{len([c for c in combinations if c[0] < c[1]])} | "
                          f"Valid: {valid_configs} | Best P&L: ${best_pnl:.2f}")
        
        logger.info(f"Tested {count} combinations, found {valid_configs} valid configs")
        return self.results
    
    def get_best_configs(self, top_n=10, metric='total_pnl'):
        """Get top N configurations by metric"""
        if not self.results:
            logger.warning("No results to analyze")
            return []
        
        # Sort by metric (descending for profit, ascending for drawdown)
        if metric == 'max_drawdown':
            sorted_results = sorted(self.results, key=lambda x: x.get(metric, float('inf')))
        else:
            sorted_results = sorted(self.results, key=lambda x: x.get(metric, 0), reverse=True)
        
        self.best_configs = sorted_results[:top_n]
        
        # Add rank
        for i, config in enumerate(self.best_configs, 1):
            config['rank'] = i
        
        return self.best_configs
    
    def print_results(self, top_n=10, metric='total_pnl'):
        """Print best configurations"""
        best = self.get_best_configs(top_n, metric)
        
        if not best:
            logger.warning("No valid configurations found")
            return
        
        print("\n" + "="*160)
        print(f"TOP {top_n} BEST CONFIGURATIONS FOR {self.symbol}")
        print(f"Sorted by: {metric.upper()}")
        print("="*160)
        
        for result in best:
            print(f"\n🏆 RANK #{result['rank']}")
            print("-" * 160)
            print(f"PARAMETERS:")
            print(f"  EMA: {result['ema_fast']}/{result['ema_slow']} | "
                  f"RSI: {result['rsi_period']} | "
                  f"ATR: {result['atr_period']} | "
                  f"TP: {result['take_profit_pips']}pips | "
                  f"SL: {result['stop_loss_pips']}pips")
            print(f"\nPERFORMANCE:")
            print(f"  Total Trades: {result['total_trades']:3d} | Wins: {result['wins']:3d} | Losses: {result['losses']:3d}")
            print(f"  Win Rate: {result['win_rate']:6.1f}% | Profit Factor: {result['profit_factor']:5.2f}")
            print(f"  Total P&L: ${result['total_pnl']:8.2f} | Avg Trade: ${result['avg_trade']:6.2f}")
            print(f"  Best Trade: ${result['best_trade']:8.2f} | Worst Trade: ${result['worst_trade']:8.2f}")
            print(f"  Max Drawdown: {result['max_drawdown']:6.2f}% | Sharpe Ratio: {result['sharpe_ratio']:6.3f}")
            print(f"  Avg Duration: {result['avg_duration']:6.0f} min | Recovery Factor: {result['recovery_factor']:6.2f}")
        
        print("\n" + "="*160)
    
    def export_results(self, filename='optimization_results.json'):
        """Export results to JSON"""
        if not self.best_configs:
            self.get_best_configs(10)
        
        export_data = []
        for result in self.best_configs:
            export_data.append({
                'rank': result['rank'],
                'ema_fast': result['ema_fast'],
                'ema_slow': result['ema_slow'],
                'rsi_period': result['rsi_period'],
                'atr_period': result['atr_period'],
                'take_profit_pips': result['take_profit_pips'],
                'stop_loss_pips': result['stop_loss_pips'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'total_pnl': result['total_pnl'],
                'profit_factor': result['profit_factor'],
                'max_drawdown': result['max_drawdown'],
                'sharpe_ratio': result['sharpe_ratio'],
                'recovery_factor': result['recovery_factor']
            })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Results exported to {filename}")


def main():
    # Date range
    end_date = datetime(2026, 1, 19)
    start_date = datetime(2025, 12, 20)
    
    # Initialize optimizer
    optimizer = FastBacktestOptimizer(symbol='XAUUSD', initial_balance=500)
    
    # Run optimization
    logger.info("="*80)
    logger.info("STARTING XAUUSD PARAMETER OPTIMIZATION")
    logger.info("="*80)
    
    results = optimizer.optimize(start_date, end_date, verbose=True)
    logger.info(f"Total valid configurations: {len(results)}")
    
    # Print top 10 by P&L
    print("\n\n")
    optimizer.print_results(top_n=10, metric='total_pnl')
    
    # Print top 10 by Win Rate
    print("\n\n")
    optimizer.print_results(top_n=10, metric='win_rate')
    
    # Print top 10 by Sharpe Ratio
    print("\n\n")
    optimizer.print_results(top_n=10, metric='sharpe_ratio')
    
    # Export results
    optimizer.export_results('optimization_results.json')
    
    logger.info("="*80)
    logger.info("OPTIMIZATION COMPLETE!")
    logger.info("="*80)


if __name__ == '__main__':
    main()
