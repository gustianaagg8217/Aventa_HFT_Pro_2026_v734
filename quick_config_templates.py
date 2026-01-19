"""
QUICK BACKTEST PARAMETER TEMPLATES FOR XAUUSD
Copy and paste these configurations into the GUI
"""

CONFIGURATIONS = {
    "1_MAXIMUM_PROFIT": {
        "name": "MAXIMUM PROFIT",
        "ema_fast_period": 7,
        "ema_slow_period": 21,
        "rsi_period": 7,
        "atr_period": 14,
        "take_profit_pips": 3.5,
        "stop_loss_pips": 10.0,
        "max_floating_loss_pips": 15.0,
        "max_duration_minutes": 1440,
    },
    "2_CONSERVATIVE": {
        "name": "CONSERVATIVE",
        "ema_fast_period": 9,
        "ema_slow_period": 28,
        "rsi_period": 14,
        "atr_period": 14,
        "take_profit_pips": 5.0,
        "stop_loss_pips": 7.0,
        "max_floating_loss_pips": 10.0,
        "max_duration_minutes": 720,
    },
    "3_AGGRESSIVE": {
        "name": "AGGRESSIVE",
        "ema_fast_period": 5,
        "ema_slow_period": 15,
        "rsi_period": 5,
        "atr_period": 10,
        "take_profit_pips": 2.5,
        "stop_loss_pips": 5.0,
        "max_floating_loss_pips": 8.0,
        "max_duration_minutes": 480,
    },
    "4_BALANCED": {
        "name": "BALANCED RISK-REWARD",
        "ema_fast_period": 7,
        "ema_slow_period": 21,
        "rsi_period": 9,
        "atr_period": 14,
        "take_profit_pips": 8.0,
        "stop_loss_pips": 8.0,
        "max_floating_loss_pips": 12.0,
        "max_duration_minutes": 960,
    },
    "5_PROFIT_FACTOR": {
        "name": "PROFIT FACTOR OPTIMIZED",
        "ema_fast_period": 9,
        "ema_slow_period": 25,
        "rsi_period": 12,
        "atr_period": 16,
        "take_profit_pips": 6.0,
        "stop_loss_pips": 4.0,
        "max_floating_loss_pips": 12.0,
        "max_duration_minutes": 1200,
    },
}

if __name__ == '__main__':
    print("="*100)
    print("XAUUSD CONFIGURATION TEMPLATES - COPY PASTE INTO CONFIG MANAGER")
    print("="*100)
    
    for key, config in CONFIGURATIONS.items():
        print(f"\n{key}")
        print("-" * 100)
        print(f"Configuration Name: {config['name']}")
        print(f"copy_config = {{")
        for k, v in config.items():
            if k != 'name':
                print(f"    '{k}': {v},")
        print(f"}}")
        
        print(f"\nGUI Entry (quick reference):")
        print(f"  EMA: {config['ema_fast_period']}/{config['ema_slow_period']} | " +
              f"RSI: {config['rsi_period']} | ATR: {config['atr_period']} | " +
              f"TP: {config['take_profit_pips']} | SL: {config['stop_loss_pips']}")
