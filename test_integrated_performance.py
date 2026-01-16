"""
Test integrated performance after optimization (WITH WARMUP)
"""

import sys
sys.path.append('.')

from aventa_hft_core import UltraLowLatencyEngine
import time
import numpy as np

print("=" * 60)
print("INTEGRATED PERFORMANCE TEST (WITH WARMUP)")
print("=" * 60)

# Test config
config = {
    'symbol': 'BTCUSD.futu',
    'default_volume': 0.01,
    'magic_number': 2026002,
    'ema_fast_period': 7,
    'ema_slow_period':  21,
    'rsi_period': 7,
    'atr_period': 14,
    'momentum_period':  5,
    'min_signal_strength': 0.6,
    'max_spread':  2.0,  # Increased to allow testing
    'mt5_path':  'C:\\Program Files\\XM Global MT5\\terminal64.exe'
}

# Create engine
engine = UltraLowLatencyEngine(config['symbol'], config, risk_manager=None)

# Initialize
print("\nInitializing engine...")
if engine.initialize():
    print("✓ Engine initialized")
    
    # Simulate tick collection
    print("\nCollecting 100 ticks...")
    for i in range(100):
        tick = engine.get_tick_ultra_fast()
        if tick:
            engine.tick_buffer.append(tick)
        time.sleep(0.001)  # Small delay to get real ticks
    
    print(f"✓ Collected {len(engine.tick_buffer)} ticks")
    
    # === WARMUP PHASE ===
    print("\n🔥 WARMUP PHASE (10 iterations)...")
    for i in range(10):
        _ = engine.analyze_microstructure()
    print("✓ Warmup complete")
    
    # === ACTUAL TEST ===
    print("\nTesting microstructure analysis speed (100 iterations)...")
    
    times = []
    for i in range(100):
        start = time.perf_counter()
        microstructure = engine.analyze_microstructure()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)
    
    # Calculate statistics (excluding outliers)
    times_sorted = sorted(times)
    # Remove top 5% and bottom 5% (outliers)
    trimmed_times = times_sorted[5:95]
    
    avg_time = np.mean(trimmed_times)
    min_time = min(times)
    max_time = max(times)
    median_time = np.median(trimmed_times)
    p95_time = np.percentile(trimmed_times, 95)
    
    print(f"\nResults (100 iterations):")
    print(f"  Average (trimmed): {avg_time:.4f}ms")
    print(f"  Median:             {median_time:.4f}ms")
    print(f"  Min:               {min_time:.4f}ms")
    print(f"  Max:               {max_time:.4f}ms")
    print(f"  95th percentile:   {p95_time:.4f}ms")
    
    # Check fast indicator usage
    if hasattr(engine, '_fast_indicator_count'):
        print(f"\n✓ Fast indicators used: {engine._fast_indicator_count} times")
    
    # Performance rating based on median (more stable metric)
    print("\n" + "=" * 60)
    if median_time < 1.0:
        print("[GREEN] PERFORMANCE:  EXCELLENT - HFT READY!")
        print("  Median latency < 1ms - suitable for high-frequency trading")
    elif median_time < 5.0:
        print("[YELLOW] PERFORMANCE: GOOD - Suitable for scalping")
        print("  Median latency < 5ms - suitable for short-term trading")
    else:
        print("[ORANGE] PERFORMANCE: ACCEPTABLE - Needs optimization")
        print(f"  Median latency {median_time:.2f}ms - consider further optimization")
    print("=" * 60)
    
    engine.stop()
else:
    print("✗ Failed to initialize engine")

print()