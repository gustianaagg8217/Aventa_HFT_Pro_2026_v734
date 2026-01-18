# Aventa HFT Pro 2026 - Ultra Low Latency Trading System

## 🚀 **Panduan Lengkap Penggunaan Aventa HFT Pro 2026**

*High-Frequency Trading System dengan AI & Telegram Notifications*

---

## 📋 **Daftar Isi**
1. [Persyaratan Sistem](#-persyaratan-sistem)
2. [Instalasi & Setup](#-instalasi--setup)
3. [Konfigurasi Telegram Bot](#-konfigurasi-telegram-bot)
4. [Konfigurasi Trading](#-konfigurasi-trading)
5. [Menjalankan Sistem](#-menjalankan-sistem)
6. [Fitur Trading](#-fitur-trading)
7. [Monitoring & Manajemen](#-monitoring--manajemen)
8. [Troubleshooting](#-troubleshooting)
9. [API Reference](#-api-reference)

---

## 💻 **Persyaratan Sistem**

### **Minimum Requirements:**
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 8GB minimum, 16GB recommended
- **CPU**: Intel i5/AMD Ryzen 5 or better
- **Storage**: 50GB free space
- **Python**: 3.8 - 3.11

### **Software Dependencies:**
- MetaTrader 5 Terminal
- Python 3.8+
- Telegram Bot API access

### **Network Requirements:**
- Stable internet connection (minimum 10 Mbps)
- Low latency connection to broker
- Access to Telegram API

---

## 🔧 **Instalasi & Setup**

### **1. Clone/Download Repository**
```bash
# Extract files ke folder yang diinginkan
# Pastikan path tidak ada spasi
```

### **2. Install Python Dependencies**
```bash
# Install requirements
pip install -r requirements.txt

# Atau untuk performa optimal
pip install -r requirements_optimized.txt
```

### **3. Setup MetaTrader 5**
1. Install MetaTrader 5 Terminal
2. Login ke akun trading Anda
3. Enable AutoTrading
4. Pastikan terminal MT5 running

### **4. Setup Virtual Environment (Opsional)**
```bash
# Buat virtual environment
python -m venv venv

# Aktivasi virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 📱 **Konfigurasi Telegram Bot**

### **1. Buat Telegram Bot**
1. Buka Telegram, cari **@BotFather**
2. Kirim `/newbot`
3. Ikuti instruksi untuk membuat bot
4. Simpan **Bot Token** yang diberikan

### **2. Dapatkan Chat ID**
1. Buka Telegram, cari **@userinfobot**
2. Kirim `/start`
3. Bot akan memberikan Chat ID Anda
4. Simpan Chat ID untuk notifikasi

### **3. Konfigurasi Bot di Sistem**
Edit file `configs/Bot_5_config.json`:
```json
{
    "telegram": {
        "token": "YOUR_BOT_TOKEN_HERE",
        "chat_ids": [
            "YOUR_CHAT_ID_HERE"
        ]
    }
}
```

### **4. Test Telegram Connection**
Jalankan sistem dan klik tombol **"Test Telegram"** di GUI untuk memastikan koneksi berfungsi.

---

## ⚙️ **Konfigurasi Trading**

### **File Konfigurasi Utama**
Edit `configs/Bot_5_config.json` untuk mengatur parameter trading:

```json
{
    "bot_id": "Bot_5",
    "symbol": "BTCUSD.futu",
    "default_volume": 0.01,
    "magic_number": 2026005,
    "risk_per_trade": 1.0,
    "min_signal_strength": 0.01,
    "max_spread": 0.4,
    "max_volatility": 0.005,
    "filling_mode": "FOK",
    "sl_multiplier": 50.0,
    "risk_reward_ratio": 0.5,
    "tp_mode": "FixedDollar",
    "tp_dollar_amount": 0.15,
    "max_floating_loss": 5.0,
    "max_floating_profit": 0.5,
    "max_positions": 5,
    "max_daily_loss": 150.0,
    "max_daily_trades": 1000,
    "max_position_size": 1.0,
    "max_drawdown_pct": 50.0
}
```

### **Parameter Penting:**

| Parameter | Deskripsi | Default |
|-----------|-----------|---------|
| `symbol` | Simbol trading | BTCUSD.futu |
| `default_volume` | Volume per trade | 0.01 |
| `max_positions` | Max posisi terbuka | 5 |
| `max_floating_loss` | Max loss floating | $5.00 |
| `tp_dollar_amount` | Target profit per trade | $0.15 |
| `sl_multiplier` | Stop loss multiplier (ATR) | 50.0x |

---

## ▶️ **Menjalankan Sistem**

### **1. Jalankan dengan Batch File**
```bash
# Klik double-click file
Aventa_HFT_Pro_2026_v7_3_3.bat
```

### **2. Jalankan Manual**
```bash
# Aktivasi virtual environment (jika ada)
venv\Scripts\activate

# Jalankan aplikasi
python Aventa_HFT_Pro_2026_v7_3_3.py
```

### **3. Startup Sequence**
Sistem akan:
1. ✅ Load fast indicators (Numba)
2. ✅ Initialize trade database
3. ✅ Load bot configurations
4. ✅ Connect to MetaTrader 5
5. ✅ Start trading threads
6. ✅ Begin market monitoring

---

## 📊 **Fitur Trading**

### **Core Features:**
- **⚡ Ultra Low Latency**: Sub-millisecond execution
- **🤖 AI/ML Predictions**: XGBoost integration
- **📱 Real-time Telegram**: Instant trade notifications
- **🛡️ Risk Management**: Multi-layer protection
- **📈 Advanced Indicators**: Numba-optimized calculations

### **Trading Signals:**
- **Order Flow Analysis**: Delta-based signals
- **Momentum Detection**: Price velocity analysis
- **Volatility Filtering**: Market condition assessment
- **Strength Scoring**: Signal quality evaluation

### **Risk Management:**
- **Position Limits**: Max 5 positions per bot
- **Daily Loss Limits**: $150 max daily loss
- **Floating Loss Control**: $5 max floating loss
- **Drawdown Protection**: 50% max drawdown
- **Volume Controls**: Position size limits

---

## 📱 **Telegram Notifications**

### **Signal Types:**

#### **🔵 OPEN POSITION SIGNAL**
```
🤖 Bot: Bot_5
📊 Symbol: BTCUSD.futu
📈 Order Type: BUY
📦 Volume: 0.01
💰 Price: $95121.59
🛡️ Stop Loss: $95071.59
🎯 Take Profit: $95136.59
🕐 Timestamp: 2026-01-18 12:32:20

🚀 Position opened successfully!
```

#### **🔴 CLOSE POSITION SIGNAL**
```
🤖 Bot: Bot_5
📊 Symbol: BTCUSD.futu
🎫 Ticket: 12345678
💰 Profit: $0.15
📦 Volume: 0.01
🕐 Timestamp: 2026-01-18 12:32:25

✅ Position closed successfully!
```

### **Close Position Triggers:**
- ✅ **Take Profit Hit**: Automatic close when TP target reached
- ✅ **Stop Loss Hit**: Automatic close when SL triggered  
- ✅ **Manual Close**: GUI button close all positions
- ✅ **Risk Management**: Daily loss limits, floating loss limits
- ✅ **Signal-based Close**: CLOSE signals from trading logic
- ✅ **Emergency Close**: Circuit breaker activations

---

## 📈 **Monitoring & Manajemen**

### **GUI Dashboard:**
- **Real-time P&L**: Live profit monitoring
- **Position Status**: Open positions overview
- **System Health**: CPU, RAM, Disk, Network
- **Trade History**: Recent transactions
- **Risk Metrics**: Drawdown, exposure tracking

### **Log Monitoring:**
```bash
# Check logs in terminal output
# Logs include:
# - Trade executions
# - Signal generation
# - Risk management actions
# - Telegram API calls
# - System performance metrics
```

### **Database Management:**
- **Trade Database**: `trades.db` (SQLite)
- **Performance Tracking**: Win rate, profit factor
- **Historical Analysis**: Backtesting results
- **Risk Analytics**: Drawdown analysis

---

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **1. MetaTrader 5 Connection Failed**
```
ERROR - Failed to get account info from MT5
```
**Solution:**
- Pastikan MT5 terminal running
- Check login credentials
- Verify AutoTrading enabled
- Restart MT5 terminal

#### **2. Telegram Signals Not Working**
```
ERROR - Telegram signal error: no running event loop
```
**Solution:**
- Check bot token validity
- Verify chat ID correct
- Test token with "Test Telegram" button
- Check internet connection

#### **3. Fast Indicators Not Available**
```
WARNING - Fast indicators not available - using slower pandas methods
```
**Solution:**
- Install Numba: `pip install numba`
- Restart application
- Check Python version compatibility

#### **4. Memory Issues**
```
WARNING - High memory usage detected
```
**Solution:**
- Close unnecessary applications
- Increase system RAM
- Reduce position limits
- Enable garbage collection

### **Performance Optimization:**

#### **For Low-End Systems:**
```json
{
    "max_positions": 3,
    "analysis_interval": 0.2,
    "enable_ml": false
}
```

#### **For High-End Systems:**
```json
{
    "max_positions": 10,
    "analysis_interval": 0.05,
    "enable_ml": true
}
```

---

## 📚 **API Reference**

### **Core Classes:**

#### **UltraLowLatencyEngine**
```python
engine = UltraLowLatencyEngine(
    symbol="BTCUSD.futu",
    config=config_dict,
    risk_manager=risk_manager,
    ml_predictor=ml_predictor,
    telegram_callback=callback_function
)
```

#### **RiskManager**
```python
risk_manager = RiskManager(config)
allowed, reason = risk_manager.validate_trade(
    trade_type="BUY",
    volume=0.01,
    current_positions=3
)
```

#### **Telegram Integration**
```python
# Send custom signal
self.send_telegram_signal(
    bot_id="Bot_5",
    signal_type="custom_alert",
    message="Custom notification"
)
```

### **Configuration Parameters:**

| Category | Parameter | Type | Description |
|----------|-----------|------|-------------|
| **Trading** | `symbol` | string | Trading symbol |
| **Risk** | `max_floating_loss` | float | Max loss per trade |
| **Position** | `max_positions` | int | Max open positions |
| **Telegram** | `token` | string | Bot token |
| **ML** | `enable_ml` | bool | Enable AI predictions |

---

## 🎯 **Best Practices**

### **Trading Hours:**
- **Active Hours**: 24/7 for crypto markets
- **Monitor**: High volatility periods
- **Maintenance**: Weekly system restarts

### **Risk Management:**
- **Start Small**: Begin with minimum volume
- **Monitor P&L**: Daily position reviews
- **Emergency Stops**: Use circuit breakers
- **Backup Plans**: Multiple exit strategies

### **System Maintenance:**
- **Daily**: Check system logs
- **Weekly**: Database cleanup
- **Monthly**: Performance analysis
- **Quarterly**: Strategy optimization

---

## 📞 **Support & Contact**

### **Documentation:**
- `Aventa_HFT_Pro_2026_User_Manual_ID-EN.pdf`
- `MANUAL BOOK AVENTA HFT PRO 2026 v7.docx`

### **Community:**
- GitHub Issues for bug reports
- Telegram channel for updates
- Discord server for community support

### **Emergency Contacts:**
- System alerts via Telegram
- Email notifications
- Emergency stop procedures

---

## 🔄 **Update & Upgrade**

### **Version Updates:**
```bash
# Backup configuration
cp configs/ configs_backup/

# Update source code
# Restart application
# Test functionality
```

### **Configuration Migration:**
```bash
# Export current settings
# Update to new version
# Import settings
# Test trading
```

---

## 🔄 **Recent Updates & Fixes**

### **Version 7.3.3 - Telegram Integration**
- ✅ **Fixed Close Position Notifications**: All position closes now send Telegram alerts
- ✅ **Unified Signal Format**: Consistent parameters across all notification types
- ✅ **Manual Close Notifications**: GUI close button now sends Telegram alerts
- ✅ **Async Error Handling**: Improved Telegram API error handling
- ✅ **Thread-safe Operations**: Background thread for Telegram sending

### **Notification Coverage:**
- **OPEN POSITION**: All new trades (BUY/SELL)
- **CLOSE POSITION**: All position closures including:
  - Take Profit hits
  - Stop Loss triggers
  - Manual closes
  - Risk management closes
  - Signal-based closes

---

## ⚠️ **Disclaimer**

**Trading cryptocurrencies and forex involves substantial risk of loss and is not suitable for every investor. Past performance does not guarantee future results.**

**Please:**
- ✅ Test on demo account first
- ✅ Start with small amounts
- ✅ Understand all risks involved
- ✅ Have emergency stop procedures
- ✅ Monitor trading activity regularly

---

## 📈 **Performance Metrics**

### **Expected Performance:**
- **Latency**: < 100ms execution
- **Uptime**: 99.9% availability
- **Success Rate**: 60-80% win rate (varies by market)
- **Drawdown**: < 5% maximum

### **Monitoring KPIs:**
- **Sharpe Ratio**: Risk-adjusted returns
- **Win Rate**: Percentage profitable trades
- **Profit Factor**: Gross profit / Gross loss
- **Max Drawdown**: Peak-to-valley decline

---

**🎯 Your Aventa HFT Pro 2026 is now ready for automated trading with AI and Telegram notifications!**

**Happy Trading & May Allah Bless Your Investments!** 🤲📈

---
*Last Updated: January 18, 2026*
*Version: 7.3.3*
*Developed by: Aventa AI Team*