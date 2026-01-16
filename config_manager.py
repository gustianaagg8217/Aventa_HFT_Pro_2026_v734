"""
Configuration Manager for Aventa HFT Pro 2026
Handles deep copying and config isolation between bots
"""

import copy
import json
import os
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages bot configurations with deep copy isolation"""
    
    DEFAULT_CONFIG = {
        # Trading Configuration
        'symbol': 'GOLD.ls',
        'default_volume': 0.01,
        'magic_number': 2026002,
        'risk_per_trade': 1.0,
        'min_signal_strength': 0.45,
        'max_spread': 0.12,
        'max_volatility':  0.005,
        'filling_mode': 'FOK',
        'sl_multiplier': 50.0,
        'risk_reward_ratio': 2.0,
        'tp_mode': 'FixedDollar',
        'tp_dollar_amount': 0.8,
        'max_floating_loss': 5.0,
        'max_floating_profit': 0.5,
        'mt5_path': 'C:\\Program Files\\XM Global MT5\\terminal64.exe',
        'enable_ml': False,
        'commission_per_trade': 0.9,
        
        # Indicators
        'ema_fast_period': 7,
        'ema_slow_period': 21,
        'rsi_period': 7,
        'rsi_overbought': 68,
        'rsi_oversold': 32,
        'atr_period': 14,
        'momentum_period': 5,
        
        # Risk Limits
        'max_daily_loss': 40.0,
        'max_daily_trades': 1000,
        'max_position_size': 2.0,
        'max_positions':  20,
        'max_drawdown_pct': 10.0,
        
        # Performance
        'tick_buffer_size': 1000,
        'analysis_interval': 0.1,
    }
    
    def __init__(self, config_dir='configs'):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)
    
    def create_isolated_config(self, base_config:  Dict = None, bot_id: str = None) -> Dict:
        """
        Create a completely isolated config (deep copy)
        
        Args:  
            base_config: Base configuration to copy from (or use DEFAULT_CONFIG)
            bot_id: Bot identifier (will increment magic number)
        
        Returns:
            Deep copied configuration
        """
        if base_config is None:
            base_config = self.DEFAULT_CONFIG
        
        # CRITICAL: Deep copy to prevent shared references
        config = copy.deepcopy(base_config)
        
        # ✅ FIX: Generate unique magic number WITHOUT hash collisions
        if bot_id:  
            # Extract numeric suffix from bot_id (e.g., "Bot_5" -> 5)
            import re
            match = re.search(r'_(\d+)$', bot_id)
            if match:
                bot_num = int(match.group(1))
                config['magic_number'] = 2026000 + bot_num
            else:
                # Fallback:  Use length-based offset if no number found
                config['magic_number'] = 2026000 + len(bot_id)
        
        # Add metadata
        config['_created_at'] = datetime.now().isoformat()
        config['_bot_id'] = bot_id
        
        logger.info(f"Created isolated config for {bot_id} (magic: {config['magic_number']})")
        
        return config
    
    def validate_config(self, config: Dict) -> bool:
        """
        Validate configuration
        
        Returns:
            True if valid, False otherwise
        """
        required_keys = [
            'symbol', 'default_volume', 'magic_number',
            'max_daily_loss', 'max_daily_trades'
        ]
        
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required config key: {key}")
                return False
        
        # Validate ranges
        if config['default_volume'] <= 0:
            logger.error("Volume must be positive")
            return False
        
        if config['max_daily_loss'] <= 0:
            logger.error("Max daily loss must be positive")
            return False
        
        return True
    
    def save_config(self, config: Dict, filename: str = None, bot_id: str = None):
        """
        Save configuration to file
        
        Args: 
            config: Configuration to save
            filename: Target filename (optional)
            bot_id: Bot identifier (used for default filename)
        """
        if filename is None:
            if bot_id:
                filename = f"{bot_id.replace(' ', '_')}_config.json"
            else:
                filename = f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.config_dir, filename)
        
        # Deep copy before saving (prevent mutation)
        save_data = copy.deepcopy(config)
        
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=4)
        
        logger.info(f"Config saved to {filepath}")
        return filepath
    
    def load_config(self, filename: str) -> Dict:
        """
        Load configuration from file
        
        Returns:
            Deep copied configuration
        """
        filepath = os.path.join(self.config_dir, filename)
        
        if not os.path.exists(filepath):
            logger.error(f"Config file not found: {filepath}")
            return None
        
        with open(filepath, 'r') as f:
            config = json.load(f)
        
        # CRITICAL: Deep copy after loading
        config = copy.deepcopy(config)
        
        logger.info(f"Config loaded from {filepath}")
        return config
    
    def merge_configs(self, base:  Dict, override: Dict) -> Dict:
        """
        Merge two configs (override takes precedence)
        
        Returns:
            Deep copied merged config
        """
        merged = copy.deepcopy(base)
        
        for key, value in override.items():
            if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
                # Recursive merge for nested dicts
                merged[key] = self.merge_configs(merged[key], value)
            else:
                merged[key] = copy.deepcopy(value)
        
        return merged
    
    def diff_configs(self, config1: Dict, config2: Dict) -> Dict:
        """
        Find differences between two configs
        
        Returns:
            Dict with changed keys
        """
        diff = {}
        
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            val1 = config1.get(key)
            val2 = config2.get(key)
            
            if val1 != val2:
                diff[key] = {
                    'old': val1,
                    'new': val2
                }
        
        return diff


if __name__ == "__main__":
    # Test config isolation
    manager = ConfigManager()
    
    # Create two isolated configs
    config1 = manager.create_isolated_config(bot_id="Bot_1")
    config2 = manager.create_isolated_config(bot_id="Bot_2")
    
    # Modify config1
    config1['symbol'] = 'EURUSD'
    
    # Verify config2 is unchanged
    assert config2['symbol'] == 'GOLD.ls', "Config isolation failed!"
    
    print("✅ Config isolation test passed")
    print(f"Bot 1 magic: {config1['magic_number']}")
    print(f"Bot 2 magic: {config2['magic_number']}")