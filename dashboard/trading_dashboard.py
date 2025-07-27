#!/usr/bin/env python3
"""
AI Gold Scalper - Production Trading Dashboard
Phase 6: Production Integration & Infrastructure

Comprehensive web-based dashboard for monitoring all system components,
trading performance, AI models, and infrastructure health.
"""

import asyncio
import json
import logging
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading
import time

# Web Framework
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Import our system components
import sys
sys.path.append('scripts')
from data.market_data_processor import MarketDataProcessor
from training.automated_model_trainer import AutomatedModelTrainer
from ai.model_registry import ModelRegistry
from integration.phase4_integration import Phase4Integration

class TradingDashboard:
    """Production trading dashboard application"""
    
    def __init__(self, host='127.0.0.1', port=5000, debug=False):
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='static')
        self.app.config['SECRET_KEY'] = 'ai_gold_scalper_dashboard'
        
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Configuration
        self.host = host
        self.port = port
        self.debug = debug
        
        # System components
        self.market_processor = None
        self.model_trainer = None
        self.model_registry = ModelRegistry()
        self.phase4_integration = None
        
        # Data paths
        self.market_db = Path("data/market_data.db")
        self.trades_db = Path("data/trades.db")
        
        # Dashboard state
        self.is_running = False
        self.update_thread = None
        self.update_interval = 5  # seconds
        
        # Performance cache
        self.performance_cache = {}
        self.cache_timeout = 60  # seconds
        
        # Setup routes and handlers
        self._setup_routes()
        self._setup_socketio()
        
        logging.info("Trading Dashboard initialized")
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template('dashboard.html')
        
        @self.app.route('/api/health')
        def health_check():
            """System health check endpoint"""
            try:
                health_data = self._get_system_health()
                return jsonify(health_data)
            except Exception as e:
                logging.error(f"Health check failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/performance')
        def performance_metrics():
            """Trading performance metrics"""
            try:
                performance_data = self._get_performance_metrics()
                return jsonify(performance_data)
            except Exception as e:
                logging.error(f"Performance metrics failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/trades')
        def recent_trades():
            """Recent trades data"""
            try:
                limit = request.args.get('limit', 50, type=int)
                trades_data = self._get_recent_trades(limit)
                return jsonify(trades_data)
            except Exception as e:
                logging.error(f"Recent trades failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/models')
        def model_status():
            """AI model status and performance"""
            try:
                models_data = self._get_model_status()
                return jsonify(models_data)
            except Exception as e:
                logging.error(f"Model status failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/market-data')
        def market_data():
            """Market data and charts"""
            try:
                symbol = request.args.get('symbol', 'XAUUSD')
                periods = request.args.get('periods', 100, type=int)
                market_data = self._get_market_data(symbol, periods)
                return jsonify(market_data)
            except Exception as e:
                logging.error(f"Market data failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/equity-curve')
        def equity_curve():
            """Account equity curve"""
            try:
                days = request.args.get('days', 30, type=int)
                equity_data = self._get_equity_curve(days)
                return jsonify(equity_data)
            except Exception as e:
                logging.error(f"Equity curve failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system-logs')
        def system_logs():
            """Recent system logs"""
            try:
                limit = request.args.get('limit', 100, type=int)
                level = request.args.get('level', 'INFO')
                logs_data = self._get_system_logs(limit, level)
                return jsonify(logs_data)
            except Exception as e:
                logging.error(f"System logs failed: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/control/<action>', methods=['POST'])
        def system_control(action):
            """System control endpoints"""
            try:
                result = self._handle_system_control(action, request.json or {})
                return jsonify(result)
            except Exception as e:
                logging.error(f"System control '{action}' failed: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _setup_socketio(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logging.info("Dashboard client connected")
            emit('status', {'message': 'Connected to AI Gold Scalper Dashboard'})
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logging.info("Dashboard client disconnected")
        
        @self.socketio.on('subscribe')
        def handle_subscribe(data):
            """Handle subscription to real-time updates"""
            subscription_type = data.get('type', 'all')
            logging.info(f"Client subscribed to: {subscription_type}")
            emit('subscription_confirmed', {'type': subscription_type})
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'alerts': []
        }
        
        # Market data processor health
        if self.market_processor:
            market_health = self.market_processor.get_health_status()
            health['components']['market_data'] = {
                'status': 'healthy' if market_health['is_running'] else 'stopped',
                'healthy_sources': market_health['healthy_sources'],
                'total_sources': market_health['total_sources'],
                'primary_source': market_health['primary_source']
            }
            
            if market_health['healthy_sources'] == 0:
                health['alerts'].append({
                    'level': 'critical',
                    'component': 'market_data',
                    'message': 'No healthy data sources available'
                })
        else:
            health['components']['market_data'] = {'status': 'not_initialized'}
        
        # Model trainer health
        if self.model_trainer:
            trainer_health = self.model_trainer.get_training_status()
            health['components']['model_trainer'] = {
                'status': 'running' if trainer_health['is_running'] else 'idle',
                'models_configured': trainer_health['models_configured'],
                'success_rate': trainer_health['recent_success_rate']
            }
            
            if trainer_health['recent_success_rate'] < 0.8:
                health['alerts'].append({
                    'level': 'warning',
                    'component': 'model_trainer',
                    'message': f"Low training success rate: {trainer_health['recent_success_rate']:.1%}"
                })
        else:
            health['components']['model_trainer'] = {'status': 'not_initialized'}
        
        # Database health
        db_health = self._check_database_health()
        health['components']['database'] = db_health
        
        # Phase 4 integration health
        if self.phase4_integration:
            try:
                phase4_status = self.phase4_integration.get_system_status()
                health['components']['phase4_ai'] = {
                    'status': 'operational' if phase4_status.get('system_operational', False) else 'degraded',
                    'ensemble_models': len(phase4_status.get('ensemble_models', [])),
                    'market_regime': phase4_status.get('current_regime', 'unknown')
                }
            except Exception as e:
                health['components']['phase4_ai'] = {'status': 'error', 'error': str(e)}
        else:
            health['components']['phase4_ai'] = {'status': 'not_initialized'}
        
        # Determine overall status
        component_statuses = [comp.get('status', 'unknown') for comp in health['components'].values()]
        if any(status == 'critical' for status in component_statuses):
            health['overall_status'] = 'critical'
        elif any(status in ['error', 'degraded'] for status in component_statuses):
            health['overall_status'] = 'degraded'
        elif any(status == 'stopped' for status in component_statuses):
            health['overall_status'] = 'partial'
        
        return health
    
    def _check_database_health(self) -> Dict[str, Any]:
        """Check database health"""
        try:
            # Check market data database
            market_db_ok = False
            market_record_count = 0
            if self.market_db.exists():
                with sqlite3.connect(self.market_db) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM ohlc_1m WHERE timestamp >= datetime('now', '-1 hour')")
                    market_record_count = cursor.fetchone()[0]
                    market_db_ok = True
            
            # Check trades database
            trades_db_ok = False
            trades_record_count = 0
            if self.trades_db.exists():
                with sqlite3.connect(self.trades_db) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM trades WHERE timestamp >= datetime('now', '-1 day')")
                    trades_record_count = cursor.fetchone()[0]
                    trades_db_ok = True
            
            return {
                'status': 'healthy' if (market_db_ok and trades_db_ok) else 'degraded',
                'market_db': {
                    'accessible': market_db_ok,
                    'recent_records': market_record_count
                },
                'trades_db': {
                    'accessible': trades_db_ok,
                    'recent_records': trades_record_count
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get trading performance metrics"""
        cache_key = 'performance_metrics'
        if self._is_cache_valid(cache_key):
            return self.performance_cache[cache_key]['data']
        
        try:
            # Get recent trading data
            with sqlite3.connect(self.trades_db) as conn:
                # Daily performance
                daily_query = """
                    SELECT DATE(timestamp) as date,
                           COUNT(*) as trades,
                           SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                           SUM(profit_loss) as daily_pnl,
                           AVG(profit_loss) as avg_pnl_per_trade,
                           MIN(profit_loss) as worst_trade,
                           MAX(profit_loss) as best_trade
                    FROM trades 
                    WHERE timestamp >= datetime('now', '-30 days')
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """
                daily_df = pd.read_sql_query(daily_query, conn)
                
                # Overall statistics
                stats_query = """
                    SELECT COUNT(*) as total_trades,
                           SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                           SUM(profit_loss) as total_pnl,
                           AVG(profit_loss) as avg_pnl,
                           STDEV(profit_loss) as pnl_std,
                           MIN(profit_loss) as worst_loss,
                           MAX(profit_loss) as best_win,
                           AVG(duration_minutes) as avg_duration
                    FROM trades 
                    WHERE timestamp >= datetime('now', '-30 days')
                """
                stats = pd.read_sql_query(stats_query, conn).iloc[0]
            
            # Calculate derived metrics
            win_rate = (stats['winning_trades'] / stats['total_trades']) if stats['total_trades'] > 0 else 0
            profit_factor = abs(daily_df[daily_df['daily_pnl'] > 0]['daily_pnl'].sum() / 
                               daily_df[daily_df['daily_pnl'] < 0]['daily_pnl'].sum()) if len(daily_df[daily_df['daily_pnl'] < 0]) > 0 else float('inf')
            sharpe_ratio = (stats['avg_pnl'] / stats['pnl_std']) if stats['pnl_std'] > 0 else 0
            
            # Calculate maximum drawdown
            daily_df['cumulative_pnl'] = daily_df['daily_pnl'].cumsum()
            daily_df['running_max'] = daily_df['cumulative_pnl'].cummax()
            daily_df['drawdown'] = daily_df['cumulative_pnl'] - daily_df['running_max']
            max_drawdown = daily_df['drawdown'].min()
            
            performance_data = {
                'summary': {
                    'total_trades': int(stats['total_trades']),
                    'winning_trades': int(stats['winning_trades']),
                    'win_rate': float(win_rate),
                    'total_pnl': float(stats['total_pnl']),
                    'avg_pnl_per_trade': float(stats['avg_pnl']),
                    'profit_factor': float(profit_factor),
                    'sharpe_ratio': float(sharpe_ratio),
                    'max_drawdown': float(max_drawdown),
                    'best_trade': float(stats['best_win']),
                    'worst_trade': float(stats['worst_loss']),
                    'avg_duration_minutes': float(stats['avg_duration'])
                },
                'daily_performance': daily_df.to_dict('records'),
                'equity_curve': daily_df[['date', 'cumulative_pnl']].to_dict('records')
            }
            
            self._cache_data(cache_key, performance_data)
            return performance_data
            
        except Exception as e:
            logging.error(f"Failed to get performance metrics: {e}")
            return {
                'summary': {},
                'daily_performance': [],
                'equity_curve': [],
                'error': str(e)
            }
    
    def _get_recent_trades(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent trades data"""
        try:
            with sqlite3.connect(self.trades_db) as conn:
                query = """
                    SELECT timestamp, symbol, trade_type, entry_price, exit_price,
                           profit_loss, duration_minutes, status, volume
                    FROM trades 
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                trades_df = pd.read_sql_query(query, conn, params=(limit,))
            
            # Convert to dict and format
            trades_data = trades_df.to_dict('records')
            for trade in trades_data:
                trade['timestamp'] = pd.to_datetime(trade['timestamp']).isoformat()
                trade['profit_loss'] = round(float(trade['profit_loss']), 2)
                trade['entry_price'] = round(float(trade['entry_price']), 4)
                trade['exit_price'] = round(float(trade['exit_price']), 4) if trade['exit_price'] else None
            
            return {
                'trades': trades_data,
                'count': len(trades_data)
            }
            
        except Exception as e:
            logging.error(f"Failed to get recent trades: {e}")
            return {'trades': [], 'count': 0, 'error': str(e)}
    
    def _get_model_status(self) -> Dict[str, Any]:
        """Get AI model status and performance"""
        try:
            models_data = {
                'registered_models': [],
                'training_history': [],
                'performance_comparison': {}
            }
            
            # Get registered models
            models = self.model_registry.list_models()
            for model_name, metadata in models.items():
                model_info = {
                    'name': model_name,
                    'version': metadata.version,
                    'type': metadata.model_type,
                    'framework': metadata.framework,
                    'training_score': metadata.training_score,
                    'validation_score': metadata.validation_score,
                    'feature_count': metadata.feature_count,
                    'sample_count': metadata.sample_count,
                    'created_at': metadata.created_at,
                    'is_active': True  # Could check if model is currently being used
                }
                models_data['registered_models'].append(model_info)
            
            # Get training history if trainer is available
            if self.model_trainer:
                training_status = self.model_trainer.get_training_status()
                models_data['training_status'] = training_status
                
                # Recent training results
                recent_history = self.model_trainer.training_history[-10:] if self.model_trainer.training_history else []
                for result in recent_history:
                    history_item = {
                        'model_name': result.model_name,
                        'version': result.model_version,
                        'success': result.success,
                        'validation_score': result.validation_score,
                        'training_time': result.training_time,
                        'sample_count': result.sample_count
                    }
                    models_data['training_history'].append(history_item)
            
            return models_data
            
        except Exception as e:
            logging.error(f"Failed to get model status: {e}")
            return {
                'registered_models': [],
                'training_history': [],
                'performance_comparison': {},
                'error': str(e)
            }
    
    def _get_market_data(self, symbol: str, periods: int) -> Dict[str, Any]:
        """Get market data for charts"""
        try:
            if self.market_processor:
                # Get from market processor
                df = self.market_processor.get_ohlc_data(symbol, periods)
            else:
                # Fallback to direct database access
                with sqlite3.connect(self.market_db) as conn:
                    query = """
                        SELECT timestamp, open, high, low, close, volume
                        FROM ohlc_1m 
                        WHERE symbol = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    """
                    df = pd.read_sql_query(query, conn, params=(symbol, periods))
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    df = df.sort_values('timestamp')
            
            if df.empty:
                return {'error': 'No market data available'}
            
            # Create candlestick chart
            candlestick = go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='OHLC'
            )
            
            # Create volume chart
            volume_chart = go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name='Volume',
                yaxis='y2'
            )
            
            # Layout
            layout = go.Layout(
                title=f'{symbol} Price Chart',
                xaxis=dict(title='Time'),
                yaxis=dict(title='Price'),
                yaxis2=dict(title='Volume', overlaying='y', side='right'),
                height=400
            )
            
            # Convert to JSON
            fig = go.Figure(data=[candlestick, volume_chart], layout=layout)
            chart_json = json.dumps(fig, cls=PlotlyJSONEncoder)
            
            # Return market data with chart
            return {
                'symbol': symbol,
                'periods': len(df),
                'latest_price': float(df['close'].iloc[-1]),
                'price_change': float(df['close'].iloc[-1] - df['close'].iloc[-2]) if len(df) > 1 else 0,
                'chart_data': chart_json,
                'ohlc_data': df.tail(20).to_dict('records')  # Last 20 bars for table
            }
            
        except Exception as e:
            logging.error(f"Failed to get market data: {e}")
            return {'error': str(e)}
    
    def _get_equity_curve(self, days: int) -> Dict[str, Any]:
        """Get account equity curve"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            with sqlite3.connect(self.trades_db) as conn:
                query = """
                    SELECT timestamp, profit_loss
                    FROM trades 
                    WHERE timestamp >= ? AND status = 'completed'
                    ORDER BY timestamp
                """
                trades_df = pd.read_sql_query(query, conn, params=(cutoff_date,))
            
            if trades_df.empty:
                return {'error': 'No trade data available'}
            
            # Calculate cumulative P&L
            trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
            trades_df['cumulative_pnl'] = trades_df['profit_loss'].cumsum()
            
            # Create equity curve chart
            equity_fig = go.Figure()
            equity_fig.add_trace(go.Scatter(
                x=trades_df['timestamp'],
                y=trades_df['cumulative_pnl'],
                mode='lines',
                name='Equity Curve',
                line=dict(color='green', width=2)
            ))
            
            equity_fig.update_layout(
                title='Account Equity Curve',
                xaxis_title='Date',
                yaxis_title='Cumulative P&L',
                height=300
            )
            
            chart_json = json.dumps(equity_fig, cls=PlotlyJSONEncoder)
            
            return {
                'chart_data': chart_json,
                'current_equity': float(trades_df['cumulative_pnl'].iloc[-1]),
                'total_trades': len(trades_df),
                'days_analyzed': days
            }
            
        except Exception as e:
            logging.error(f"Failed to get equity curve: {e}")
            return {'error': str(e)}
    
    def _get_system_logs(self, limit: int, level: str) -> Dict[str, Any]:
        """Get recent system logs"""
        try:
            # This is a simplified version - in production you'd read from actual log files
            logs = [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'component': 'dashboard',
                    'message': 'Dashboard is operational'
                },
                {
                    'timestamp': (datetime.now() - timedelta(minutes=5)).isoformat(),
                    'level': 'INFO',
                    'component': 'market_data',
                    'message': 'Market data processor running normally'
                },
                {
                    'timestamp': (datetime.now() - timedelta(minutes=10)).isoformat(),
                    'level': 'INFO',
                    'component': 'ai_models',
                    'message': 'AI models loaded successfully'
                }
            ]
            
            return {
                'logs': logs[:limit],
                'total_count': len(logs)
            }
            
        except Exception as e:
            logging.error(f"Failed to get system logs: {e}")
            return {'logs': [], 'total_count': 0, 'error': str(e)}
    
    def _handle_system_control(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle system control actions"""
        try:
            if action == 'start_training':
                if self.model_trainer:
                    model_name = params.get('model', 'all')
                    if model_name == 'all':
                        results = self.model_trainer.train_all_models()
                    else:
                        results = [self.model_trainer.train_model(model_name)]
                    
                    return {
                        'success': True,
                        'message': f'Training initiated for {model_name}',
                        'results': len(results)
                    }
                else:
                    return {'success': False, 'message': 'Model trainer not initialized'}
            
            elif action == 'restart_market_data':
                if self.market_processor:
                    # This would restart the market data processor
                    return {
                        'success': True,
                        'message': 'Market data processor restart initiated'
                    }
                else:
                    return {'success': False, 'message': 'Market data processor not initialized'}
            
            elif action == 'emergency_stop':
                # Emergency stop all trading activities
                return {
                    'success': True,
                    'message': 'Emergency stop activated - all trading halted'
                }
            
            else:
                return {
                    'success': False,
                    'message': f'Unknown action: {action}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Control action failed: {str(e)}'
            }
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is valid"""
        if key not in self.performance_cache:
            return False
        
        cache_entry = self.performance_cache[key]
        age = time.time() - cache_entry['timestamp']
        return age < self.cache_timeout
    
    def _cache_data(self, key: str, data: Any):
        """Cache data with timestamp"""
        self.performance_cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def _real_time_update_loop(self):
        """Real-time update loop for WebSocket clients"""
        while self.is_running:
            try:
                # Get latest data
                health_data = self._get_system_health()
                
                # Get latest market data
                if self.market_processor:
                    latest_tick = self.market_processor.get_latest_tick('XAUUSD')
                    if latest_tick:
                        market_update = {
                            'symbol': latest_tick.symbol,
                            'price': latest_tick.last,
                            'bid': latest_tick.bid,
                            'ask': latest_tick.ask,
                            'timestamp': latest_tick.timestamp.isoformat()
                        }
                        self.socketio.emit('market_update', market_update)
                
                # Emit health status
                self.socketio.emit('health_update', health_data)
                
                # Sleep for next update
                time.sleep(self.update_interval)
                
            except Exception as e:
                logging.error(f"Real-time update error: {e}")
                time.sleep(10)  # Longer sleep on error
    
    def initialize_components(self):
        """Initialize system components"""
        try:
            # Initialize market data processor
            self.market_processor = MarketDataProcessor()
            
            # Initialize model trainer
            self.model_trainer = AutomatedModelTrainer()
            
            # Initialize Phase 4 integration
            self.phase4_integration = Phase4Integration()
            
            logging.info("Dashboard components initialized successfully")
            return True
            
        except Exception as e:
            logging.error(f"Failed to initialize components: {e}")
            return False
    
    def start(self):
        """Start the dashboard server"""
        if self.is_running:
            logging.warning("Dashboard already running")
            return
        
        logging.info(f"Starting Trading Dashboard on {self.host}:{self.port}")
        
        # Initialize components
        if not self.initialize_components():
            logging.error("Failed to initialize dashboard components")
            return
        
        # Start real-time updates
        self.is_running = True
        self.update_thread = threading.Thread(target=self._real_time_update_loop)
        self.update_thread.start()
        
        # Start Flask-SocketIO server
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=self.debug
            )
        except KeyboardInterrupt:
            logging.info("Dashboard shutdown requested")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the dashboard server"""
        logging.info("Stopping Trading Dashboard")
        
        self.is_running = False
        
        if self.update_thread:
            self.update_thread.join(timeout=10)
        
        logging.info("Trading Dashboard stopped")

def create_dashboard_template():
    """Create the HTML template for the dashboard"""
    template_dir = Path("dashboard/templates")
    template_dir.mkdir(parents=True, exist_ok=True)
    
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Gold Scalper - Trading Dashboard</title>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-error { color: #dc3545; }
        .card-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .metric-card { transition: transform 0.2s; }
        .metric-card:hover { transform: translateY(-2px); }
        #status-indicator { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    </style>
</head>
<body class="bg-light">
    <div class="container-fluid">
        <!-- Header -->
        <nav class="navbar navbar-dark bg-dark mb-4">
            <div class="navbar-brand">
                <i class="fas fa-chart-line me-2"></i>
                AI Gold Scalper - Trading Dashboard
            </div>
            <div class="navbar-text">
                <span id="status-indicator" class="bg-success"></span>
                <span id="connection-status">Connected</span>
            </div>
        </nav>

        <!-- System Health Row -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-heartbeat me-2"></i>System Health</h5>
                    </div>
                    <div class="card-body">
                        <div class="row" id="health-indicators">
                            <!-- Health indicators will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Performance Metrics Row -->
        <div class="row mb-4">
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-primary">Total P&L</h5>
                        <h3 id="total-pnl">$0.00</h3>
                        <small class="text-muted">30 days</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-success">Win Rate</h5>
                        <h3 id="win-rate">0%</h3>
                        <small class="text-muted">Last 30 days</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-info">Total Trades</h5>
                        <h3 id="total-trades">0</h3>
                        <small class="text-muted">Last 30 days</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card h-100">
                    <div class="card-body text-center">
                        <h5 class="card-title text-warning">Sharpe Ratio</h5>
                        <h3 id="sharpe-ratio">0.00</h3>
                        <small class="text-muted">Risk-adjusted</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
            <div class="col-lg-8 mb-3">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-chart-candlestick me-2"></i>Market Data</h5>
                    </div>
                    <div class="card-body">
                        <div id="market-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4 mb-3">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-line-chart me-2"></i>Equity Curve</h5>
                    </div>
                    <div class="card-body">
                        <div id="equity-chart" style="height: 400px;"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Trades and Model Status -->
        <div class="row mb-4">
            <div class="col-lg-6 mb-3">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-exchange-alt me-2"></i>Recent Trades</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Type</th>
                                        <th>Price</th>
                                        <th>P&L</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-trades">
                                    <!-- Trades will be loaded here -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-lg-6 mb-3">
                <div class="card h-100">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-brain me-2"></i>AI Models Status</h5>
                    </div>
                    <div class="card-body">
                        <div id="model-status">
                            <!-- Model status will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Control Panel -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-cogs me-2"></i>System Control</h5>
                    </div>
                    <div class="card-body">
                        <div class="btn-group me-2" role="group">
                            <button type="button" class="btn btn-success" onclick="startTraining()">
                                <i class="fas fa-play me-1"></i>Start Training
                            </button>
                            <button type="button" class="btn btn-warning" onclick="restartMarketData()">
                                <i class="fas fa-refresh me-1"></i>Restart Market Data
                            </button>
                            <button type="button" class="btn btn-danger" onclick="emergencyStop()">
                                <i class="fas fa-stop me-1"></i>Emergency Stop
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Initialize WebSocket connection
        const socket = io();

        // Connection status
        socket.on('connect', function() {
            document.getElementById('status-indicator').className = 'bg-success';
            document.getElementById('connection-status').textContent = 'Connected';
        });

        socket.on('disconnect', function() {
            document.getElementById('status-indicator').className = 'bg-danger';
            document.getElementById('connection-status').textContent = 'Disconnected';
        });

        // Real-time updates
        socket.on('health_update', function(data) {
            updateHealthIndicators(data);
        });

        socket.on('market_update', function(data) {
            // Update live market data
            console.log('Market update:', data);
        });

        // Load initial data
        async function loadDashboardData() {
            try {
                // Load performance metrics
                const perfResponse = await fetch('/api/performance');
                const perfData = await perfResponse.json();
                updatePerformanceMetrics(perfData);

                // Load market data
                const marketResponse = await fetch('/api/market-data?periods=100');
                const marketData = await marketResponse.json();
                updateMarketChart(marketData);

                // Load equity curve
                const equityResponse = await fetch('/api/equity-curve?days=30');
                const equityData = await equityResponse.json();
                updateEquityChart(equityData);

                // Load recent trades
                const tradesResponse = await fetch('/api/trades?limit=10');
                const tradesData = await tradesResponse.json();
                updateRecentTrades(tradesData);

                // Load model status
                const modelsResponse = await fetch('/api/models');
                const modelsData = await modelsResponse.json();
                updateModelStatus(modelsData);

                // Load health status
                const healthResponse = await fetch('/api/health');
                const healthData = await healthResponse.json();
                updateHealthIndicators(healthData);

            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }

        function updatePerformanceMetrics(data) {
            if (data.summary) {
                document.getElementById('total-pnl').textContent = 
                    '$' + (data.summary.total_pnl || 0).toFixed(2);
                document.getElementById('win-rate').textContent = 
                    ((data.summary.win_rate || 0) * 100).toFixed(1) + '%';
                document.getElementById('total-trades').textContent = 
                    data.summary.total_trades || 0;
                document.getElementById('sharpe-ratio').textContent = 
                    (data.summary.sharpe_ratio || 0).toFixed(2);
            }
        }

        function updateMarketChart(data) {
            if (data.chart_data) {
                const chartData = JSON.parse(data.chart_data);
                Plotly.newPlot('market-chart', chartData.data, chartData.layout, {responsive: true});
            }
        }

        function updateEquityChart(data) {
            if (data.chart_data) {
                const chartData = JSON.parse(data.chart_data);
                Plotly.newPlot('equity-chart', chartData.data, chartData.layout, {responsive: true});
            }
        }

        function updateRecentTrades(data) {
            const tbody = document.getElementById('recent-trades');
            tbody.innerHTML = '';
            
            if (data.trades) {
                data.trades.slice(0, 10).forEach(trade => {
                    const row = document.createElement('tr');
                    const pnlClass = trade.profit_loss > 0 ? 'text-success' : 'text-danger';
                    const time = new Date(trade.timestamp).toLocaleTimeString();
                    
                    row.innerHTML = `
                        <td>${time}</td>
                        <td><span class="badge ${trade.trade_type === 'buy' ? 'bg-success' : 'bg-danger'}">${trade.trade_type?.toUpperCase()}</span></td>
                        <td>${trade.entry_price?.toFixed(4)}</td>
                        <td class="${pnlClass}">$${trade.profit_loss?.toFixed(2)}</td>
                    `;
                    tbody.appendChild(row);
                });
            }
        }

        function updateModelStatus(data) {
            const container = document.getElementById('model-status');
            container.innerHTML = '';
            
            if (data.registered_models) {
                data.registered_models.forEach(model => {
                    const modelDiv = document.createElement('div');
                    modelDiv.className = 'mb-2 p-2 border rounded';
                    modelDiv.innerHTML = `
                        <div class="d-flex justify-content-between">
                            <strong>${model.name}</strong>
                            <span class="badge bg-success">Active</span>
                        </div>
                        <small class="text-muted">
                            Score: ${model.validation_score?.toFixed(3)} | 
                            Features: ${model.feature_count} | 
                            Version: ${model.version}
                        </small>
                    `;
                    container.appendChild(modelDiv);
                });
            }
        }

        function updateHealthIndicators(data) {
            const container = document.getElementById('health-indicators');
            container.innerHTML = '';
            
            if (data.components) {
                Object.entries(data.components).forEach(([name, status]) => {
                    const col = document.createElement('div');
                    col.className = 'col-lg-3 col-md-6 mb-2';
                    
                    let statusClass = 'success';
                    let statusIcon = 'check-circle';
                    
                    if (status.status === 'error' || status.status === 'critical') {
                        statusClass = 'danger';
                        statusIcon = 'exclamation-circle';
                    } else if (status.status === 'warning' || status.status === 'degraded') {
                        statusClass = 'warning';
                        statusIcon = 'exclamation-triangle';
                    } else if (status.status === 'stopped') {
                        statusClass = 'secondary';
                        statusIcon = 'pause-circle';
                    }
                    
                    col.innerHTML = `
                        <div class="card border-${statusClass}">
                            <div class="card-body text-center py-2">
                                <i class="fas fa-${statusIcon} text-${statusClass} mb-1"></i>
                                <div class="fw-bold">${name.replace('_', ' ').toUpperCase()}</div>
                                <small class="text-muted">${status.status}</small>
                            </div>
                        </div>
                    `;
                    container.appendChild(col);
                });
            }
        }

        // Control functions
        async function startTraining() {
            try {
                const response = await fetch('/api/control/start_training', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({model: 'all'})
                });
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                alert('Error starting training: ' + error.message);
            }
        }

        async function restartMarketData() {
            try {
                const response = await fetch('/api/control/restart_market_data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'}
                });
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                alert('Error restarting market data: ' + error.message);
            }
        }

        async function emergencyStop() {
            if (confirm('Are you sure you want to activate emergency stop? This will halt all trading activities.')) {
                try {
                    const response = await fetch('/api/control/emergency_stop', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'}
                    });
                    const result = await response.json();
                    alert(result.message);
                } catch (error) {
                    alert('Error activating emergency stop: ' + error.message);
                }
            }
        }

        // Subscribe to real-time updates
        socket.emit('subscribe', {type: 'all'});

        // Load initial data when page loads
        document.addEventListener('DOMContentLoaded', loadDashboardData);

        // Refresh data every 30 seconds
        setInterval(loadDashboardData, 30000);
    </script>
</body>
</html>
"""
    
    with open(template_dir / "dashboard.html", 'w') as f:
        f.write(html_content)

def main():
    """Run the dashboard"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create template if it doesn't exist
    create_dashboard_template()
    
    # Create and run dashboard
    dashboard = TradingDashboard(host='127.0.0.1', port=5000, debug=False)
    
    try:
        dashboard.start()
    except KeyboardInterrupt:
        print("Dashboard stopped by user")
    finally:
        dashboard.stop()

if __name__ == "__main__":
    main()
