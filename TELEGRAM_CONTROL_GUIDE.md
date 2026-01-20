# 📱 Kontrol Bot dari Telegram - Panduan Lengkap

## Ringkasan Fitur

Anda sekarang dapat mengontrol **start/stop bot** dari Telegram **tanpa perlu buka VPS**. Cukup kirim perintah Telegram, dan GUI Launcher akan merespons secara real-time.

### Fitur Utama:
✅ **Start bot dari Telegram** - `/start_bot <bot_id>`  
✅ **Stop bot dari Telegram** - `/stop_bot <bot_id>`  
✅ **Lihat daftar bot dan statusnya** - `/bots`  
✅ **Status GUI otomatis berubah** ke "Start trading" atau "Stop trading"  
✅ **Notifikasi real-time** dari Telegram dengan konfirmasi  
✅ **Multi-bot support** - Kontrol bot mana saja yang aktif di GUI  

---

## Setup Telegram Bot

Anda sudah memiliki token Telegram:

```
Bot Name: Aventa HFT Pro 2026 v733
Token: 8531073542:AAENQ-O9fnaHpFCvBB11xxa9vWq5aT22hLA
```

### Langkah Setup:

1. **Pastikan bot sudah dikonfigurasi di GUI**
   - Di tab "📱 Telegram Service", masukkan token
   - Masukkan Chat ID Anda
   - Click "Connect Telegram"

2. **Tambahkan bot sebagai admin di Telegram**
   - Cari bot: `Aventa HFT Pro 2026 v733` di Telegram
   - Click /start untuk mengaktifkan

3. **Siap digunakan!**
   - GUI Launcher akan otomatis mendengarkan perintah dari Telegram

---

## Perintah Telegram

### 1. Lihat Daftar Bot dan Statusnya

```
/bots
```

**Response:**
```
🤖 Bot Status Report
━━━━━━━━━━━━━━━━━━━━

🟢 Bot_1
   Symbol: EURUSD
   Magic: 2026001
   Status: TRADING ACTIVE
   Last update: 2026-01-20 14:30:45

🔴 Bot_2
   Symbol: GOLD
   Magic: 2026002
   Status: STOPPED
   Last update: 2026-01-20 14:25:30

━━━━━━━━━━━━━━━━━━━━
Total bots: 2
Running: 1
Stopped: 1

Commands:
/start_bot <bot_id> - Start bot
/stop_bot <bot_id> - Stop bot
```

### 2. Start Bot

**Format:**
```
/start_bot <bot_id>
```

**Contoh:**
```
/start_bot Bot_1
```

**Response jika berhasil:**
```
✅ Bot Started!

Bot ID: Bot_1
Started by: @your_username
Time: 14:35:20

🟢 Status: TRADING ACTIVE
```

**Response jika gagal:**
```
❌ Failed to start bot:
Bot is already running
```

### 3. Stop Bot

**Format:**
```
/stop_bot <bot_id>
```

**Contoh:**
```
/stop_bot Bot_1
```

**Response jika berhasil:**
```
✅ Bot Stopped!

Bot ID: Bot_1
Stopped by: @your_username
Time: 14:35:25

🔴 Status: STOPPED
```

**Response jika gagal:**
```
❌ Failed to stop bot:
Bot is already stopped
```

### 4. Lihat Daftar Bot Tersedia

Panggil `/start_bot` tanpa parameter:
```
/start_bot
```

**Response:**
```
🤖 Available Bots:
━━━━━━━━━━━━━━━━

🟢 Bot_1 - RUNNING
🔴 Bot_2 - STOPPED

Usage:
/start_bot <bot_id>
Example: /start_bot Bot_1
```

---

## Cara Kerja Teknis

### Arsitektur Komunikasi

```
Telegram Bot
    ↓
    ├─ /start_bot Bot_1
    ├─ /stop_bot Bot_1
    └─ /bots
         ↓
   [IPC Channel - JSON Files]
   .ipc/bot_commands.json
   .ipc/bot_responses.json
   .ipc/bot_status.json
         ↓
   GUI Launcher (Aventa_HFT_Pro_2026_v7_3_3.py)
    ├─ telegram_integration.py
    ├─ Proses Command
    ├─ Jalankan start_trading() / stop_trading()
    └─ Update Status
         ↓
   Telegram Bot
   [Kirim Response ke User]
```

### File-File Baru

1. **`bot_control_ipc.py`** - IPC module untuk komunikasi
   - `BotControlIPC` class
   - Thread-safe communication
   - Command queuing & response handling

2. **`gui_telegram_integration.py`** - Integration layer
   - `GUITelegramIntegration` class
   - Command listener thread
   - Status update management

3. **`.ipc/` folder** - IPC file storage
   - `bot_commands.json` - Perintah dari Telegram
   - `bot_responses.json` - Response ke Telegram
   - `bot_status.json` - Status semua bot

### Alur Eksekusi

**Saat user kirim `/start_bot Bot_1`:**

1. Telegram bot menerima command
2. Validasi user authorized
3. Cek bot ada di file `.ipc/bot_status.json`
4. Send command ke `.ipc/bot_commands.json`
5. GUI listener thread membaca command
6. GUI set `active_bot_id = Bot_1`
7. GUI call `start_trading()` method
8. Bot engine start, `is_running = True`
9. GUI update status di `.ipc/bot_status.json`
10. Telegram bot baca response dari `.ipc/bot_responses.json`
11. Kirim notifikasi ke user

**Response time:** Biasanya 0.5-1 detik

---

## Status Perubahan di GUI

Saat bot di-start/stop dari Telegram:

### Sebelum (di GUI):
```
Status: Stopped
Button: [START TRADING] [disabled STOP TRADING]
```

### Sesaat setelah `/start_bot Bot_1`:
```
Status: ⏳ STARTING...
```

### Setelah Bot Fully Start:
```
Status: 🟢 TRADING ACTIVE
Button: [disabled START TRADING] [STOP TRADING]
```

### Sesaat setelah `/stop_bot Bot_1`:
```
Status: ⏳ STOPPING...
```

### Setelah Bot Fully Stop:
```
Status: 🔴 STOPPED
Button: [START TRADING] [disabled STOP TRADING]
```

---

## Fitur Keamanan

### Authorization
- Hanya user dalam `allowed_users` list yang bisa kontrol bot
- User ID dan username di-log di setiap command

### Validasi
- Cek bot existence sebelum execute command
- Cek status bot (already running/stopped)
- Timeout untuk response (5 detik)

### Logging
- Semua command di-log dengan timestamp
- Username & user ID di-record
- Command success/failure di-track

---

## Contoh Use Case

### Scenario 1: Start Bot Saat Sedang Perjalanan

```
User di jalan dengan HP:

[14:30] /bots
Response: Bot_1 STOPPED, Bot_2 STOPPED

[14:31] /start_bot Bot_1
Response: ✅ Bot Started! 🟢 Status: TRADING ACTIVE

[14:32] Di GUI Launcher (di VPS):
        Status bar berubah jadi "Bot_1: TRADING ACTIVE"
        Button START TRADING jadi disabled
        Button STOP TRADING jadi enabled
```

### Scenario 2: Emergency Stop Dari HP

```
User melihat ada problem via /status:
💰 Balance: $10,500
📊 Equity: $10,200
💵 Profit: -$300 (loss!)

[14:45] /stop_bot Bot_1
Response: ✅ Bot Stopped! 🔴 Status: STOPPED

[14:45] Di GUI Launcher:
        Bot immediately stop
        Status bar: "Bot_1: Stopped"
        Button STOP TRADING jadi disabled
```

### Scenario 3: Multi-Bot Control

```
User punya 3 bot running:

[15:00] /bots
Response:
🟢 Bot_1 RUNNING (EURUSD)
🟢 Bot_2 RUNNING (GOLD)
🔴 Bot_3 STOPPED

[15:01] /stop_bot Bot_1
✅ Bot_1 Stopped

[15:02] /stop_bot Bot_2
✅ Bot_2 Stopped

[15:03] /start_bot Bot_3
✅ Bot_3 Started

[15:04] /bots
Response:
🔴 Bot_1 STOPPED
🔴 Bot_2 STOPPED
🟢 Bot_3 RUNNING (GBPUSD)
```

---

## Troubleshooting

### ❌ Bot tidak respond

**Problem:** `/start_bot Bot_1` tidak ada response

**Solusi:**
1. Pastikan GUI Launcher running
2. Pastikan bot sudah di-setup di GUI
3. Check folder `.ipc/` exists
4. Restart GUI Launcher

### ❌ "Bot not found"

**Problem:** `/start_bot Bot_1` response: "Bot not found"

**Solusi:**
1. Check bot name (case-sensitive)
2. Gunakan `/bots` untuk lihat daftar bot
3. Tambah bot di GUI terlebih dahulu

### ❌ "Already running"

**Problem:** `/start_bot Bot_1` response: "Bot already running"

**Solusi:**
1. Bot sudah aktif, tidak perlu start lagi
2. Gunakan `/stop_bot Bot_1` dulu baru start

### ❌ Response delay (>5 detik)

**Problem:** Telegram tidak menerima response

**Solusi:**
1. Command sudah sent tapi response timeout
2. Check CPU/RAM di server
3. Restart GUI Launcher
4. Reduce update frequency di performance display

### ❌ Telegram says "Unauthorized"

**Problem:** `/start_bot` response: "Unauthorized"

**Solusi:**
1. User ID Anda belum dalam whitelist
2. Contact admin untuk add user ID
3. Buka chat dengan telegram bot, note user ID dari /start

---

## Monitoring & Logging

### Lihat Log di GUI

Tab "📝 Logs" akan menampilkan:
```
[14:30:15] ✓ Telegram integration ready
[14:31:02] Processing command: start for bot Bot_1 by user @username
[14:31:03] ✓ Bot_1 started successfully!
[14:31:03] Command 19f7d4a2... completed successfully
```

### Lihat Log di Server

File `.ipc/bot_commands.json`:
```json
{
  "commands": [
    {
      "command_id": "19f7d4a2-abc1-4321-xyz9-def456789abc",
      "command": "start",
      "bot_id": "Bot_1",
      "user_id": 123456789,
      "username": "your_username",
      "timestamp": "2026-01-20T14:31:02.123456",
      "status": "completed",
      "completed_at": "2026-01-20T14:31:03.456789"
    }
  ]
}
```

---

## Advanced Configuration

### Customize Response Time

File `gui_telegram_integration.py`:

```python
def __init__(self, gui_instance=None):
    ...
    self.update_interval = 0.5  # Change this (in seconds)
```

Smaller value = faster response but more CPU usage

### Cleanup Old Commands

Otomatis cleanup commands older than 1 day:

```python
ipc = get_ipc()
ipc.cleanup_old_commands(days=1)  # Change days as needed
```

---

## Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Start bot dari Telegram | ✅ Active | Real-time command processing |
| Stop bot dari Telegram | ✅ Active | Thread-safe implementation |
| Multi-bot control | ✅ Active | Control multiple bots independently |
| Status sync | ✅ Active | GUI status updates instantly |
| Authorization | ✅ Active | User whitelist validation |
| Logging | ✅ Active | Full audit trail |
| Emergency stop | ✅ Active | Instant bot shutdown |
| Response timeout | ✅ Active | 5-second timeout for reliability |

---

## Next Steps

1. **Test Telegram Commands**
   - Jalankan GUI Launcher
   - Kirim `/bots` untuk test
   - Coba `/start_bot` dan `/stop_bot`

2. **Monitor Logs**
   - Lihat tab "Logs" di GUI
   - Check `.ipc/` folder untuk debug

3. **Set Whitelist Users**
   - Di `telegram_bot.py`, configure `allowed_users` list
   - Add user ID Anda

4. **Production Deployment**
   - Test di environment baru
   - Monitor response times
   - Setup log rotation untuk `.ipc/` files

---

*Dibuat: 20 Januari 2026*  
*Versi: 1.0*  
*Kompatibel dengan: Aventa HFT Pro 2026 v7.3.3+*
