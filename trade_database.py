"""
SQLite Trade Persistence for Aventa HFT Pro 2026
Stores trade history and performance metrics
"""

import sqlite3
from contextlib import closing
from datetime import datetime
from typing import List, Dict, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)


class TradeDatabase:
    """SQLite database for trade persistence"""
    
    def __init__(self, db_path='trades.db'):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            # Trades table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    symbol TEXT NOT NULL,
                    trade_type TEXT NOT NULL,
                    volume REAL NOT NULL,
                    open_price REAL NOT NULL,
                    close_price REAL NOT NULL,
                    profit REAL NOT NULL,
                    duration REAL NOT NULL,
                    reason TEXT,
                    magic_number INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Performance metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bot_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    total_trades INTEGER,
                    wins INTEGER,
                    losses INTEGER,
                    win_rate REAL,
                    daily_pnl REAL,
                    max_drawdown REAL,
                    sharpe_ratio REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(bot_id, date)
                )
            ''')
            
            # Indices for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trades_bot_timestamp 
                ON trades(bot_id, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_trades_symbol 
                ON trades(symbol)
            ''')
            
            conn.commit()
            
        logger.info(f"Trade database initialized:  {self.db_path}")
    
    def record_trade(self, bot_id: str, trade_data: Dict):
        """
        Record a single trade
        
        Args: 
            bot_id: Bot identifier
            trade_data: Trade information dict
        """
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO trades (
                    bot_id, timestamp, symbol, trade_type, volume,
                    open_price, close_price, profit, duration, reason, magic_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bot_id,
                trade_data.get('timestamp', datetime.now().timestamp()),
                trade_data.get('symbol'),
                trade_data.get('trade_type'),
                trade_data.get('volume'),
                trade_data.get('open_price'),
                trade_data.get('close_price'),
                trade_data.get('profit'),
                trade_data.get('duration'),
                trade_data.get('reason'),
                trade_data.get('magic_number')
            ))
            
            conn.commit()
            
            logger.debug(f"Trade recorded for {bot_id}: {trade_data.get('profit'):.2f}")
    
    def get_trades(self, bot_id: str = None, start_date: datetime = None, 
                   end_date: datetime = None, limit: int = None) -> List[Dict]:
        """
        Retrieve trades with filters
        
        Args:
            bot_id: Filter by bot (optional)
            start_date: Start datetime (optional)
            end_date: End datetime (optional)
            limit: Maximum number of results (optional)
        
        Returns:
            List of trade dictionaries
        """
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if bot_id: 
                query += " AND bot_id = ?"
                params.append(bot_id)
            
            if start_date: 
                query += " AND timestamp >= ?"
                params.append(start_date.timestamp())
            
            if end_date: 
                query += " AND timestamp <= ?"
                params.append(end_date.timestamp())
            
            query += " ORDER BY timestamp DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            trades = [dict(row) for row in rows]
            
            logger.debug(f"Retrieved {len(trades)} trades")
            return trades
    
    def get_daily_stats(self, bot_id: str, date: datetime = None) -> Dict:
        """
        Get daily statistics for a bot
        
        Args:
            bot_id:  Bot identifier
            date: Date (defaults to today)
        
        Returns:
            Statistics dictionary
        """
        if date is None:
            date = datetime.now()
        
        # ✅ FIX:  Use timestamp range instead of DATE() function
        # Start of day (00:00:00)
        start_of_day = datetime.combine(date.date(), datetime.min.time())
        # End of day (23:59:59)
        end_of_day = datetime.combine(date.date(), datetime.max.time())
        
        # Convert to Unix timestamps
        start_ts = start_of_day.timestamp()
        end_ts = end_of_day.timestamp()
        
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(CASE WHEN profit < 0 THEN 1 ELSE 0 END) as losses,
                    SUM(profit) as total_pnl,
                    AVG(profit) as avg_profit,
                    MAX(profit) as best_trade,
                    MIN(profit) as worst_trade
                FROM trades
                WHERE bot_id = ? 
                AND timestamp >= ? 
                AND timestamp <= ?
            ''', (bot_id, start_ts, end_ts))
            
            row = cursor.fetchone()
            
            if row:
                total_trades = row[0]
                wins = row[1] or 0
                losses = row[2] or 0
                
                win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
                
                return {
                    'total_trades': total_trades,
                    'wins': wins,
                    'losses': losses,
                    'win_rate': win_rate,
                    'total_pnl': row[3] or 0,
                    'avg_profit':  row[4] or 0,
                    'best_trade': row[5] or 0,
                    'worst_trade': row[6] or 0
                }
            
            return {}
    
    def save_performance(self, bot_id: str, metrics: Dict):
        """
        Save daily performance metrics
        
        Args: 
            bot_id: Bot identifier
            metrics: Performance metrics dict
        """
        date = datetime.now().strftime('%Y-%m-%d')
        
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO performance (
                    bot_id, date, total_trades, wins, losses,
                    win_rate, daily_pnl, max_drawdown, sharpe_ratio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                bot_id,
                date,
                metrics.get('total_trades', 0),
                metrics.get('wins', 0),
                metrics.get('losses', 0),
                metrics.get('win_rate', 0),
                metrics.get('daily_pnl', 0),
                metrics.get('max_drawdown', 0),
                metrics.get('sharpe_ratio', 0)
            ))
            
            conn.commit()
            
        logger.debug(f"Performance saved for {bot_id}")
    
    def export_to_csv(self, output_file: str, bot_id: str = None):
        """Export trades to CSV"""
        import csv
        
        trades = self.get_trades(bot_id=bot_id)
        
        if not trades: 
            logger.warning("No trades to export")
            return False
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=trades[0].keys())
            writer.writeheader()
            writer.writerows(trades)
        
        logger.info(f"Exported {len(trades)} trades to {output_file}")
        return True
    
    def get_statistics(self, bot_id: str = None, days: int = 30) -> Dict:
        """
        Get comprehensive statistics
        
        Args: 
            bot_id: Bot identifier (optional)
            days: Number of days to analyze
        
        Returns:
            Statistics dictionary
        """
        start_date = datetime.now().timestamp() - (days * 86400)
        
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT 
                    COUNT(*) as total_trades,
                    SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) as wins,
                    SUM(profit) as total_pnl,
                    AVG(profit) as avg_profit,
                    MAX(profit) as best_trade,
                    MIN(profit) as worst_trade,
                    AVG(duration) as avg_duration
                FROM trades
                WHERE timestamp >= ?
            '''
            
            params = [start_date]
            
            if bot_id:
                query += " AND bot_id = ?"
                params.append(bot_id)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row and row[0] > 0:
                total = row[0]
                wins = row[1] or 0
                
                return {
                    'total_trades': total,
                    'wins': wins,
                    'losses': total - wins,
                    'win_rate': (wins / total * 100),
                    'total_pnl': row[2] or 0,
                    'avg_profit': row[3] or 0,
                    'best_trade': row[4] or 0,
                    'worst_trade': row[5] or 0,
                    'avg_duration': row[6] or 0
                }
            
            return {}
    
    def cleanup_old_trades(self, days:  int = 90):
        """Delete trades older than N days"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        with closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM trades WHERE timestamp < ?', (cutoff,))
            deleted = cursor.rowcount
            
            conn.commit()
            
        logger.info(f"Cleaned up {deleted} old trades (older than {days} days)")
        return deleted


if __name__ == "__main__":
    # Test database
    db = TradeDatabase('test_trades.db')
    
    # Record test trade
    trade = {
        'timestamp': datetime.now().timestamp(),
        'symbol': 'GOLD.ls',
        'trade_type': 'BUY',
        'volume': 0.01,
        'open_price':  2600.00,
        'close_price': 2601.00,
        'profit':  1.00,
        'duration': 60.0,
        'reason': 'Test trade',
        'magic_number': 2026001
    }
    
    db.record_trade('Bot_1', trade)
    
    # Get stats
    stats = db.get_daily_stats('Bot_1')
    print(f"Daily stats:  {stats}")
    
    # Export
    db.export_to_csv('test_export.csv', 'Bot_1')
    
    print("✅ Database test passed")