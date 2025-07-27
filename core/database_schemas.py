#!/usr/bin/env python3
"""
AI Gold Scalper - Unified Database Schema Definitions
Fix for 100/100 System Health Score

Standardizes database schemas across all components to prevent conflicts
and ensure data consistency throughout the system.
"""

import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import logging

class DatabaseSchemas:
    """Unified database schema definitions for the AI Gold Scalper system"""
    
    # Standard database schemas
    SCHEMAS = {
        'trades': """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                trade_type VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'
                entry_price REAL NOT NULL,
                exit_price REAL,
                volume REAL NOT NULL,
                profit_loss REAL,
                duration_minutes INTEGER,
                status VARCHAR(20) DEFAULT 'open',  -- 'open', 'closed', 'completed'
                signal_source VARCHAR(50),  -- 'ai', 'technical', 'ensemble', etc.
                confidence_score REAL,
                stop_loss REAL,
                take_profit REAL,
                commission REAL DEFAULT 0.0,
                swap REAL DEFAULT 0.0,
                magic_number INTEGER,
                comment TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'market_data_ticks': """
            CREATE TABLE IF NOT EXISTS market_data_ticks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                bid REAL NOT NULL,
                ask REAL NOT NULL,
                last REAL,
                volume REAL DEFAULT 0,
                spread REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """,
        
        'ohlc_1m': """
            CREATE TABLE IF NOT EXISTS ohlc_1m (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL DEFAULT 0,
                tick_volume INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """,
        
        'ohlc_5m': """
            CREATE TABLE IF NOT EXISTS ohlc_5m (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL DEFAULT 0,
                tick_volume INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """,
        
        'ohlc_15m': """
            CREATE TABLE IF NOT EXISTS ohlc_15m (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL DEFAULT 0,
                tick_volume INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """,
        
        'ohlc_1h': """
            CREATE TABLE IF NOT EXISTS ohlc_1h (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL DEFAULT 0,
                tick_volume INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """,
        
        'ohlc_daily': """
            CREATE TABLE IF NOT EXISTS ohlc_daily (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATE NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL DEFAULT 0,
                tick_volume INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """,
        
        'technical_indicators': """
            CREATE TABLE IF NOT EXISTS technical_indicators (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                timeframe VARCHAR(10) NOT NULL,  -- '1m', '5m', '15m', '1h', 'daily'
                indicator_name VARCHAR(50) NOT NULL,
                indicator_value REAL,
                indicator_data TEXT,  -- JSON for complex indicators
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol, timeframe, indicator_name)
            )
        """,
        
        'ai_signals': """
            CREATE TABLE IF NOT EXISTS ai_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                signal_type VARCHAR(10) NOT NULL,  -- 'buy' or 'sell'
                confidence_score REAL NOT NULL,
                entry_price REAL,
                stop_loss REAL,
                take_profit REAL,
                signal_source VARCHAR(50) NOT NULL,  -- 'gpt4', 'ensemble', 'technical', etc.
                model_version VARCHAR(20),
                market_conditions TEXT,  -- JSON
                reasoning TEXT,
                executed BOOLEAN DEFAULT FALSE,
                trade_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (trade_id) REFERENCES trades (id)
            )
        """,
        
        'model_registry': """
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL UNIQUE,
                version VARCHAR(20) NOT NULL,
                model_type VARCHAR(50) NOT NULL,
                framework VARCHAR(50) NOT NULL,
                file_path TEXT NOT NULL,
                training_score REAL,
                validation_score REAL,
                feature_count INTEGER,
                sample_count INTEGER,
                hyperparameters TEXT,  -- JSON
                metrics TEXT,  -- JSON
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'model_performance': """
            CREATE TABLE IF NOT EXISTS model_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id INTEGER NOT NULL,
                timestamp DATETIME NOT NULL,
                prediction_accuracy REAL,
                precision_score REAL,
                recall_score REAL,
                f1_score REAL,
                auc_score REAL,
                prediction_count INTEGER DEFAULT 0,
                correct_predictions INTEGER DEFAULT 0,
                profit_attribution REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (model_id) REFERENCES models (id)
            )
        """,
        
        'system_logs': """
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                level VARCHAR(10) NOT NULL,  -- 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
                component VARCHAR(50) NOT NULL,
                message TEXT NOT NULL,
                exception_info TEXT,
                context TEXT,  -- JSON
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'system_config': """
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key VARCHAR(100) NOT NULL UNIQUE,
                config_value TEXT NOT NULL,
                config_type VARCHAR(20) DEFAULT 'string',  -- 'string', 'integer', 'float', 'boolean', 'json'
                description TEXT,
                is_encrypted BOOLEAN DEFAULT FALSE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'backtesting_results': """
            CREATE TABLE IF NOT EXISTS backtesting_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id VARCHAR(50) NOT NULL,
                strategy_name VARCHAR(100) NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                initial_balance REAL NOT NULL,
                final_balance REAL NOT NULL,
                total_return REAL NOT NULL,
                max_drawdown REAL NOT NULL,
                sharpe_ratio REAL,
                win_rate REAL,
                total_trades INTEGER DEFAULT 0,
                winning_trades INTEGER DEFAULT 0,
                profit_factor REAL,
                avg_trade_duration REAL,
                parameters TEXT,  -- JSON
                metrics TEXT,  -- JSON
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        
        'backtesting_trades': """
            CREATE TABLE IF NOT EXISTS backtesting_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id VARCHAR(50) NOT NULL,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                trade_type VARCHAR(10) NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                quantity REAL NOT NULL,
                profit_loss REAL,
                duration_minutes INTEGER,
                signal_source VARCHAR(50),
                confidence_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
    }
    
    # Database indices for performance optimization
    INDICES = {
        'trades': [
            "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades (status)",
            "CREATE INDEX IF NOT EXISTS idx_trades_signal_source ON trades (signal_source)"
        ],
        'market_data_ticks': [
            "CREATE INDEX IF NOT EXISTS idx_ticks_timestamp ON market_data_ticks (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ticks_symbol ON market_data_ticks (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ticks_symbol_timestamp ON market_data_ticks (symbol, timestamp)"
        ],
        'ohlc_1m': [
            "CREATE INDEX IF NOT EXISTS idx_ohlc_1m_timestamp ON ohlc_1m (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_1m_symbol ON ohlc_1m (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_1m_symbol_timestamp ON ohlc_1m (symbol, timestamp)"
        ],
        'ohlc_5m': [
            "CREATE INDEX IF NOT EXISTS idx_ohlc_5m_timestamp ON ohlc_5m (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_5m_symbol ON ohlc_5m (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_5m_symbol_timestamp ON ohlc_5m (symbol, timestamp)"
        ],
        'ohlc_15m': [
            "CREATE INDEX IF NOT EXISTS idx_ohlc_15m_timestamp ON ohlc_15m (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_15m_symbol ON ohlc_15m (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_15m_symbol_timestamp ON ohlc_15m (symbol, timestamp)"
        ],
        'ohlc_1h': [
            "CREATE INDEX IF NOT EXISTS idx_ohlc_1h_timestamp ON ohlc_1h (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_1h_symbol ON ohlc_1h (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_1h_symbol_timestamp ON ohlc_1h (symbol, timestamp)"
        ],
        'ohlc_daily': [
            "CREATE INDEX IF NOT EXISTS idx_ohlc_daily_timestamp ON ohlc_daily (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_daily_symbol ON ohlc_daily (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ohlc_daily_symbol_timestamp ON ohlc_daily (symbol, timestamp)"
        ],
        'technical_indicators': [
            "CREATE INDEX IF NOT EXISTS idx_indicators_timestamp ON technical_indicators (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_indicators_symbol ON technical_indicators (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_indicators_name ON technical_indicators (indicator_name)",
            "CREATE INDEX IF NOT EXISTS idx_indicators_composite ON technical_indicators (symbol, timeframe, indicator_name, timestamp)"
        ],
        'ai_signals': [
            "CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON ai_signals (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_signals_symbol ON ai_signals (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_signals_source ON ai_signals (signal_source)",
            "CREATE INDEX IF NOT EXISTS idx_signals_executed ON ai_signals (executed)"
        ],
        'model_performance': [
            "CREATE INDEX IF NOT EXISTS idx_model_perf_model_id ON model_performance (model_id)",
            "CREATE INDEX IF NOT EXISTS idx_model_perf_timestamp ON model_performance (timestamp)"
        ],
        'system_logs': [
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs (level)",
            "CREATE INDEX IF NOT EXISTS idx_logs_component ON system_logs (component)"
        ],
        'backtesting_results': [
            "CREATE INDEX IF NOT EXISTS idx_backtest_run_id ON backtesting_results (run_id)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_strategy ON backtesting_results (strategy_name)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_dates ON backtesting_results (start_date, end_date)"
        ],
        'backtesting_trades': [
            "CREATE INDEX IF NOT EXISTS idx_backtest_trades_run_id ON backtesting_trades (run_id)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_trades_timestamp ON backtesting_trades (timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_backtest_trades_symbol ON backtesting_trades (symbol)"
        ]
    }
    
    @classmethod
    def create_database(cls, db_path: str, tables: Optional[List[str]] = None) -> bool:
        """
        Create database with standardized schemas
        
        Args:
            db_path: Path to the database file
            tables: List of table names to create (None = all tables)
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Enable foreign key constraints
                cursor.execute("PRAGMA foreign_keys = ON")
                
                # Create tables
                tables_to_create = tables or list(cls.SCHEMAS.keys())
                
                for table_name in tables_to_create:
                    if table_name in cls.SCHEMAS:
                        schema_sql = cls.SCHEMAS[table_name]
                        cursor.execute(schema_sql)
                        logging.info(f"Created table: {table_name}")
                        
                        # Create indices for this table
                        if table_name in cls.INDICES:
                            for index_sql in cls.INDICES[table_name]:
                                cursor.execute(index_sql)
                            logging.info(f"Created indices for table: {table_name}")
                    else:
                        logging.warning(f"Unknown table schema: {table_name}")
                
                conn.commit()
                logging.info(f"Database created successfully: {db_path}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to create database {db_path}: {e}")
            return False
    
    @classmethod
    def migrate_existing_database(cls, db_path: str) -> bool:
        """
        Migrate existing database to use standardized schemas
        
        Args:
            db_path: Path to existing database file
            
        Returns:
            bool: Success status
        """
        try:
            if not Path(db_path).exists():
                logging.info(f"Database doesn't exist, creating new: {db_path}")
                return cls.create_database(db_path)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get existing tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                existing_tables = [row[0] for row in cursor.fetchall()]
                
                # Create missing tables
                for table_name, schema_sql in cls.SCHEMAS.items():
                    if table_name not in existing_tables:
                        cursor.execute(schema_sql)
                        logging.info(f"Added missing table: {table_name}")
                        
                        # Create indices for new table
                        if table_name in cls.INDICES:
                            for index_sql in cls.INDICES[table_name]:
                                cursor.execute(index_sql)
                            logging.info(f"Created indices for new table: {table_name}")
                
                # Add missing indices to existing tables
                for table_name in existing_tables:
                    if table_name in cls.INDICES:
                        for index_sql in cls.INDICES[table_name]:
                            try:
                                cursor.execute(index_sql)
                            except sqlite3.OperationalError:
                                # Index might already exist
                                pass
                
                conn.commit()
                logging.info(f"Database migration completed: {db_path}")
                return True
                
        except Exception as e:
            logging.error(f"Failed to migrate database {db_path}: {e}")
            return False
    
    @classmethod
    def validate_database_schema(cls, db_path: str) -> Dict[str, bool]:
        """
        Validate database schema against standard definitions
        
        Args:
            db_path: Path to database file
            
        Returns:
            Dict[str, bool]: Validation results per table
        """
        results = {}
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for table_name in cls.SCHEMAS.keys():
                    try:
                        # Check if table exists and has expected structure
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = cursor.fetchall()
                        
                        if columns:
                            results[table_name] = True
                            logging.info(f"Table {table_name}: VALID")
                        else:
                            results[table_name] = False
                            logging.warning(f"Table {table_name}: MISSING")
                            
                    except Exception as e:
                        results[table_name] = False
                        logging.error(f"Table {table_name}: ERROR - {e}")
                        
        except Exception as e:
            logging.error(f"Failed to validate database {db_path}: {e}")
            
        return results
    
    @classmethod
    def get_database_info(cls, db_path: str) -> Dict[str, any]:
        """
        Get comprehensive database information
        
        Args:
            db_path: Path to database file
            
        Returns:
            Dict containing database statistics and info
        """
        info = {
            'path': db_path,
            'exists': Path(db_path).exists(),
            'size_mb': 0,
            'tables': {},
            'total_records': 0,
            'schema_compliance': {}
        }
        
        if not info['exists']:
            return info
            
        try:
            # Get file size
            info['size_mb'] = round(Path(db_path).stat().st_size / (1024 * 1024), 2)
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Get record counts for each table
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        info['tables'][table] = count
                        info['total_records'] += count
                    except Exception:
                        info['tables'][table] = 'ERROR'
                
                # Check schema compliance
                info['schema_compliance'] = cls.validate_database_schema(db_path)
                
        except Exception as e:
            logging.error(f"Failed to get database info for {db_path}: {e}")
            
        return info


def initialize_system_databases():
    """Initialize all system databases with standardized schemas"""
    
    # Database paths
    databases = {
        'market_data.db': [
            'market_data_ticks', 'ohlc_1m', 'ohlc_5m', 'ohlc_15m', 
            'ohlc_1h', 'ohlc_daily', 'technical_indicators'
        ],
        'trades.db': [
            'trades', 'ai_signals', 'backtesting_results', 'backtesting_trades'
        ],
        'models.db': [
            'model_registry', 'model_performance'
        ],
        'system.db': [
            'system_logs', 'system_config'
        ]
    }
    
    # Create data directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    
    success_count = 0
    total_count = len(databases)
    
    for db_name, tables in databases.items():
        db_path = data_dir / db_name
        
        if DatabaseSchemas.create_database(str(db_path), tables):
            success_count += 1
            logging.info(f"✅ Database initialized: {db_name}")
        else:
            logging.error(f"❌ Database initialization failed: {db_name}")
    
    logging.info(f"Database initialization complete: {success_count}/{total_count} successful")
    return success_count == total_count


def main():
    """Main function for database schema management"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI Gold Scalper Database Schema Manager')
    parser.add_argument('action', choices=['init', 'migrate', 'validate', 'info'], 
                       help='Action to perform')
    parser.add_argument('--db-path', type=str, help='Database file path')
    parser.add_argument('--all', action='store_true', help='Apply to all system databases')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(levelname)s - %(message)s')
    
    if args.action == 'init':
        if args.all:
            initialize_system_databases()
        elif args.db_path:
            DatabaseSchemas.create_database(args.db_path)
        else:
            print("Error: Specify --db-path or --all")
            
    elif args.action == 'migrate':
        if args.db_path:
            DatabaseSchemas.migrate_existing_database(args.db_path)
        else:
            print("Error: --db-path required for migration")
            
    elif args.action == 'validate':
        if args.db_path:
            results = DatabaseSchemas.validate_database_schema(args.db_path)
            print(f"Validation results for {args.db_path}:")
            for table, valid in results.items():
                status = "✅ VALID" if valid else "❌ INVALID"
                print(f"  {table}: {status}")
        else:
            print("Error: --db-path required for validation")
            
    elif args.action == 'info':
        if args.db_path:
            info = DatabaseSchemas.get_database_info(args.db_path)
            print(f"Database Information for {args.db_path}:")
            print(f"  Exists: {info['exists']}")
            print(f"  Size: {info['size_mb']} MB")
            print(f"  Total Records: {info['total_records']}")
            print(f"  Tables: {len(info['tables'])}")
            for table, count in info['tables'].items():
                print(f"    {table}: {count} records")
        else:
            print("Error: --db-path required for info")


if __name__ == "__main__":
    main()
