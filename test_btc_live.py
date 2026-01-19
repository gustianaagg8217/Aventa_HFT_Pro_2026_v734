"""
Live Test - XAUUSD Weekend Trading
Monitor performance in real market conditions
"""

import sys
sys.path.append('.')

from aventa_hft_core import UltraLowLatencyEngine
from risk_manager import RiskManager
import time
import json
from datetime import datetime

print("=" * 60)
print("BTCUSD LIVE MONITORING TEST (WEEKEND)")
print("=" * 60)
print()

# Load config
with open('config_BTCUSD_CONSERVATIVE.json', 'r') as f:
    config = json.load(f)

print(f"Symbol: {config['symbol']}")
print(f"Volume: {config['default_volume']}")
print(f"Max Spread: {config['max_spread']}")
print(f"TP Target: ${config['tp_dollar_amount']}")
print()

# Create components
risk_manager = RiskManager(config)
engine = UltraLowLatencyEngine(config['symbol'], config, risk_manager)

# Initialize
print("Initializing engine...")
if not engine.initialize():
    print("✗ Failed to initialize")
    sys.exit(1)

print("✓ Engine initialized")
print()

# Start engine (monitoring only - no trading)
print("=" * 60)
print("LIVE MONITORING MODE (NO TRADING)")
print("Press Ctrl+C to stop")
print("=" * 60)
print()

try:
    # Monitor for 60 seconds
    start_time = time.time()
    tick_count = 0
    signal_count = 0
    
    while time.time() - start_time < 60:
        # Get tick
        tick = engine.get_tick_ultra_fast()
        
        if tick:
            tick_count += 1
            engine.tick_buffer.append(tick)
            
            # Analyze every 10 ticks
            if tick_count % 10 == 0:
                microstructure = engine.analyze_microstructure()
                
                if microstructure:
                    # Generate signal (but don't execute)
                    signal = engine.generate_signal(microstructure)
                    
                    if signal:
                        signal_count += 1
                        print(f"\n🎯 SIGNAL #{signal_count}:")
                        print(f"  Type: {signal.signal_type}")
                        print(f"  Strength: {signal.strength:.2f}")
                        print(f"  Price: {signal.price:.2f}")
                        print(f"  SL: {signal.stop_loss:.2f}")
                        print(f"  TP: {signal.take_profit:.2f}")
                        print(f"  Reason: {signal.reason}")
                
                # Display stats
                if tick_count % 50 == 0:
                    elapsed = time.time() - start_time
                    ticks_per_sec = tick_count / elapsed
                    
                    print(f"\n📊 Stats after {elapsed:.1f}s:")
                    print(f"  Ticks:  {tick_count} ({ticks_per_sec:.1f}/sec)")
                    print(f"  Signals: {signal_count}")
                    print(f"  Spread: {tick.spread:.2f}")
                    print(f"  Price: {tick.mid_price:.2f}")
        
        time.sleep(0.01)  # 10ms delay
    
    # Final report
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    elapsed = time.time() - start_time
    print(f"\nDuration: {elapsed:.1f} seconds")
    print(f"Ticks processed: {tick_count}")
    print(f"Signals generated:  {signal_count}")
    print(f"Ticks per second: {tick_count/elapsed:.1f}")
    
    if signal_count > 0:
        print(f"Signals per minute: {signal_count / (elapsed/60):.1f}")
        print("\n✅ System generating signals - READY FOR TRADING!")
    else:
        print("\n⚠️ No signals generated - Market may be quiet or settings too strict")

except KeyboardInterrupt:
    print("\n\n⚠️ Test interrupted by user")

finally:
    engine.stop()
    print("\n✓ Engine stopped")

print()