#!/usr/bin/env python3
"""
Comprehensive test for Strategy Tester functionality
Tests backtester core functions without GUI dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from strategy_backtester import StrategyBacktester
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

def test_backtester_initialization():
    """Test backtester initialization with valid config"""
    print("\n" + "="*70)
    print("TEST 1: Backtester Initialization")
    print("="*70)
    
    try:
        config = {
            'symbol': 'EURUSD',
            'default_volume': 0.01,
            'magic_number': 2026001,
            'ema_fast_period': 7,
            'ema_slow_period': 21,
            'rsi_period': 14,
            'atr_period': 14,
            'momentum_period': 5,
            'min_signal_strength': 0.45,
            'max_volatility': 0.005,
            'tp_mode': 'FixedDollar',
            'tp_dollar_amount': 0.8,
            'sl_multiplier': 50.0,
            'risk_reward_ratio': 2.0,
            'rsi_overbought': 68,
            'rsi_oversold': 32,
            'max_floating_loss': 5.0,
            'max_floating_profit': 0.5
        }
        
        backtester = StrategyBacktester(config, initial_balance=10000)
        
        assert backtester.initial_balance == 10000, "Initial balance mismatch"
        assert backtester.balance == 10000, "Current balance mismatch"
        assert backtester.config['symbol'] == 'EURUSD', "Symbol mismatch"
        assert backtester.pip_size == 0.00001, "Pip size should default to 0.00001"
        
        print("✅ Backtester initialized successfully")
        print(f"   • Initial Balance: ${backtester.initial_balance:,.2f}")
        print(f"   • Symbol: {backtester.config['symbol']}")
        print(f"   • Pip Size: {backtester.pip_size}")
        return True
        
    except Exception as e:
        print(f"❌ Initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """Test configuration validation"""
    print("\n" + "="*70)
    print("TEST 2: Configuration Validation")
    print("="*70)
    
    try:
        # Test missing symbol
        invalid_config = {
            'default_volume': 0.01,
            'magic_number': 2026001
        }
        
        try:
            backtester = StrategyBacktester(invalid_config, 10000)
            print("❌ Should have raised error for missing symbol")
            return False
        except ValueError as e:
            if "symbol" in str(e).lower():
                print("✅ Correctly detected missing symbol")
            else:
                print(f"❌ Wrong error message: {e}")
                return False
        
        # Test invalid volume
        invalid_config = {
            'symbol': 'EURUSD',
            'default_volume': -0.01,
            'magic_number': 2026001
        }
        
        try:
            backtester = StrategyBacktester(invalid_config, 10000)
            print("❌ Should have raised error for negative volume")
            return False
        except ValueError as e:
            if "volume" in str(e).lower():
                print("✅ Correctly detected invalid volume")
            else:
                print(f"❌ Wrong error message: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Config validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_indicator_calculation():
    """Test technical indicator calculations"""
    print("\n" + "="*70)
    print("TEST 3: Indicator Calculations")
    print("="*70)
    
    try:
        config = {
            'symbol': 'EURUSD',
            'default_volume': 0.01,
            'magic_number': 2026001,
            'ema_fast_period': 7,
            'ema_slow_period': 21,
            'rsi_period': 14,
            'atr_period': 14,
            'momentum_period': 5
        }
        
        backtester = StrategyBacktester(config, 10000)
        
        # Create sample OHLC data
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1H')
        np.random.seed(42)
        close_prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
        
        df = pd.DataFrame({
            'time': dates,
            'open': close_prices - np.random.rand(100) * 0.5,
            'high': close_prices + np.random.rand(100) * 0.5,
            'low': close_prices - np.random.rand(100) * 0.5,
            'close': close_prices,
            'volume': np.random.randint(1000, 10000, 100),
            'spread': np.random.rand(100) * 10
        })
        
        df_with_indicators = backtester.calculate_indicators(df)
        
        # Check all indicators are calculated
        required_indicators = ['ema_fast', 'ema_slow', 'rsi', 'atr', 'momentum', 'volatility']
        for indicator in required_indicators:
            assert indicator in df_with_indicators.columns, f"Missing indicator: {indicator}"
            # Check no NaN in important indicators after warmup
            assert not df_with_indicators[indicator].iloc[50:].isnull().any(), f"NaN values in {indicator}"
        
        print("✅ All indicators calculated successfully")
        print(f"   • EMA (Fast={config['ema_fast_period']}, Slow={config['ema_slow_period']}): ✓")
        print(f"   • RSI ({config['rsi_period']}): ✓")
        print(f"   • ATR ({config['atr_period']}): ✓")
        print(f"   • Momentum ({config['momentum_period']}): ✓")
        print(f"   • Volatility: ✓")
        return True
        
    except Exception as e:
        print(f"❌ Indicator calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_signal_generation():
    """Test signal generation logic"""
    print("\n" + "="*70)
    print("TEST 4: Signal Generation")
    print("="*70)
    
    try:
        config = {
            'symbol': 'EURUSD',
            'default_volume': 0.01,
            'magic_number': 2026001,
            'ema_fast_period': 7,
            'ema_slow_period': 21,
            'rsi_period': 14,
            'atr_period': 14,
            'momentum_period': 5,
            'rsi_overbought': 68,
            'rsi_oversold': 32,
            'min_signal_strength': 0.45
        }
        
        backtester = StrategyBacktester(config, 10000)
        
        # Create test bar with various indicator values
        test_bar = pd.Series({
            'time': datetime.now(),
            'open': 100,
            'high': 101,
            'low': 99,
            'close': 100.5,
            'volume': 5000,
            'spread': 1,
            'ema_fast': 100.8,  # Fast above slow = BUY
            'ema_slow': 100.2,
            'rsi': 25,  # Oversold = BUY
            'atr': 0.5,
            'momentum': 0.3,  # Positive = BUY
            'volatility': 0.003
        })
        
        strength, signal_type = backtester.calculate_signal(test_bar, 50, None)
        
        assert signal_type == 'BUY', f"Expected BUY signal, got {signal_type}"
        assert strength > 0, f"Expected positive strength for BUY, got {strength}"
        
        print("✅ Signal generation working correctly")
        print(f"   • Test Signal: {signal_type} (Strength: {strength:.2f})")
        print(f"   • EMA Cross: ✓ (Fast > Slow)")
        print(f"   • RSI: ✓ (Oversold)")
        print(f"   • Momentum: ✓ (Positive)")
        return True
        
    except Exception as e:
        print(f"❌ Signal generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_profit_calculation():
    """Test profit calculation logic"""
    print("\n" + "="*70)
    print("TEST 5: Profit Calculation")
    print("="*70)
    
    try:
        config = {
            'symbol': 'EURUSD',
            'default_volume': 0.01,
            'magic_number': 2026001,
            'commission_per_trade': 0.0,
            'slippage_pips': 0
        }
        
        backtester = StrategyBacktester(config, 10000)
        
        # Debug: check pip_value
        print(f"   Debug: pip_value = {backtester.pip_value}, pip_size = {backtester.pip_size}")
        
        # Simulate open position
        backtester.open_position = {
            'type': 'BUY',
            'entry_price': 1.1000,
            'volume': 0.01,
            'commission': 0
        }
        
        # For EURUSD: 0.01 lot = $0.1 per pip
        # Price move from 1.1000 to 1.1010 = 10 pips = $1.0
        profit_positive = backtester.calculate_profit(1.1010)
        print(f"   BUY at 1.1000, exit at 1.1010: ${profit_positive:.2f}")
        assert profit_positive > 0, f"Profit should be positive, got {profit_positive}"
        
        # Price move from 1.1000 to 1.0990 = -10 pips = -$1.0
        profit_negative = backtester.calculate_profit(1.0990)
        print(f"   BUY at 1.1000, exit at 1.0990: ${profit_negative:.2f}")
        assert profit_negative < 0, f"Profit should be negative, got {profit_negative}"
        
        print("✅ Profit calculation working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Profit calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_results_calculation():
    """Test results calculation with sample trades"""
    print("\n" + "="*70)
    print("TEST 6: Results Calculation")
    print("="*70)
    
    try:
        config = {
            'symbol': 'EURUSD',
            'default_volume': 0.01,
            'magic_number': 2026001
        }
        
        backtester = StrategyBacktester(config, 10000)
        
        # Add sample trades
        backtester.trades = [
            {
                'entry_time': datetime.now(),
                'exit_time': datetime.now() + timedelta(hours=1),
                'type': 'BUY',
                'entry_price': 1.1000,
                'exit_price': 1.1010,
                'profit': 10.0,
                'duration': '60 min',
                'reason': 'TP',
                'volume': 0.01,
                'commission': 0,
                'symbol': 'EURUSD'
            },
            {
                'entry_time': datetime.now() + timedelta(hours=2),
                'exit_time': datetime.now() + timedelta(hours=3),
                'type': 'SELL',
                'entry_price': 1.1010,
                'exit_price': 1.0990,
                'profit': 20.0,
                'duration': '60 min',
                'reason': 'TP',
                'volume': 0.01,
                'commission': 0,
                'symbol': 'EURUSD'
            },
            {
                'entry_time': datetime.now() + timedelta(hours=4),
                'exit_time': datetime.now() + timedelta(hours=5),
                'type': 'BUY',
                'entry_price': 1.0990,
                'exit_price': 1.0950,
                'profit': -4.0,
                'duration': '60 min',
                'reason': 'SL',
                'volume': 0.01,
                'commission': 0,
                'symbol': 'EURUSD'
            }
        ]
        
        backtester.balance = 10000 + 10.0 + 20.0 - 4.0  # 10026
        backtester.equity_curve = [
            {'time': datetime.now(), 'equity': 10010},
            {'time': datetime.now() + timedelta(hours=1), 'equity': 10030},
            {'time': datetime.now() + timedelta(hours=2), 'equity': 10026}
        ]
        backtester.peak_equity = 10030
        backtester.max_drawdown = 0.04  # ~0.04% drawdown
        
        results = backtester.calculate_results()
        
        assert results['total_trades'] == 3, f"Expected 3 trades, got {results['total_trades']}"
        assert results['wins'] == 2, f"Expected 2 wins, got {results['wins']}"
        assert results['losses'] == 1, f"Expected 1 loss, got {results['losses']}"
        assert results['win_rate'] == 66.66666666666666, f"Win rate incorrect"
        assert results['total_pnl'] == 26.0, f"Expected P&L of 26.0, got {results['total_pnl']}"
        
        print("✅ Results calculation working correctly")
        print(f"   • Total Trades: {results['total_trades']}")
        print(f"   • Wins: {results['wins']}")
        print(f"   • Losses: {results['losses']}")
        print(f"   • Win Rate: {results['win_rate']:.1f}%")
        print(f"   • Total P&L: ${results['total_pnl']:.2f}")
        print(f"   • Profit Factor: {results['profit_factor']:.2f}")
        print(f"   • Max Drawdown: {results['max_drawdown_pct']:.2f}%")
        return True
        
    except Exception as e:
        print(f"❌ Results calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n")
    print("=" * 70)
    print("STRATEGY TESTER COMPREHENSIVE VALIDATION TEST".center(70))
    print("=" * 70)
    
    tests = [
        ("Backtester Initialization", test_backtester_initialization),
        ("Configuration Validation", test_config_validation),
        ("Indicator Calculations", test_indicator_calculation),
        ("Signal Generation", test_signal_generation),
        ("Profit Calculation", test_profit_calculation),
        ("Results Calculation", test_results_calculation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("="*70)
    print(f"Results: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED - Strategy Tester is fully functional!")
        return 0
    else:
        print(f"⚠️  {total_count - passed_count} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
