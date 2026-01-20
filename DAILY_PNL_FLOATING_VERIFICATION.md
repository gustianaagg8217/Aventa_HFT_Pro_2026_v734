# Daily P&L - Floating P&L Verification

## Status: ✅ IMPLEMENTED & VERIFIED

Daily P&L now correctly includes the ACTUAL floating P&L from MT5, not just accumulated closed trades.

## Formula

```
Daily P&L = Realized P&L (Closed Trades Today) + Unrealized P&L (Floating from Open Positions)

Where:
- Realized P&L = Sum of profit from all closed deals today (history)
- Unrealized P&L = Current floating profit/loss from all open positions
- Result = Total daily profit/loss reflecting ACTUAL MT5 floating actual
```

## Implementation Details

### 1. Core Calculation in `get_today_trade_stats()` (Lines 1888-1943, aventa_hft_core.py)

```python
# Get today's closed deals (realized P&L)
realized_pnl = 0.0
for d in deals:
    if d.magic == magic:
        realized_pnl += d.profit  # From MT5 history

# Get current floating P&L from open positions
floating_pnl = 0.0
positions = mt5.positions_get(symbol=self.symbol)
if positions:
    for pos in positions:
        if pos.magic == magic:
            floating_pnl += pos.profit  # Current unrealized P&L

# Total Daily P&L = Realized + Floating
total_daily_pnl = realized_pnl + floating_pnl
```

**Key Points:**
- ✅ Closed trades counted from MT5 history_deals_get() [REALIZED]
- ✅ Open positions floating P&L from mt5.positions_get().profit [UNREALIZED]
- ✅ Only this bot's trades filtered by magic number
- ✅ Includes both wins and losses

### 2. Updated `get_performance_snapshot()` (Lines 1717-1780, aventa_hft_core.py)

```python
# Now calls the updated get_today_trade_stats()
trades_today, bot_wins, bot_losses, daily_pnl_actual = self.get_today_trade_stats()

# Returns daily_pnl with ACTUAL floating included
"daily_pnl": daily_pnl_actual  # ✅ INCLUDES FLOATING FROM OPEN POSITIONS
```

### 3. GUI Display (Line 2347-2362, Aventa_HFT_Pro_2026_v7_3_3.py)

```python
engine_snapshot = bot['engine'].get_performance_snapshot()
daily_pnl_actual = engine_snapshot.get('daily_pnl', 0.0)

# Display with actual floating P&L
self.risk_vars['daily_pnl'].set(f"${daily_pnl_actual:.2f}")
```

## Practical Examples

### Example 1: Winning Open Position
```
Closed Trades Today:
  - Trade 1: +$50
  - Trade 2: +$30
  Realized P&L: $80

Open Positions:
  - Position 1 (BUY): +$25 floating
  
Daily P&L = $80 + $25 = $105 ✅
```

### Example 2: Mixed Results
```
Closed Trades Today:
  - Trade 1: +$100
  - Trade 2: -$40
  Realized P&L: $60

Open Positions:
  - Position 1 (SELL): -$15 floating (loss)
  - Position 2 (BUY): +$10 floating (profit)
  Total Floating: -$5
  
Daily P&L = $60 + (-$5) = $55 ✅
```

### Example 3: No Closed Trades
```
Closed Trades Today: None
  Realized P&L: $0

Open Positions:
  - Position 1: -$50 floating (underwater)
  
Daily P&L = $0 + (-$50) = -$50 ✅
```

## Risk Calculation Integration

Daily P&L is now used in:
1. **Risk Level Assessment** (risk_manager.py lines 462-464)
   - HIGH: abs(daily_pnl) > max_daily_loss × 70%
   - MEDIUM: abs(daily_pnl) > max_daily_loss × 50%

2. **Daily P&L Percentage Display** (GUI)
   - Percentage = (abs(daily_pnl) / max_daily_loss) × 100

3. **Daily Loss Limit Check** (risk_manager.py line 132)
   - Circuit breaker: daily_pnl ≤ -max_daily_loss

## Why This Matters

**Before Fix:**
- Daily P&L only showed closed trades
- Open positions' floating loss ignored
- Risk level could be understated if positions underwater
- Example: +$500 closed trades but -$600 floating = showed +$500 (WRONG)

**After Fix:**
- Daily P&L shows COMPLETE picture
- Includes both realized and unrealized P&L
- Floating losses properly reflected in risk calculations
- Example: +$500 closed trades but -$600 floating = shows -$100 (CORRECT)

## Data Flow

```
MT5 Account
├── History Deals (Closed Trades)
│   └── Get profit per deal → Realized P&L
└── Open Positions
    └── Get pos.profit → Unrealized (Floating) P&L
        └── Combine: Total Daily P&L
            └── GUI Display: "$XXX.XX"
            └── Risk Assessment: Calculate risk level
            └── Circuit Breaker: Check loss limits
```

## Verification Checklist

- ✅ Realized P&L calculated from MT5 history_deals_get()
- ✅ Floating P&L calculated from mt5.positions_get().profit
- ✅ Both filtered by magic number (bot-specific)
- ✅ Combined in get_today_trade_stats()
- ✅ Returned via get_performance_snapshot()
- ✅ Displayed in GUI Risk Management tab
- ✅ Used in risk level calculation
- ✅ Includes both wins and losses
- ✅ Reflects ACTUAL MT5 floating actual
- ✅ Updates in real-time as positions change

## Integration Points

1. **Performance Tab**: Shows Daily P&L with floating included
2. **Risk Management Tab**: Displays Daily P&L and percentage of limit
3. **Risk Level Assessment**: HIGH/MEDIUM/LOW determined with floating considered
4. **Circuit Breaker**: Triggers when floating losses exceed threshold
5. **Logs**: Shows daily P&L updates in real-time

## Final Status

✅ **PRODUCTION READY**

Daily P&L now correctly represents:
- ✅ Realized profits from closed trades (MT5 history)
- ✅ Unrealized profits from floating open positions (MT5 positions)
- ✅ TOTAL daily P&L reflecting ACTUAL MT5 floating actual
- ✅ Accurate risk assessment based on complete P&L picture

---

**Last Updated:** January 21, 2026
**Changes:** Updated get_today_trade_stats() to include floating P&L from open positions
**Impact:** Daily P&L now reflects ACTUAL floating from MT5 instead of accumulated trades only
