#!/usr/bin/env python3
"""
Test telegram close position signal formatting with account info
"""
import datetime
import pytz

def format_close_position_signal(bot_id, symbol, ticket, profit, volume, balance=None, equity=None, free_margin=None, margin_level=None):
    """Test version of the format method"""
    # Format account info with N/A fallback
    balance_str = f"{balance:.2f}" if balance is not None else "N/A"
    equity_str = f"{equity:.2f}" if equity is not None else "N/A"
    free_margin_str = f"{free_margin:.2f}" if free_margin is not None else "N/A"
    margin_level_str = f"{margin_level:.2f}%" if margin_level is not None else "N/A"

    # Get current time in Jakarta timezone
    jakarta_tz = pytz.timezone('Asia/Jakarta')
    current_time = datetime.datetime.now(jakarta_tz).strftime('%Y-%m-%d %H:%M:%S')

    message = f"""🚀 **CLOSE POSITION SIGNAL**
🤖 Bot: {bot_id}
📊 Symbol: {symbol}
🎫 Ticket: {ticket}
💰 Profit: ${profit:.2f}
📈 Volume: {volume}

💳 **Account Summary:**
💵 Balance: ${balance_str}
📊 Equity: ${equity_str}
🆓 Free Margin: ${free_margin_str}
📊 Margin Level: {margin_level_str}

⏰ Time: {current_time} WIB"""

    return message

# Test the formatter with account info
msg = format_close_position_signal(
    bot_id='Bot_5',
    symbol='BTCUSD.futu',
    ticket=12345678,
    profit=0.15,
    volume=0.01,
    balance=6780.98,
    equity=6780.71,
    free_margin=6399.97,
    margin_level=1780.93
)

print("Formatted close position message:")
print("=" * 50)
print(msg)
print("=" * 50)

# Test with None values (should show N/A)
msg_na = format_close_position_signal(
    bot_id='Bot_5',
    symbol='BTCUSD.futu',
    ticket=12345678,
    profit=0.15,
    volume=0.01,
    balance=None,
    equity=None,
    free_margin=None,
    margin_level=None
)

print("\nWith None values (should show N/A):")
print("=" * 50)
print(msg_na)
print("=" * 50)