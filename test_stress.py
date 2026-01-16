"""
Stress Test - Simulate multiple bots running
"""

import threading
import time
import psutil
from datetime import datetime
import MetaTrader5 as mt5

print("🔥 MULTI-BOT STRESS TEST")
print("=" * 60)

# Configuration
NUM_BOTS = 5
TEST_DURATION = 60  # seconds
TICK_INTERVAL = 0.1  # seconds

# Metrics
tick_counts = [0] * NUM_BOTS
errors = [0] * NUM_BOTS
latencies = [[] for _ in range(NUM_BOTS)]

running = True

def bot_simulation(bot_id):
    """Simulate a trading bot"""
    global running
    
    if not mt5.initialize():
        print(f"Bot {bot_id}:  Failed to initialize MT5")
        return
    
    symbol = 'GOLD.ls'
    
    while running:
        try:
            start = time.perf_counter()
            
            # Simulate tick retrieval
            tick = mt5.symbol_info_tick(symbol)
            
            if tick:
                # Simulate calculations
                price = tick.bid
                _ = price * 1.01  # Simple calculation
                
                latency = (time.perf_counter() - start) * 1000  # ms
                latencies[bot_id].append(latency)
                tick_counts[bot_id] += 1
            else:
                errors[bot_id] += 1
            
            time.sleep(TICK_INTERVAL)
            
        except Exception as e:
            errors[bot_id] += 1
    
    mt5.shutdown()

# Start monitoring
print(f"Starting {NUM_BOTS} simulated bots for {TEST_DURATION} seconds...")
print()

# Start bots
threads = []
for i in range(NUM_BOTS):
    t = threading.Thread(target=bot_simulation, args=(i,), daemon=True)
    t.start()
    threads.append(t)
    print(f"✓ Bot {i+1} started")

print()
print("Running stress test...")

# Monitor system resources
start_time = time.time()
cpu_samples = []
ram_samples = []

while time.time() - start_time < TEST_DURATION:
    cpu_samples.append(psutil.cpu_percent(interval=1))
    ram_samples.append(psutil.virtual_memory().percent)
    
    elapsed = int(time.time() - start_time)
    print(f"⏱️  {elapsed}/{TEST_DURATION}s - CPU: {cpu_samples[-1]:.1f}% | RAM: {ram_samples[-1]:.1f}%", end='\r')

# Stop bots
running = False
time.sleep(2)

print("\n")
print("=" * 60)
print("📊 STRESS TEST RESULTS")
print("=" * 60)

# Results per bot
import numpy as np

for i in range(NUM_BOTS):
    print(f"\nBot {i+1}:")
    print(f"  Ticks processed: {tick_counts[i]}")
    print(f"  Errors: {errors[i]}")
    
    if latencies[i]:
        print(f"  Avg latency: {np.mean(latencies[i]):.2f}ms")
        print(f"  Max latency: {np.max(latencies[i]):.2f}ms")

# Overall stats
print(f"\n📈 Overall Statistics:")
print(f"  Total ticks:  {sum(tick_counts)}")
print(f"  Total errors: {sum(errors)}")
print(f"  Avg CPU: {np.mean(cpu_samples):.1f}%")
print(f"  Max CPU: {np.max(cpu_samples):.1f}%")
print(f"  Avg RAM: {np.mean(ram_samples):.1f}%")
print(f"  Max RAM: {np.max(ram_samples):.1f}%")

# Performance rating
total_errors = sum(errors)
avg_cpu = np.mean(cpu_samples)

print(f"\n🎯 Performance Rating:")

if total_errors == 0 and avg_cpu < 50:
    print("  🟢 EXCELLENT - System can handle multiple bots")
elif total_errors < 5 and avg_cpu < 70:
    print("  🟡 GOOD - System adequate for multi-bot trading")
else:
    print("  🔴 POOR - Reduce number of bots or optimize system")

print()
print("=" * 60)