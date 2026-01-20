# Telegram Bot Manual Start - Workaround

Karena auto-start di GUI masih ada issue, saya sediakan cara manual start bot di background.

## Quick Start (Recommended)

### 1. Close GUI Launcher (jika masih buka)

### 2. Run bot starter script
```bash
python start_telegram_bot_manual.py
```

Script ini akan:
- ✅ Load Telegram config dari file
- ✅ Create bot instance  
- ✅ Start event loop di background
- ✅ Begin polling Telegram commands
- ✅ Keep running sampai Ctrl+C

Hasilnya:
```
Starting Telegram Bot: Trading Bot Account
Token: 8531073542:AAENQ-...
Chat ID: 752182014
Event loop started ✓
Bot polling active ✓
```

### 3. Open GUI Launcher (di terminal baru/berbeda)
```bash
python Aventa_HFT_Pro_2026_v7_3_3.py
```

### 4. Kirim Telegram Command
```
/bots
/start_bot Trading Bot Account
/stop_bot Trading Bot Account
```

Bot akan respons! ✅

---

## Architecture

```
┌─────────────────────────────┐
│  Telegram Bot Starter       │  (separate terminal)
│  (event loop + polling)     │
└────────────┬────────────────┘
             │ IPC communication
             ▼
┌─────────────────────────────┐
│      GUI Launcher           │  (main app)
│  - Control trading          │
│  - Monitor performance      │
│  - Receive bot updates      │
└─────────────────────────────┘
```

Bot dan GUI berkomunikasi via IPC (file-based queue) jadi bisa run di process berbeda.

---

## Cleanup

Saat shutdown:
1. Close GUI Launcher
2. Press Ctrl+C di terminal bot starter
3. Done!

---

## Troubleshoot

**Bot tidak respond di Telegram:**
- Check: Chat ID di GUI = 752182014
- Check: Bot token valid
- Check: Script `start_telegram_bot_manual.py` masih running (lihat terminal)

**Event loop not starting:**
- Jika ada error, akan terlihat di terminal saat run script

**Multiple bots:**
- Edit `start_telegram_bot_manual.py` dan tambah bot ke runner

---

## Next Step

1. Jalankan script starter
2. Buka GUI
3. Test Telegram command
4. Report jika ada error!
