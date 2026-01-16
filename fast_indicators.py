"""
Fast Indicators - Numba-optimized technical indicators for HFT
Ultra-low latency calculations using JIT compilation
"""

import numpy as np
from numba import jit

@jit(nopython=True)
def ema_fast(data, period):
    """
    Ultra-fast EMA calculation using Numba JIT
    
    Args:
        data:  numpy array of prices
        period: EMA period
        
    Returns: 
        numpy array of EMA values
    """
    alpha = 2.0 / (period + 1.0)
    ema = np.zeros_like(data)
    ema[0] = data[0]
    
    for i in range(1, len(data)):
        ema[i] = alpha * data[i] + (1.0 - alpha) * ema[i-1]
    
    return ema


@jit(nopython=True)
def rsi_fast(data, period=14):
    """
    Ultra-fast RSI calculation using Numba JIT
    
    Args:
        data: numpy array of prices
        period: RSI period (default 14)
        
    Returns:
        numpy array of RSI values
    """
    n = len(data)
    rsi = np.zeros(n)
    
    # Calculate price changes
    deltas = np.zeros(n)
    for i in range(1, n):
        deltas[i] = data[i] - data[i-1]
    
    # Separate gains and losses
    gains = np.zeros(n)
    losses = np.zeros(n)
    
    for i in range(n):
        if deltas[i] > 0:
            gains[i] = deltas[i]
        else: 
            losses[i] = -deltas[i]
    
    # Calculate average gain/loss
    avg_gain = 0.0
    avg_loss = 0.0
    
    # Initial average
    for i in range(1, period + 1):
        avg_gain += gains[i]
        avg_loss += losses[i]
    
    avg_gain /= period
    avg_loss /= period
    
    # Calculate RSI
    for i in range(period, n):
        if avg_loss == 0:
            rsi[i] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100.0 - (100.0 / (1.0 + rs))
        
        # Update averages (smoothed)
        avg_gain = ((avg_gain * (period - 1)) + gains[i]) / period
        avg_loss = ((avg_loss * (period - 1)) + losses[i]) / period
    
    return rsi


@jit(nopython=True)
def atr_fast(high, low, close, period=14):
    """
    Ultra-fast ATR calculation using Numba JIT
    
    Args: 
        high: numpy array of high prices
        low:  numpy array of low prices
        close: numpy array of close prices
        period: ATR period (default 14)
        
    Returns:
        numpy array of ATR values
    """
    n = len(close)
    tr = np.zeros(n)
    atr = np.zeros(n)
    
    # Calculate True Range
    for i in range(1, n):
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i-1])
        lc = abs(low[i] - close[i-1])
        tr[i] = max(hl, max(hc, lc))
    
    # First ATR is simple average
    atr[period] = np.mean(tr[1:period+1])
    
    # Subsequent ATR values (smoothed)
    for i in range(period + 1, n):
        atr[i] = ((atr[i-1] * (period - 1)) + tr[i]) / period
    
    return atr


@jit(nopython=True)
def momentum_fast(data, period=10):
    """
    Ultra-fast Momentum calculation using Numba JIT
    
    Args: 
        data: numpy array of prices
        period: momentum period
        
    Returns:
        numpy array of momentum values
    """
    n = len(data)
    momentum = np.zeros(n)
    
    for i in range(period, n):
        momentum[i] = data[i] - data[i - period]
    
    return momentum


@jit(nopython=True)
def bollinger_bands_fast(data, period=20, num_std=2.0):
    """
    Ultra-fast Bollinger Bands calculation using Numba JIT
    
    Args:
        data:  numpy array of prices
        period:  MA period
        num_std: number of standard deviations
        
    Returns:
        tuple of (middle_band, upper_band, lower_band)
    """
    n = len(data)
    middle = np.zeros(n)
    upper = np.zeros(n)
    lower = np.zeros(n)
    
    for i in range(period - 1, n):
        # Calculate SMA
        sum_val = 0.0
        for j in range(i - period + 1, i + 1):
            sum_val += data[j]
        middle[i] = sum_val / period
        
        # Calculate standard deviation
        sum_sq = 0.0
        for j in range(i - period + 1, i + 1):
            diff = data[j] - middle[i]
            sum_sq += diff * diff
        std = np.sqrt(sum_sq / period)
        
        # Calculate bands
        upper[i] = middle[i] + (num_std * std)
        lower[i] = middle[i] - (num_std * std)
    
    return middle, upper, lower


# === PERFORMANCE TEST ===
if __name__ == "__main__": 
    import time
    
    print("=" * 60)
    print("FAST INDICATORS - PERFORMANCE TEST")
    print("=" * 60)
    
    # Generate test data
    data_size = 10000
    data = np.random.random(data_size) * 100
    high = data * 1.01
    low = data * 0.99
    close = data
    
    # Warmup (compile functions)
    print("\nWarming up JIT compiler...")
    _ = ema_fast(data[: 100], 20)
    _ = rsi_fast(data[:100], 14)
    _ = atr_fast(high[: 100], low[:100], close[: 100], 14)
    _ = momentum_fast(data[:100], 10)
    _ = bollinger_bands_fast(data[:100], 20, 2.0)
    print("✓ JIT compilation complete")
    
    print("\n" + "=" * 60)
    print("PERFORMANCE RESULTS (10,000 bars)")
    print("=" * 60)
    
    # Test EMA
    start = time.perf_counter()
    ema = ema_fast(data, 20)
    ema_time = (time.perf_counter() - start) * 1000
    print(f"EMA (20):        {ema_time:.4f}ms")
    
    # Test RSI
    start = time.perf_counter()
    rsi = rsi_fast(data, 14)
    rsi_time = (time.perf_counter() - start) * 1000
    print(f"RSI (14):        {rsi_time:.4f}ms")
    
    # Test ATR
    start = time.perf_counter()
    atr = atr_fast(high, low, close, 14)
    atr_time = (time.perf_counter() - start) * 1000
    print(f"ATR (14):        {atr_time:.4f}ms")
    
    # Test Momentum
    start = time.perf_counter()
    mom = momentum_fast(data, 10)
    mom_time = (time.perf_counter() - start) * 1000
    print(f"Momentum (10):   {mom_time:.4f}ms")
    
    # Test Bollinger Bands
    start = time.perf_counter()
    bb_middle, bb_upper, bb_lower = bollinger_bands_fast(data, 20, 2.0)
    bb_time = (time.perf_counter() - start) * 1000
    print(f"Bollinger (20):  {bb_time:.4f}ms")
    
    # Total time
    total_time = ema_time + rsi_time + atr_time + mom_time + bb_time
    print(f"\nTotal Time:      {total_time:.4f}ms")
    
    # Performance rating
    print("\n" + "=" * 60)
    if total_time < 1.0:
        print("[GREEN] PERFORMANCE:  EXCELLENT - HFT READY!")
    elif total_time < 10.0:
        print("[YELLOW] PERFORMANCE:  GOOD - Suitable for scalping")
    else:
        print("[RED] PERFORMANCE:  NEEDS OPTIMIZATION")
    
    print("=" * 60)