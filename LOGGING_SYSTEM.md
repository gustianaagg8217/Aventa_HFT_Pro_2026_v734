# 📝 Logging System Documentation

## Overview

Semua error, warning, dan informasi dari aplikasi akan ditampilkan di tab **Logs**, sehingga Anda tidak perlu membuka console lagi.

---

## ✨ Fitur Logging

### 1. **Console Output Redirection**
- Semua `print()` statements otomatis tampil di GUI Logs tab
- stdout dan stderr di-redirect ke text widget

### 2. **Structured Logging**
```
[2026-01-20 14:35:22] [INFO] Starting ML Model Training...
[2026-01-20 14:35:23] [SUCCESS] ✓ MT5 initialized
[2026-01-20 14:35:25] [WARNING] ⚠️ Low balance detected
[2026-01-20 14:35:27] [ERROR] ❌ Failed to collect historical data
```

### 3. **Color-Coded Levels**
- 🟢 **INFO**: Normal information (green: `#00e676`)
- 🔵 **SUCCESS**: Operation succeeded (blue: `#00b0ff`)
- 🟡 **WARNING**: Caution messages (yellow: `#ffd600`)
- 🔴 **ERROR**: Error messages (red: `#ff1744`)

### 4. **Global Exception Handler**
- Uncaught exceptions automatic logged to Logs tab
- Stack traces displayed untuk debugging
- Application tidak crash tanpa info

---

## 📋 Log Locations

### Tab Locations
1. **Logs Tab** - Main application logs
   - Semua system messages
   - Configuration changes
   - Bot start/stop events
   - Error messages

2. **Backtest Logs** (Strategy Tester Tab)
   - Backtest progress
   - Trade entries/exits
   - Performance metrics
   - ML training status

3. **Risk Events** (Risk Management Tab)
   - Circuit breaker triggers
   - Risk limit breaches
   - Position management events

4. **Training Logs** (ML Models Tab)
   - ML model training progress
   - Feature engineering steps
   - Model accuracy metrics

---

## 🎯 Example Log Output

### ML Model Training
```
[2026-01-20 14:35:22] [INFO] 🧠 Starting ML Model Training...
[2026-01-20 14:35:22] [INFO] 📊 Symbol: GOLD
[2026-01-20 14:35:23] [INFO] ⏳ Collecting historical data (30 days)...
[2026-01-20 14:35:23] [SUCCESS] ✓ MT5 initialized
[2026-01-20 14:35:25] [INFO] 📚 Initializing ML predictor for GOLD...
[2026-01-20 14:35:25] [INFO] 📚 Training models (RandomForest + GradientBoosting)...
[2026-01-20 14:35:45] [SUCCESS] ✅ ML Model Training Completed!
[2026-01-20 14:35:45] [INFO]   📈 Training Accuracy: 52.34%
[2026-01-20 14:35:45] [INFO]   🎯 Test Accuracy: 51.89%
```

### Bot Start/Stop
```
[2026-01-20 14:40:10] [INFO] ✓ Starting TAGJA XM GOLD (Magic: 2026001)...
[2026-01-20 14:40:11] [SUCCESS] ✅ Bot started - Trading GOLD with Symbol
[2026-01-20 14:40:12] [INFO] 📊 Initial Balance: $1000.00
[2026-01-20 14:40:13] [INFO] 🟢 TAGJA XM GOLD: TRADING ACTIVE
[2026-01-20 14:41:55] [WARNING] ⚠️ Daily loss limit reached: $-50.00
[2026-01-20 14:42:00] [INFO] 🔵 TAGJA XM GOLD: Stopped
```

### Error Handling
```
[2026-01-20 15:10:30] [ERROR] ❌ Failed to initialize MT5
[2026-01-20 15:10:30] [ERROR]    Make sure MT5 is running
[2026-01-20 15:10:35] [ERROR] ❌ Connection Error
[2026-01-20 15:10:35] [ERROR]    Traceback (most recent call last):
[2026-01-20 15:10:35] [ERROR]      File "aventa_hft_core.py", line 145, in initialize
[2026-01-20 15:10:35] [ERROR]        mt5.initialize()
[2026-01-20 15:10:35] [ERROR]    RuntimeError: MT5 not available
```

---

## 🔍 How to Debug

### 1. **Check Logs Tab First**
- Open **📝 Logs** tab
- All errors visible immediately
- No need to check console

### 2. **Multi-Tab Monitoring**
- **Logs Tab**: System-wide messages
- **Backtest Logs**: Strategy results
- **Risk Events**: Risk management events
- **Training Logs**: ML training progress

### 3. **Filter by Level**
Look for:
- 🔴 [ERROR] - Critical issues
- 🟡 [WARNING] - Potential problems
- 🔵 [SUCCESS] - Successful operations
- 🟢 [INFO] - Informational messages

---

## 📝 Log Features

### Timestamps
```
[YYYY-MM-DD HH:MM:SS] [LEVEL] Message
```
- Precise time of every event
- Useful for correlation analysis

### Message Levels
```python
# Auto-detection based on keyword
if "error" in message.lower():
    level = "ERROR"
elif "failed" in message.lower():
    level = "ERROR"
elif "warning" in message.lower():
    level = "WARNING"
elif "success" in message.lower() or "✓" in message:
    level = "SUCCESS"
else:
    level = "INFO"
```

### Auto-Scrolling
- New messages automatically visible at bottom
- No need to manual scroll

---

## 🛠️ Developer Usage

### Log from Your Code
```python
# In any method:
self.log_message("Your message here", "INFO")
self.log_message("Operation successful!", "SUCCESS")
self.log_message("Something went wrong", "ERROR")
self.log_message("Be careful!", "WARNING")
```

### Print Still Works
```python
# This also appears in Logs tab:
print("This will appear in Logs!")
print("Error occurred: Failed to connect")
```

### Exception Logging
```python
try:
    do_something()
except Exception as e:
    self.log_message(f"Error: {e}", "ERROR")
    # Also logged by global handler
```

---

## 📊 Log Retention

- **In Memory**: All current session logs
- **Max Buffer**: ~1000 lines per tab
- **Clearing**: Manual clear button available
- **Export**: Can copy/save logs manually

### Clear Logs
1. Open **📝 Logs** tab
2. Press `[🗑️ Clear]` button
3. Logs cleared, fresh start

---

## 🎯 Common Log Patterns

### Normal Startup
```
[INFO] ✓ Logging system initialized
[INFO] Loading configuration...
[SUCCESS] ✓ Configuration loaded
[INFO] Initializing database...
[SUCCESS] ✓ Database connected
[INFO] Starting Telegram listener...
[SUCCESS] ✓ System ready
```

### Trading Session
```
[INFO] 🟢 Bot: TRADING ACTIVE
[INFO] 🔄 Signal detected: BUY
[INFO] 📈 Entry price: $2050.25
[INFO] ✓ Position opened: 0.1 lot
[INFO] 📊 P&L: +$10.50
[INFO] 🔄 Signal detected: SELL
[INFO] ✓ Position closed
```

### Error Scenario
```
[WARNING] ⚠️ Spread too wide: 0.45
[ERROR] ❌ Entry rejected
[WARNING] Retrying connection...
[SUCCESS] ✓ Connection restored
[INFO] Resuming trading...
```

---

## ✅ Advantages

| Before | After |
|--------|-------|
| ❌ Need to open console | ✅ Everything in GUI |
| ❌ Console window separate | ✅ Integrated logging |
| ❌ Errors might be missed | ✅ Color-coded visible |
| ❌ Hard to follow flow | ✅ Timestamp + levels |
| ❌ Manual screenshot/copy | ✅ All in one place |

---

## 🔧 Technical Details

### Logging Architecture
```
Application Code
    ↓
sys.stdout/stderr
    ↓
TextWidgetLogger (Custom Stream)
    ↓
log_message() method
    ↓
GUI Text Widget (Color-coded)
```

### Thread Safety
- Logging thread-safe
- GUI updates via `root.after()`
- No race conditions

### Performance
- Minimal overhead
- Non-blocking logging
- Efficient buffering

---

## 💡 Tips

1. **Monitor While Trading**
   - Keep Logs tab visible
   - Watch for warnings in real-time

2. **Debugging Issues**
   - Check Logs tab first
   - Look for red [ERROR] messages
   - Check timestamps for correlation

3. **Performance**
   - Use "Clear" periodically
   - Prevents memory bloat
   - Keeps UI responsive

4. **Multitab Monitoring**
   - Keep multiple tabs open
   - Watch different log sources
   - Better real-time insight

---

## 🚀 Result

**No more console window hunting!**
- ✅ All logs in GUI
- ✅ Color-coded for quick scanning
- ✅ Timestamps for debugging
- ✅ Multiple log sources integrated
- ✅ Professional look & feel

