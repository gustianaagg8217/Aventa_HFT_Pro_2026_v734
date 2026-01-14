"""
Performance Baseline Test
Measure system capability before live trading
"""

import psutil
import time
import MetaTrader5 as mt5
from datetime import datetime
import numpy as np

print("=" * 60)
print("AVENTA HFT PRO 2026 - PERFORMANCE BASELINE TEST")
print("=" * 60)
print()

# === SYSTEM RESOURCES TEST ===
print("SYSTEM RESOURCES CHECK")
print("-" * 60)

cpu_percent = psutil.cpu_percent(interval=1)
ram = psutil.virtual_memory()
disk = psutil.disk_usage('/')

print("CPU Usage:  {:.1f}% (Idle)".format(cpu_percent))
print("RAM Available: {:.1f} GB / {:.1f} GB".format(ram.available / (1024**3), ram.total / (1024**3)))
print("Disk Free: {:.0f} GB / {:.0f} GB".format(disk.free / (1024**3), disk.total / (1024**3)))

# Warnings
if cpu_percent > 50:
    print("WARNING: High CPU usage detected - close background apps")
if ram.percent > 80:
    print("WARNING:  High RAM usage - close unnecessary programs")
if disk.percent > 90:
    print("WARNING: Low disk space - free up space")

print()

# === MT5 CONNECTION TEST ===
print("MT5 CONNECTION TEST")
print("-" * 60)

# Test MT5 initialization
start_time = time.perf_counter()
mt5_path = "C:\\Program Files\\XM Global MT5\\terminal64.exe"

if mt5.initialize(mt5_path):
    init_time = (time.perf_counter() - start_time) * 1000
    print("MT5 Connected: {:.2f}ms".format(init_time))
    
    # Get account info
    account = mt5.account_info()
    if account:
        print("Account: {}".format(account.login))
        print("Balance:  ${:.2f}".format(account.balance))
        print("Server: {}".format(account.server))
    
    # Test symbol info retrieval speed
    symbols = ['GOLD.ls', 'EURUSD', 'XAUUSD', 'BTCUSD.futu']
    print()
    print("SYMBOL ACCESS SPEED TEST")
    print("-" * 60)
    
    for symbol in symbols: 
        start = time.perf_counter()
        info = mt5.symbol_info(symbol)
        elapsed = (time.perf_counter() - start) * 1000
        
        if info:
            print("{: <15s}: {:.3f}ms - Spread: {} points".format(symbol, elapsed, info.spread))
        else:
            print("{:<15s}:  Not available".format(symbol))
    
    # Test tick retrieval speed
    print()
    print("TICK RETRIEVAL SPEED TEST (100 iterations)")
    print("-" * 60)
    
    test_symbol = 'GOLD.ls'
    tick_times = []
    
    for i in range(100):
        start = time.perf_counter()
        tick = mt5.symbol_info_tick(test_symbol)
        elapsed = (time.perf_counter() - start) * 1000000  # microseconds
        if tick:
            tick_times.append(elapsed)
    
    if tick_times: 
        avg_latency = np.mean(tick_times)
        print("Average: {:.1f} us".format(avg_latency))
        print("Min: {:.1f} us".format(np.min(tick_times)))
        print("Max:  {:.1f} us".format(np.max(tick_times)))
        print("Std Dev: {:.1f} us".format(np.std(tick_times)))
        
        # Performance rating
        if avg_latency < 100:
            rating = "EXCELLENT"
            emoji = "[GREEN]"
        elif avg_latency < 500:
            rating = "GOOD"
            emoji = "[YELLOW]"
        elif avg_latency < 1000:
            rating = "ACCEPTABLE"
            emoji = "[ORANGE]"
        else: 
            rating = "POOR - Consider upgrading connection"
            emoji = "[RED]"
        
        print("\n{} Performance Rating: {}".format(emoji, rating))
    
    mt5.shutdown()
else:
    print("MT5 Connection Failed")
    print("  Error: {}".format(mt5.last_error()))
    print("  Path: {}".format(mt5_path))
    avg_latency = 9999  # Set high value for rating

print()

# === CALCULATION SPEED TEST ===
print("CALCULATION SPEED TEST")
print("-" * 60)

# Simulate indicator calculations
data = np.random.random(1000)

# EMA calculation speed
start = time.perf_counter()
import pandas as pd
df = pd.DataFrame({'close': data})
ema = df['close'].ewm(span=20).mean()
ema_time = (time.perf_counter() - start) * 1000

print("EMA (1000 bars): {:.3f}ms".format(ema_time))

# RSI calculation speed
start = time.perf_counter()
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))
rsi_time = (time.perf_counter() - start) * 1000

print("RSI (1000 bars): {:.3f}ms".format(rsi_time))

# ATR calculation speed
start = time.perf_counter()
df['high'] = data * 1.001
df['low'] = data * 0.999
high_low = df['high'] - df['low']
atr = high_low.rolling(14).mean()
atr_time = (time.perf_counter() - start) * 1000

print("ATR (1000 bars): {:.3f}ms".format(atr_time))

total_calc_time = ema_time + rsi_time + atr_time
print("\nTotal Indicator Time: {:.3f}ms".format(total_calc_time))

if total_calc_time < 10:
    print("[GREEN] Calculation Speed: EXCELLENT (suitable for HFT)")
elif total_calc_time < 50:
    print("[YELLOW] Calculation Speed: GOOD (suitable for scalping)")
else:
    print("[RED] Calculation Speed:  SLOW (optimize or upgrade CPU)")

print()

# === MEMORY EFFICIENCY TEST ===
print("MEMORY EFFICIENCY TEST")
print("-" * 60)

import sys

# Test buffer memory usage
buffer_sizes = [1000, 5000, 10000, 50000]

for size in buffer_sizes:
    test_buffer = [{'timestamp': i, 'price': 100.0, 'volume': 1000} for i in range(size)]
    memory_mb = sys.getsizeof(test_buffer) / (1024 * 1024)
    print("Buffer size {: 6d}: {:.2f} MB".format(size, memory_mb))

print()

# === FINAL RECOMMENDATIONS ===
print("=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)

recommendations = []

if cpu_percent > 50:
    recommendations.append("- Close background applications to reduce CPU load")

if ram.percent > 80:
    recommendations.append("- Consider upgrading RAM for better performance")

if avg_latency > 500:
    recommendations.append("- Check network connection quality")
    recommendations.append("- Consider using VPS closer to broker server")

if total_calc_time > 20:
    recommendations.append("- Reduce indicator calculation frequency")
    recommendations.append("- Use simpler indicators for HFT")

if not recommendations:
    print("System is OPTIMAL for HFT trading!")
else:
    for rec in recommendations:
        print(rec)

print()
print("=" * 60)
print("BASELINE TEST COMPLETED")
print("=" * 60)