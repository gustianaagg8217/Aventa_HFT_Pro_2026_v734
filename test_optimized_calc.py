"""
Test Optimized Calculation Methods
"""

import numpy as np
import pandas as pd
import time

print("=" * 60)
print("TESTING OPTIMIZED CALCULATION METHODS")
print("=" * 60)

data_size = 1000
data = np.random.random(data_size)

# === METHOD 1: Pandas EWM (Current - SLOW) ===
print("\n1. PANDAS EWM (Current Method)")
print("-" * 60)

start = time.perf_counter()
df = pd.DataFrame({'close': data})
ema_pandas = df['close'].ewm(span=20).mean()
time_pandas = (time.perf_counter() - start) * 1000

print("Time: {:.3f}ms".format(time_pandas))

# === METHOD 2: NumPy EMA (Optimized) ===
print("\n2.NUMPY EMA (Optimized)")
print("-" * 60)

def ema_numpy(data, period):
    """Fast EMA using NumPy"""
    alpha = 2 / (period + 1)
    ema = np.zeros_like(data)
    ema[0] = data[0]
    
    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
    
    return ema

start = time.perf_counter()
ema_np = ema_numpy(data, 20)
time_numpy = (time.perf_counter() - start) * 1000

print("Time: {:.3f}ms".format(time_numpy))
print("Speedup: {:.1f}x faster".format(time_pandas / time_numpy))

# === METHOD 3: Numba JIT EMA (Ultra-Fast) ===
print("\n3.NUMBA JIT EMA (Ultra-Fast)")
print("-" * 60)

try:
    from numba import jit
    
    @jit(nopython=True)
    def ema_numba(data, period):
        """Ultra-fast EMA using Numba JIT compilation"""
        alpha = 2.0 / (period + 1.0)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1.0 - alpha) * ema[i-1]
        
        return ema
    
    # Warmup (first call compiles)
    _ = ema_numba(data, 20)
    
    # Actual timing
    start = time.perf_counter()
    ema_numba_result = ema_numba(data, 20)
    time_numba = (time.perf_counter() - start) * 1000
    
    print("Time: {:.3f}ms".format(time_numba))
    print("Speedup:  {:.1f}x faster than Pandas".format(time_pandas / time_numba))
    print("Speedup: {:.1f}x faster than NumPy".format(time_numpy / time_numba))
    
except ImportError: 
    print("Numba not installed.Install with: pip install numba")

# === SUMMARY ===
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

print("Pandas EWM:   {:.3f}ms (baseline)".format(time_pandas))
print("NumPy EMA:   {:.3f}ms ({:.1f}x faster)".format(time_numpy, time_pandas / time_numpy))

if 'time_numba' in locals():
    print("Numba JIT:    {:.3f}ms ({:.1f}x faster)".format(time_numba, time_pandas / time_numba))
    
    if time_numba < 1.0:
        print("\n[GREEN] RECOMMENDATION: Use Numba JIT for HFT!")
    elif time_numpy < 10.0:
        print("\n[YELLOW] RECOMMENDATION:  Use NumPy EMA for better performance")
else:
    if time_numpy < 10.0:
        print("\n[YELLOW] RECOMMENDATION: Use NumPy EMA")

print("=" * 60)