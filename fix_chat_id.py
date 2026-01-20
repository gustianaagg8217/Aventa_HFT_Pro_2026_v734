"""
Fix Chat ID in config file
"""

import json
import os

config_file = "configs/telegram_hft_config.json"

print(f"Reading: {config_file}")
with open(config_file, 'r') as f:
    config = json.load(f)

print(f"\nCurrent config:")
print(f"  Chat IDs: {config.get('telegram', {}).get('chat_ids', [])}")

# Fix: Remove the extra 9
if 'telegram' in config:
    chat_ids = config['telegram'].get('chat_ids', [])
    # Fix each ID
    fixed_ids = []
    for cid in chat_ids:
        cid_str = str(cid)
        # If it's 7521820149, fix to 752182014
        if cid_str == '7521820149':
            print(f"\nFound wrong ID: {cid_str}")
            print(f"Fixing to: 752182014")
            fixed_ids.append('752182014')
        else:
            fixed_ids.append(cid_str)
    
    config['telegram']['chat_ids'] = fixed_ids
    
    # Save back
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\nSaved! New Chat IDs: {config['telegram']['chat_ids']}")
else:
    print("ERROR: No telegram config!")
