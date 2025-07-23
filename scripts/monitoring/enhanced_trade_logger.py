#!/usr/bin/env python3
"""
AI Gold Scalper - Enhanced Trade Logger
Phase 1: Enhanced Logging System Implementation

Comprehensive trade logging system that tracks:
- Signal sources and confidence levels
- Market conditions at entry/exit
- Trade outcomes vs predictions
- Performance attribution by signal source
- Risk management effectiveness

Version: 1.0.0
Created: 2025-01-22
"""

import os
import sys
import json
import logging
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class TradeSignal:
    """Structure for trade signal data"""
    signal_id: str
    timestamp: str
    symbol: str = "XAUUSD"
    signal_type: str = "HOLD"  # BUY, SELL, HOLD
    confidence: float = 0.0
    source: str = "unknown"
    reasoning: str = ""
    market_conditions: Dict = None
    risk_params: Dict = None
    
    def __post_init__(self):
        if self.market_conditions is None:
            self.market_conditions = {}
        if self.risk_params is None:
            self.risk_params = {}

@dataclass
class TradeExecution:
    """Structure for trade execution data"""
    trade_id: str
    signal_id: str
    timestamp: str
    symbol: str = "XAUUSD"
    action: str = "OPEN"  # OPEN, CLOSE
    price: float = 0.0
    volume: float = 0.0
    sl_price: float = 0.0
    tp_price: float = 0.0
    platform_id: str = ""
    execution_time_ms: float = 0.0

@dataclass
class TradeOutcome:
    """Structure for completed trade outcome"""
    trade_id: str
    signal_id: str
    timestamp: str
    symbol: str = "XAUUSD"
    entry_price: float = 0.0
    exit_price: float = 0.0
    volume: float = 0.0
    pnl_pips: float = 0.0
    pnl_usd: float = 0.0
    duration_minutes: int = 0
    outcome: str = "UNKNOWN"  # WIN, LOSS, BREAKEVEN
    exit_reason: str = "UNKNOWN"  # TP, SL, MANUAL, TIMEOUT

class EnhancedTradeLogger:
    """Comprehensive trade logging system"""
    
    def __init__(self, db_path: str = "scripts/monitoring/trade_logs.db"):
        self.db_path = db_path
        self.setup_logging()
        self.setup_database()
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(f"{__name__}.EnhancedTradeLogger")
        self.logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler for trade logs
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        log_file = self.db_path.replace('.db', '_activity.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.info("Enhanced Trade Logger initialized")
    
    def setup_database(self):
        """Initialize SQLite database with required tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Signals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    reasoning TEXT,
                    market_conditions TEXT,
                    risk_params TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Executions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS executions (
                    execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL,
                    signal_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    price REAL NOT NULL,
                    volume REAL NOT NULL,
                    sl_price REAL,
                    tp_price REAL,
                    platform_id TEXT,
                    execution_time_ms REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
                )
            ''')
            
            # Outcomes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS outcomes (
                    outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trade_id TEXT NOT NULL UNIQUE,
                    signal_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    exit_price REAL NOT NULL,
                    volume REAL NOT NULL,
                    pnl_pips REAL NOT NULL,
                    pnl_usd REAL NOT NULL,
                    duration_minutes INTEGER,
                    outcome TEXT NOT NULL,
                    exit_reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (signal_id) REFERENCES signals (signal_id)
                )
            ''')
            
            # Performance tracking table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    context TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            self.logger.info("Database tables initialized successfully")
    
    def log_signal(self, signal: TradeSignal) -> bool:
        """Log a trading signal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO signals (
                        signal_id, timestamp, symbol, signal_type, confidence,
                        source, reasoning, market_conditions, risk_params
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    signal.signal_id,
                    signal.timestamp,
                    signal.symbol,
                    signal.signal_type,
                    signal.confidence,
                    signal.source,
                    signal.reasoning,
                    json.dumps(signal.market_conditions),
                    json.dumps(signal.risk_params)
                ))
                conn.commit()
                
            self.logger.info(f"Signal logged: {signal.signal_id} - {signal.signal_type} ({signal.confidence}% confidence)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging signal: {e}")
            return False
    
    def log_execution(self, execution: TradeExecution) -> bool:
        """Log a trade execution"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO executions (
                        trade_id, signal_id, timestamp, symbol, action,
                        price, volume, sl_price, tp_price, platform_id, execution_time_ms
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    execution.trade_id,
                    execution.signal_id,
                    execution.timestamp,
                    execution.symbol,
                    execution.action,
                    execution.price,
                    execution.volume,
                    execution.sl_price,
                    execution.tp_price,
                    execution.platform_id,
                    execution.execution_time_ms
                ))
                conn.commit()
                
            self.logger.info(f"Execution logged: {execution.trade_id} - {execution.action} at {execution.price}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging execution: {e}")
            return False
    
    def log_outcome(self, outcome: TradeOutcome) -> bool:
        """Log a trade outcome"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO outcomes (
                        trade_id, signal_id, timestamp, symbol, entry_price,
                        exit_price, volume, pnl_pips, pnl_usd, duration_minutes,
                        outcome, exit_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    outcome.trade_id,
                    outcome.signal_id,
                    outcome.timestamp,
                    outcome.symbol,
                    outcome.entry_price,
                    outcome.exit_price,
                    outcome.volume,
                    outcome.pnl_pips,
                    outcome.pnl_usd,
                    outcome.duration_minutes,
                    outcome.outcome,
                    outcome.exit_reason
                ))
                conn.commit()
                
            self.logger.info(f"Outcome logged: {outcome.trade_id} - {outcome.outcome} ({outcome.pnl_pips} pips)")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging outcome: {e}")
            return False
    
    def log_performance_metric(self, metric_type: str, metric_name: str, 
                             metric_value: float, context: str = "") -> bool:
        """Log a performance metric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO performance_metrics (
                        timestamp, metric_type, metric_name, metric_value, context
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    metric_type,
                    metric_name,
                    metric_value,
                    context
                ))
                conn.commit()
                
            self.logger.info(f"Performance metric logged: {metric_name} = {metric_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error logging performance metric: {e}")
            return False
    
    def get_signal_performance(self, days_back: int = 30) -> Dict[str, Any]:
        """Get signal performance analysis"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                # Signal accuracy by source
                accuracy_query = '''
                    SELECT s.source, 
                           COUNT(*) as total_signals,
                           COUNT(CASE WHEN o.outcome = 'WIN' THEN 1 END) as wins,
                           COUNT(CASE WHEN o.outcome = 'LOSS' THEN 1 END) as losses,
                           AVG(s.confidence) as avg_confidence,
                           AVG(o.pnl_pips) as avg_pips,
                           SUM(o.pnl_usd) as total_pnl
                    FROM signals s
                    LEFT JOIN outcomes o ON s.signal_id = o.signal_id
                    WHERE s.timestamp > ?
                    GROUP BY s.source
                '''
                
                df_accuracy = pd.read_sql_query(accuracy_query, conn, params=[cutoff_date])
                
                # Signal type performance
                signal_type_query = '''
                    SELECT s.signal_type,
                           COUNT(*) as total_signals,
                           COUNT(CASE WHEN o.outcome = 'WIN' THEN 1 END) as wins,
                           AVG(o.pnl_pips) as avg_pips,
                           SUM(o.pnl_usd) as total_pnl
                    FROM signals s
                    LEFT JOIN outcomes o ON s.signal_id = o.signal_id
                    WHERE s.timestamp > ? AND s.signal_type != 'HOLD'
                    GROUP BY s.signal_type
                '''
                
                df_signal_types = pd.read_sql_query(signal_type_query, conn, params=[cutoff_date])
                
                # Calculate win rates
                if not df_accuracy.empty:
                    df_accuracy['win_rate'] = (df_accuracy['wins'] / (df_accuracy['wins'] + df_accuracy['losses'])) * 100
                    df_accuracy['win_rate'] = df_accuracy['win_rate'].fillna(0)
                
                if not df_signal_types.empty:
                    df_signal_types['win_rate'] = (df_signal_types['wins'] / (df_signal_types['wins'] + df_signal_types['losses'])) * 100
                    df_signal_types['win_rate'] = df_signal_types['win_rate'].fillna(0)
                
                return {
                    'analysis_period_days': days_back,
                    'by_source': df_accuracy.to_dict('records') if not df_accuracy.empty else [],
                    'by_signal_type': df_signal_types.to_dict('records') if not df_signal_types.empty else [],
                    'summary': {
                        'total_signals': int(df_accuracy['total_signals'].sum()) if not df_accuracy.empty else 0,
                        'total_wins': int(df_accuracy['wins'].sum()) if not df_accuracy.empty else 0,
                        'total_losses': int(df_accuracy['losses'].sum()) if not df_accuracy.empty else 0,
                        'overall_win_rate': float(df_accuracy['wins'].sum() / max(1, df_accuracy['wins'].sum() + df_accuracy['losses'].sum()) * 100) if not df_accuracy.empty else 0,
                        'total_pnl_usd': float(df_accuracy['total_pnl'].sum()) if not df_accuracy.empty else 0,
                        'avg_pips_per_trade': float(df_accuracy['avg_pips'].mean()) if not df_accuracy.empty else 0
                    }
                }
                
        except Exception as e:
            self.logger.error(f"Error getting signal performance: {e}")
            return {'error': str(e)}
    
    def get_recent_trades(self, limit: int = 50) -> List[Dict]:
        """Get recent trade data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT s.signal_id, s.timestamp as signal_time, s.signal_type,
                           s.confidence, s.source, s.reasoning,
                           o.trade_id, o.entry_price, o.exit_price, 
                           o.pnl_pips, o.pnl_usd, o.outcome, o.exit_reason
                    FROM signals s
                    LEFT JOIN outcomes o ON s.signal_id = o.signal_id
                    ORDER BY s.timestamp DESC
                    LIMIT ?
                '''
                
                cursor = conn.cursor()
                cursor.execute(query, [limit])
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                return results
                
        except Exception as e:
            self.logger.error(f"Error getting recent trades: {e}")
            return []
    
    def export_performance_report(self, days_back: int = 30) -> str:
        """Export comprehensive performance report"""
        try:
            performance = self.get_signal_performance(days_back)
            recent_trades = self.get_recent_trades(100)
            
            report_path = f"scripts/monitoring/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report_data = {
                'generated_at': datetime.now().isoformat(),
                'analysis_period_days': days_back,
                'performance_analysis': performance,
                'recent_trades': recent_trades,
                'database_stats': self._get_database_stats()
            }
            
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            self.logger.info(f"Performance report exported to: {report_path}")
            return report_path
            
        except Exception as e:
            self.logger.error(f"Error exporting performance report: {e}")
            return ""
    
    def _get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                stats = {}
                for table in ['signals', 'executions', 'outcomes', 'performance_metrics']:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                
                # Get date range
                cursor.execute('SELECT MIN(timestamp), MAX(timestamp) FROM signals')
                result = cursor.fetchone()
                stats['data_range'] = {
                    'earliest_signal': result[0] if result[0] else None,
                    'latest_signal': result[1] if result[1] else None
                }
                
                return stats
                
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}

def create_sample_data():
    """Create sample trade data for testing"""
    logger = EnhancedTradeLogger()
    
    print("Creating sample trade data for testing...")
    
    # Sample signal
    signal = TradeSignal(
        signal_id="SIG_TEST_001",
        timestamp=datetime.now().isoformat(),
        symbol="XAUUSD",
        signal_type="BUY",
        confidence=75.5,
        source="Technical Analysis",
        reasoning="RSI oversold + MACD bullish crossover",
        market_conditions={
            "rsi": 28.5,
            "macd": 0.15,
            "session": "London",
            "volatility": "medium"
        },
        risk_params={
            "sl": 50.0,
            "tp": 100.0,
            "lot_size": 0.01
        }
    )
    
    # Log the signal
    logger.log_signal(signal)
    
    # Sample execution
    execution = TradeExecution(
        trade_id="TRD_001",
        signal_id="SIG_TEST_001",
        timestamp=datetime.now().isoformat(),
        symbol="XAUUSD",
        action="OPEN",
        price=2650.50,
        volume=0.01,
        sl_price=2600.50,
        tp_price=2750.50,
        platform_id="MT5_001",
        execution_time_ms=125.5
    )
    
    logger.log_execution(execution)
    
    # Sample outcome (simulating a winning trade)
    outcome = TradeOutcome(
        trade_id="TRD_001",
        signal_id="SIG_TEST_001",
        timestamp=datetime.now().isoformat(),
        symbol="XAUUSD",
        entry_price=2650.50,
        exit_price=2750.50,
        volume=0.01,
        pnl_pips=100.0,
        pnl_usd=10.00,
        duration_minutes=45,
        outcome="WIN",
        exit_reason="TP"
    )
    
    logger.log_outcome(outcome)
    
    # Log some performance metrics
    logger.log_performance_metric("accuracy", "overall_win_rate", 73.5)
    logger.log_performance_metric("risk", "max_drawdown_pips", -45.2)
    logger.log_performance_metric("performance", "profit_factor", 1.85)
    
    print("✅ Sample data created successfully!")
    
    # Generate performance report
    report_path = logger.export_performance_report(7)
    print(f"📊 Performance report generated: {report_path}")
    
    return logger

def main():
    """Main function for testing the enhanced trade logger"""
    print("="*60)
    print("AI GOLD SCALPER - ENHANCED TRADE LOGGER")
    print("Phase 1: Enhanced Logging System")
    print("="*60)
    print()
    
    # Create and test the logger
    logger = create_sample_data()
    
    print("\n" + "="*60)
    print("📈 PERFORMANCE ANALYSIS")
    print("="*60)
    
    # Get performance analysis
    performance = logger.get_signal_performance(7)
    if 'error' not in performance:
        print(f"Analysis Period: {performance['analysis_period_days']} days")
        print(f"Total Signals: {performance['summary']['total_signals']}")
        print(f"Win Rate: {performance['summary']['overall_win_rate']:.1f}%")
        print(f"Total P&L: ${performance['summary']['total_pnl_usd']:.2f}")
        print(f"Avg Pips/Trade: {performance['summary']['avg_pips_per_trade']:.1f}")
        
        print("\n📊 Performance by Source:")
        for source_data in performance['by_source']:
            print(f"  {source_data['source']}: {source_data.get('win_rate', 0):.1f}% win rate ({source_data['total_signals']} signals)")
    
    print("\n" + "="*60)
    print("🎯 NEXT STEPS:")
    print("  1. Integrate with enhanced_ai_server_consolidated.py")
    print("  2. Add real-time signal logging")
    print("  3. Create performance dashboard")
    print("  4. Set up automated reporting")
    print("="*60)

if __name__ == "__main__":
    main()
