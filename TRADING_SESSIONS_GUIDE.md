# Trading Sessions Configuration Guide

## Overview

Trading Sessions feature allows you to restrict bot trading to specific market hours (London, New York, or Asia sessions in GMT).

## Why Use Trading Sessions?

**For XAUUSD/GOLD specifically:**
- **London Session** (08:00-16:30 GMT): Tightest spreads, most consistent volatility ✅ BEST FOR HFT
- **New York Session** (13:00-21:00 GMT): Highest volatility, most volume ✅ BEST FOR SCALPING
- **Asia Session** (22:00-08:00 GMT): Low volume, wide spreads ❌ AVOID

## GUI Configuration

### Location
**Panel Kontrol** → **⏰ Trading Sessions (GMT)** section

### Settings

#### 1. Enable Trading Session Restrictions
- **Toggle**: Turn session restrictions on/off globally
- When **OFF**: Bot trades 24/7
- When **ON**: Bot only trades during selected sessions

#### 2. London Session 🇬🇧
```
Checkbox: ☑ London Session
Start: 08:00 (GMT)
End:   16:30 (GMT)
```
- **Best for**: Tight spreads, consistent trends
- **Volume**: Medium-High
- **Volatility**: 80-150 pips/day

#### 3. New York Session 🗽
```
Checkbox: ☑ New York Session
Start: 13:00 (GMT)
End:   21:00 (GMT)
```
- **Best for**: Big moves, breakouts
- **Volume**: Very High
- **Volatility**: 100-200+ pips/day
- ⚠️ Wide spreads during major news

#### 4. Asia Session 🏮
```
Checkbox: ☐ Asia Session (OFF by default)
Start: 22:00 (GMT)
End:   08:00 (GMT - next day)
```
- **Risk**: Low volume, unpredictable moves
- ❌ **NOT RECOMMENDED** for HFT bots

## Recommended Configurations

### 💎 For GOLD/XAUUSD HFT Bot (RECOMMENDED)
```
✅ Trading Sessions Enabled
✅ London Session:  08:00 - 16:30 GMT
✅ NY Session:      13:00 - 21:00 GMT
❌ Asia Session:    OFF
```

**Result**: Bot trades during London and NY (Best hours)
- Peak trading: **12:00-14:00 GMT** (London-NY overlap)

### 📈 For Aggressive Breakout Strategy
```
✅ Trading Sessions Enabled
❌ London Session:  OFF
✅ NY Session:      13:00 - 21:00 GMT
❌ Asia Session:    OFF
```

**Result**: Focus on NY volatility only

### 📊 For Conservative/Scalping
```
✅ Trading Sessions Enabled
✅ London Session:  08:00 - 16:30 GMT
❌ NY Session:      OFF
❌ Asia Session:    OFF
```

**Result**: Steady scalping during London hours

## Time Conversion Reference

### GMT Times to Your Local Timezone

**London Session (08:00-16:30 GMT)**
- UTC+0: 08:00-16:30
- UTC+1 (CET): 09:00-17:30
- UTC+8 (SGT): 16:00-00:30 (next day)
- EST (UTC-5): 03:00-11:30

**New York Session (13:00-21:00 GMT)**
- UTC+0: 13:00-21:00
- UTC+1 (CET): 14:00-22:00
- UTC+8 (SGT): 21:00-05:00 (next day)
- EST (UTC-5): 08:00-16:00

## Technical Implementation

### Backend Code (aventa_hft_core.py)

```python
def is_trading_session_allowed(self) -> bool:
    """Check if current time is within allowed trading sessions"""
    # Returns True if current GMT time is in any enabled session
    # Called before placing any trade
```

### How It Works

1. **Current Time Check**: Gets GMT time every tick
2. **Session Validation**: Compares against configured times
3. **Trading Decision**: 
   - ✅ **ALLOW** if within enabled session
   - ❌ **BLOCK** if outside all sessions
4. **Status Log**: Logs once per hour if trading blocked

## Configuration Storage

Sessions are saved in:
- **File**: `configs/Bot_1.json`
- **Structure**:
```json
{
  "trading_sessions_enabled": true,
  "london_session_enabled": true,
  "london_start": "08:00",
  "london_end": "16:30",
  "ny_session_enabled": true,
  "ny_start": "13:00",
  "ny_end": "21:00",
  "asia_session_enabled": false,
  "asia_start": "22:00",
  "asia_end": "08:00"
}
```

## Examples

### Example 1: London-Only Trading
```
Current Time: 14:30 GMT
London Session: 08:00-16:30 ✅ ALLOWED
New York Session: 13:00-21:00 (disabled)
Asia Session: OFF

Result: BOT TRADING ✅
```

### Example 2: Outside All Sessions
```
Current Time: 02:00 GMT
London Session: 08:00-16:30 ❌ NOT IN SESSION
New York Session: 13:00-21:00 ❌ NOT IN SESSION
Asia Session: OFF

Result: BOT PAUSED ❌
```

### Example 3: Asia Session Overlap (If Enabled)
```
Current Time: 23:30 GMT
London Session: 08:00-16:30 ❌ CLOSED
New York Session: 13:00-21:00 ❌ CLOSED
Asia Session: 22:00-08:00 ✅ ALLOWED

Result: BOT TRADING ✅ (Not recommended)
```

## Best Practices

1. **Always use GMT times**: All times are in GMT/UTC+0
2. **London + NY combo**: Most profitable for HFT
3. **Avoid news times**: Manually pause during major data releases
4. **Monitor overlap zones**:
   - 12:00-14:00 GMT = Best liquidity (London-NY overlap)
   - 16:30-17:00 GMT = London close, NY active
5. **Test your strategy**: Each pair/strategy works best in different sessions

## Troubleshooting

**Problem**: Bot not trading when expected
- ❌ Check if sessions are **enabled** (checkbox)
- ❌ Verify **times are in GMT** (not local time)
- ❌ Confirm at least **one session is checked**
- ✅ Check logs: "Outside trading sessions at HH:MM GMT"

**Problem**: Changing settings doesn't apply
- ❌ **Save bot config** after changing times
- ❌ **Stop bot** before changing times
- ✅ After changing, click **Save Config** button

**Problem**: Bot trading 24/7 despite settings
- ❌ Check if "Enable Trading Session Restrictions" is **ON**
- ❌ Check if "trading_sessions_enabled" is **true** in JSON
- ✅ Restart bot after enabling

## Default Configuration

```
Trading Sessions Enabled: ON
└─ London Session: ON (08:00-16:30 GMT)
└─ NY Session: ON (13:00-21:00 GMT)
└─ Asia Session: OFF (22:00-08:00 GMT)
```

This default is **optimized for GOLD/XAUUSD HFT**.

---

**Last Updated:** January 21, 2026
**Feature**: Trading Session Restrictions
**Status**: ✅ Production Ready
