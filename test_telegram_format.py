#!/usr/bin/env python3
"""
Test telegram close position signal formatting with account info
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from Aventa_HFT_Pro_2026_v7_3_3 import HFTProGUI

# Test the formatter with account info
msg = HFTProGUI.format_close_position_signal(
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
msg_na = HFTProGUI.format_close_position_signal(
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