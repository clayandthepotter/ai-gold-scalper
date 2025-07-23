#!/usr/bin/env python3
"""
AI Gold Scalper - Performance Dashboard
Phase 2.2: Performance Dashboard Creation

Real-time web-based dashboard for monitoring AI Gold Scalper performance,
risk metrics, and system health with integrated data from Phase 1 logging.

Key Features:
- Real-time performance metrics
- Historical performance charts
- Risk monitoring and alerts
- Signal source comparison
- Trade analytics and insights
- System health monitoring

Version: 1.0.0
Created: 2025-01-22
"""

import os
import sys
import json
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import threading
import time
from flask import Flask, render_template_string, jsonify, request, send_from_directory
import plotly
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots

# Add the root directory to the path
sys.path.append('.')

try:
    from scripts.monitoring.enhanced_trade_logger import EnhancedTradeLogger
    from scripts.monitoring.trade_postmortem_analyzer import TradePostmortemAnalyzer
    from scripts.analysis.risk_parameter_optimizer import RiskParameterOptimizer
except ImportError:
    print("Error: Cannot import required modules. Make sure the files exist.")
    sys.exit(1)

class PerformanceDashboard:
    """Real-time performance dashboard for AI Gold Scalper"""
    
    def __init__(self, 
                 port: int = 5555,
                 logger_db_path: str = "scripts/monitoring/trade_logs.db"):
        
        self.port = port
        self.trade_logger = EnhancedTradeLogger(logger_db_path)
        self.postmortem_analyzer = TradePostmortemAnalyzer()
        self.risk_optimizer = RiskParameterOptimizer()
        
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'ai_gold_scalper_dashboard'
        
        self.setup_logging()
        self.setup_routes()
        
        # Cache for performance data
        self.performance_cache = {}
        self.cache_timestamp = datetime.min
        self.cache_duration = 30  # seconds
        
        # Background data refresh thread
        self.data_refresh_thread = None
        self.stop_refresh = threading.Event()
        
    def setup_logging(self):
        """Setup logging for dashboard"""
        self.logger = logging.getLogger(f"{__name__}.PerformanceDashboard")
        self.logger.setLevel(logging.INFO)
        
        log_file = "scripts/monitoring/dashboard.log"
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        self.logger.info("Performance Dashboard initialized")
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page"""
            return render_template_string(self.get_dashboard_html())
        
        @self.app.route('/api/performance')
        def api_performance():
            """API endpoint for performance data"""
            try:
                days_back = request.args.get('days', 7, type=int)
                performance_data = self.get_performance_data(days_back)
                return jsonify(performance_data)
            except Exception as e:
                self.logger.error(f"Error in performance API: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/charts')
        def api_charts():
            """API endpoint for chart data"""
            try:
                chart_type = request.args.get('type', 'performance')
                days_back = request.args.get('days', 7, type=int)
                chart_data = self.generate_chart_data(chart_type, days_back)
                return jsonify(chart_data)
            except Exception as e:
                self.logger.error(f"Error in charts API: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/health')
        def api_health():
            """API endpoint for system health"""
            try:
                health_data = self.get_system_health()
                return jsonify(health_data)
            except Exception as e:
                self.logger.error(f"Error in health API: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/recent_trades')
        def api_recent_trades():
            """API endpoint for recent trades"""
            try:
                limit = request.args.get('limit', 20, type=int)
                trades_data = self.get_recent_trades_data(limit)
                return jsonify(trades_data)
            except Exception as e:
                self.logger.error(f"Error in recent trades API: {e}")
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/api/risk_analysis')
        def api_risk_analysis():
            """API endpoint for risk analysis"""
            try:
                risk_data = self.get_risk_analysis()
                return jsonify(risk_data)
            except Exception as e:
                self.logger.error(f"Error in risk analysis API: {e}")
                return jsonify({"error": str(e)}), 500
    
    def get_performance_data(self, days_back: int = 7) -> Dict:
        """Get comprehensive performance data"""
        try:
            # Check cache
            cache_key = f"performance_{days_back}"
            if (cache_key in self.performance_cache and 
                (datetime.now() - self.cache_timestamp).seconds < self.cache_duration):
                return self.performance_cache[cache_key]
            
            # Get signal performance
            signal_performance = self.trade_logger.get_signal_performance(days_back)
            
            # Get recent trades
            recent_trades = self.trade_logger.get_recent_trades(100)
            
            # Calculate additional metrics
            performance_data = {
                'period_days': days_back,
                'timestamp': datetime.now().isoformat(),
                'signal_performance': signal_performance,
                'daily_stats': self._calculate_daily_stats(recent_trades, days_back),
                'source_comparison': self._analyze_signal_sources(recent_trades),
                'risk_metrics': self._calculate_risk_metrics(recent_trades),
                'trend_analysis': self._analyze_performance_trends(recent_trades, days_back)
            }
            
            # Update cache
            self.performance_cache[cache_key] = performance_data
            self.cache_timestamp = datetime.now()
            
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Error getting performance data: {e}")
            return {"error": str(e)}
    
    def get_system_health(self) -> Dict:
        """Get system health metrics"""
        try:
            # Get database stats
            db_stats = self.trade_logger._get_database_stats()
            
            # Get recent performance
            recent_performance = self.get_performance_data(1)  # Last 24 hours
            
            # System health indicators
            health_score = 100
            alerts = []
            
            # Check win rate
            if recent_performance.get('signal_performance', {}).get('summary', {}).get('overall_win_rate', 0) < 50:
                health_score -= 20
                alerts.append("⚠️ Win rate below 50% in last 24 hours")
            
            # Check data freshness
            latest_signal = db_stats.get('data_range', {}).get('latest_signal')
            if latest_signal:
                try:
                    latest_time = datetime.fromisoformat(latest_signal.replace('Z', '+00:00'))
                    hours_since = (datetime.now() - latest_time).total_seconds() / 3600
                    if hours_since > 6:
                        health_score -= 15
                        alerts.append(f"⚠️ No new signals in {hours_since:.1f} hours")
                except:
                    pass
            
            # Check for errors in logs
            log_files = [
                "scripts/monitoring/trade_logs_activity.log",
                "scripts/monitoring/integration.log",
                "scripts/monitoring/postmortem_analysis.log"
            ]
            
            error_count = 0
            for log_file in log_files:
                if os.path.exists(log_file):
                    try:
                        with open(log_file, 'r') as f:
                            content = f.read()
                            error_count += content.lower().count('error')
                    except:
                        pass
            
            if error_count > 10:
                health_score -= 10
                alerts.append(f"⚠️ {error_count} errors detected in logs")
            
            # Overall health status
            if health_score >= 90:
                status = "EXCELLENT"
                color = "#28a745"
            elif health_score >= 70:
                status = "GOOD"
                color = "#ffc107"
            elif health_score >= 50:
                status = "WARNING"
                color = "#fd7e14"
            else:
                status = "CRITICAL"
                color = "#dc3545"
            
            return {
                'health_score': health_score,
                'status': status,
                'status_color': color,
                'alerts': alerts,
                'database_stats': db_stats,
                'system_uptime': self._get_system_uptime(),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system health: {e}")
            return {
                'health_score': 0,
                'status': 'ERROR',
                'status_color': '#dc3545',
                'alerts': [f"❌ System health check failed: {str(e)}"],
                'last_updated': datetime.now().isoformat()
            }
    
    def get_recent_trades_data(self, limit: int = 20) -> Dict:
        """Get recent trades with enhanced data"""
        try:
            recent_trades = self.trade_logger.get_recent_trades(limit)
            
            # Enhance trades with additional info
            enhanced_trades = []
            for trade in recent_trades:
                enhanced = trade.copy()
                
                # Format timestamp
                if enhanced.get('signal_time'):
                    try:
                        dt = datetime.fromisoformat(enhanced['signal_time'].replace('Z', '+00:00'))
                        enhanced['formatted_time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        enhanced['time_ago'] = self._format_time_ago(dt)
                    except:
                        enhanced['formatted_time'] = enhanced.get('signal_time', '')
                        enhanced['time_ago'] = 'Unknown'
                
                # Format P&L
                pnl_pips = enhanced.get('pnl_pips', 0)
                if pnl_pips > 0:
                    enhanced['pnl_display'] = f"+{pnl_pips:.1f} pips"
                    enhanced['pnl_class'] = "profit"
                elif pnl_pips < 0:
                    enhanced['pnl_display'] = f"{pnl_pips:.1f} pips"
                    enhanced['pnl_class'] = "loss"
                else:
                    enhanced['pnl_display'] = "0.0 pips"
                    enhanced['pnl_class'] = "neutral"
                
                # Confidence indicator
                confidence = enhanced.get('confidence', 0)
                if confidence > 80:
                    enhanced['confidence_class'] = "high"
                elif confidence > 65:
                    enhanced['confidence_class'] = "medium"
                else:
                    enhanced['confidence_class'] = "low"
                
                enhanced_trades.append(enhanced)
            
            return {
                'trades': enhanced_trades,
                'total_count': len(enhanced_trades),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting recent trades: {e}")
            return {"error": str(e)}
    
    def get_risk_analysis(self) -> Dict:
        """Get risk analysis data"""
        try:
            # Get optimization results if available
            risk_files = [f for f in os.listdir("scripts/analysis/") if f.startswith("risk_optimization_")]
            
            if risk_files:
                # Get latest optimization file
                latest_file = max(risk_files, key=lambda x: os.path.getctime(f"scripts/analysis/{x}"))
                
                with open(f"scripts/analysis/{latest_file}", 'r') as f:
                    optimization_data = json.load(f)
                
                # Extract key risk parameters
                optimized_params = optimization_data.get('optimized_parameters', {})
                improvement_metrics = optimization_data.get('improvement_metrics', {})
                
                risk_analysis = {
                    'current_risk_per_trade': optimized_params.get('max_risk_per_trade', 0.5),
                    'confidence_threshold': optimized_params.get('confidence_threshold', 75.0),
                    'max_daily_risk': optimized_params.get('max_daily_risk', 2.0),
                    'max_consecutive_losses': optimized_params.get('max_consecutive_losses', 3),
                    'improvement_metrics': improvement_metrics,
                    'optimization_confidence': optimization_data.get('confidence_score', 0),
                    'last_optimized': latest_file.split('_')[-1].replace('.json', '')
                }
            else:
                # Default risk analysis
                risk_analysis = {
                    'current_risk_per_trade': 0.5,
                    'confidence_threshold': 75.0,
                    'max_daily_risk': 2.0,
                    'max_consecutive_losses': 3,
                    'improvement_metrics': {},
                    'optimization_confidence': 0,
                    'last_optimized': 'Not available'
                }
            
            # Add current risk status
            recent_performance = self.get_performance_data(1)
            signal_perf = recent_performance.get('signal_performance', {})
            summary = signal_perf.get('summary', {})
            
            risk_analysis['current_win_rate'] = summary.get('overall_win_rate', 0)
            risk_analysis['daily_pnl'] = summary.get('total_pnl_usd', 0)
            risk_analysis['risk_status'] = self._assess_current_risk_status(risk_analysis)
            
            return risk_analysis
            
        except Exception as e:
            self.logger.error(f"Error getting risk analysis: {e}")
            return {"error": str(e)}
    
    def generate_chart_data(self, chart_type: str, days_back: int = 7) -> Dict:
        """Generate chart data for different chart types"""
        try:
            if chart_type == 'performance':
                return self._create_performance_chart(days_back)
            elif chart_type == 'signals':
                return self._create_signals_chart(days_back)
            elif chart_type == 'risk':
                return self._create_risk_chart(days_back)
            elif chart_type == 'sources':
                return self._create_sources_comparison_chart(days_back)
            else:
                return {"error": "Unknown chart type"}
            
        except Exception as e:
            self.logger.error(f"Error generating chart data: {e}")
            return {"error": str(e)}
    
    def _create_performance_chart(self, days_back: int) -> Dict:
        """Create performance chart data"""
        try:
            recent_trades = self.trade_logger.get_recent_trades(1000)
            
            # Filter trades by date range
            cutoff_date = datetime.now() - timedelta(days=days_back)
            filtered_trades = []
            
            for trade in recent_trades:
                if trade.get('signal_time'):
                    try:
                        trade_time = datetime.fromisoformat(trade['signal_time'].replace('Z', '+00:00'))
                        if trade_time >= cutoff_date:
                            filtered_trades.append(trade)
                    except:
                        continue
            
            if not filtered_trades:
                return {"error": "No trades in date range"}
            
            # Create cumulative P&L chart
            df = pd.DataFrame(filtered_trades)
            df['trade_time'] = pd.to_datetime(df['signal_time'].str.replace('Z', '+00:00'))
            df = df.sort_values('trade_time')
            df['cumulative_pnl'] = df['pnl_pips'].cumsum()
            
            # Create Plotly chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['trade_time'],
                y=df['cumulative_pnl'],
                mode='lines+markers',
                name='Cumulative P&L (pips)',
                line=dict(color='#007bff', width=2),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                title='Cumulative P&L Performance',
                xaxis_title='Time',
                yaxis_title='Cumulative P&L (pips)',
                height=400,
                template='plotly_white'
            )
            
            return {
                "chart": fig.to_json(),
                "chart_type": "performance",
                "data_points": len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating performance chart: {e}")
            return {"error": str(e)}
    
    def _create_signals_chart(self, days_back: int) -> Dict:
        """Create signals distribution chart"""
        try:
            recent_trades = self.trade_logger.get_recent_trades(200)
            
            # Count signal types
            signal_counts = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            
            for trade in recent_trades:
                signal_type = trade.get('signal_type', 'UNKNOWN')
                if signal_type in signal_counts:
                    signal_counts[signal_type] += 1
            
            # Create pie chart
            fig = go.Figure(data=[go.Pie(
                labels=list(signal_counts.keys()),
                values=list(signal_counts.values()),
                hole=0.4
            )])
            
            fig.update_layout(
                title='Signal Distribution',
                height=300,
                template='plotly_white'
            )
            
            return {
                "chart": fig.to_json(),
                "chart_type": "signals",
                "signal_counts": signal_counts
            }
            
        except Exception as e:
            self.logger.error(f"Error creating signals chart: {e}")
            return {"error": str(e)}
    
    def _create_sources_comparison_chart(self, days_back: int) -> Dict:
        """Create signal sources comparison chart"""
        try:
            performance_data = self.get_performance_data(days_back)
            source_performance = performance_data.get('signal_performance', {}).get('by_source', [])
            
            if not source_performance:
                return {"error": "No source performance data"}
            
            sources = [s['source'] for s in source_performance]
            win_rates = [s['win_rate'] for s in source_performance]
            trade_counts = [s['trades'] for s in source_performance]
            
            # Create bar chart
            fig = go.Figure(data=[
                go.Bar(name='Win Rate (%)', x=sources, y=win_rates, yaxis='y', offsetgroup=1),
                go.Bar(name='Trade Count', x=sources, y=trade_counts, yaxis='y2', offsetgroup=2)
            ])
            
            fig.update_layout(
                title='Signal Sources Performance Comparison',
                xaxis=dict(title='Signal Source'),
                yaxis=dict(title='Win Rate (%)', side='left'),
                yaxis2=dict(title='Trade Count', side='right', overlaying='y'),
                barmode='group',
                height=400,
                template='plotly_white'
            )
            
            return {
                "chart": fig.to_json(),
                "chart_type": "sources",
                "source_data": source_performance
            }
            
        except Exception as e:
            self.logger.error(f"Error creating sources chart: {e}")
            return {"error": str(e)}
    
    def _calculate_daily_stats(self, trades: List[Dict], days_back: int) -> Dict:
        """Calculate daily statistics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_back)
            daily_stats = {}
            
            for trade in trades:
                if trade.get('signal_time'):
                    try:
                        trade_time = datetime.fromisoformat(trade['signal_time'].replace('Z', '+00:00'))
                        if trade_time >= cutoff_date:
                            date_str = trade_time.strftime('%Y-%m-%d')
                            
                            if date_str not in daily_stats:
                                daily_stats[date_str] = {
                                    'trades': 0,
                                    'wins': 0,
                                    'losses': 0,
                                    'pnl_pips': 0,
                                    'pnl_usd': 0
                                }
                            
                            daily_stats[date_str]['trades'] += 1
                            pnl_pips = trade.get('pnl_pips', 0)
                            pnl_usd = trade.get('pnl_usd', 0)
                            
                            if pnl_pips > 0:
                                daily_stats[date_str]['wins'] += 1
                            elif pnl_pips < 0:
                                daily_stats[date_str]['losses'] += 1
                            
                            daily_stats[date_str]['pnl_pips'] += pnl_pips
                            daily_stats[date_str]['pnl_usd'] += pnl_usd
                    except:
                        continue
            
            # Calculate win rates
            for date, stats in daily_stats.items():
                total_trades = stats['trades']
                if total_trades > 0:
                    stats['win_rate'] = (stats['wins'] / total_trades) * 100
                else:
                    stats['win_rate'] = 0
            
            return daily_stats
            
        except Exception as e:
            self.logger.error(f"Error calculating daily stats: {e}")
            return {}
    
    def _analyze_signal_sources(self, trades: List[Dict]) -> Dict:
        """Analyze signal sources performance"""
        try:
            source_stats = {}
            
            for trade in trades:
                source = trade.get('source', 'Unknown')
                
                if source not in source_stats:
                    source_stats[source] = {
                        'total': 0,
                        'wins': 0,
                        'losses': 0,
                        'total_pnl': 0,
                        'avg_confidence': 0,
                        'confidence_sum': 0
                    }
                
                source_stats[source]['total'] += 1
                pnl_pips = trade.get('pnl_pips', 0)
                confidence = trade.get('confidence', 0)
                
                if pnl_pips > 0:
                    source_stats[source]['wins'] += 1
                elif pnl_pips < 0:
                    source_stats[source]['losses'] += 1
                
                source_stats[source]['total_pnl'] += pnl_pips
                source_stats[source]['confidence_sum'] += confidence
            
            # Calculate derived metrics
            for source, stats in source_stats.items():
                if stats['total'] > 0:
                    stats['win_rate'] = (stats['wins'] / stats['total']) * 100
                    stats['avg_confidence'] = stats['confidence_sum'] / stats['total']
                    stats['avg_pnl_per_trade'] = stats['total_pnl'] / stats['total']
                else:
                    stats['win_rate'] = 0
                    stats['avg_confidence'] = 0
                    stats['avg_pnl_per_trade'] = 0
            
            return source_stats
            
        except Exception as e:
            self.logger.error(f"Error analyzing signal sources: {e}")
            return {}
    
    def _calculate_risk_metrics(self, trades: List[Dict]) -> Dict:
        """Calculate risk metrics"""
        try:
            if not trades:
                return {}
            
            df = pd.DataFrame(trades)
            
            # Basic risk metrics
            risk_metrics = {
                'total_trades': len(df),
                'max_loss_pips': df['pnl_pips'].min() if len(df) > 0 else 0,
                'max_win_pips': df['pnl_pips'].max() if len(df) > 0 else 0,
                'avg_loss_pips': df[df['pnl_pips'] < 0]['pnl_pips'].mean() if len(df[df['pnl_pips'] < 0]) > 0 else 0,
                'avg_win_pips': df[df['pnl_pips'] > 0]['pnl_pips'].mean() if len(df[df['pnl_pips'] > 0]) > 0 else 0
            }
            
            # Drawdown calculation
            df['cumulative_pnl'] = df['pnl_pips'].cumsum()
            df['running_max'] = df['cumulative_pnl'].cummax()
            df['drawdown'] = df['cumulative_pnl'] - df['running_max']
            
            risk_metrics['max_drawdown_pips'] = abs(df['drawdown'].min()) if len(df) > 0 else 0
            
            # Risk-reward ratio
            if risk_metrics['avg_loss_pips'] != 0:
                risk_metrics['avg_risk_reward_ratio'] = abs(risk_metrics['avg_win_pips'] / risk_metrics['avg_loss_pips'])
            else:
                risk_metrics['avg_risk_reward_ratio'] = 0
            
            return risk_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating risk metrics: {e}")
            return {}
    
    def _analyze_performance_trends(self, trades: List[Dict], days_back: int) -> Dict:
        """Analyze performance trends"""
        try:
            if len(trades) < 10:
                return {"trend": "insufficient_data"}
            
            # Sort trades by time and calculate rolling performance
            df = pd.DataFrame(trades)
            df['trade_time'] = pd.to_datetime(df['signal_time'].str.replace('Z', '+00:00'), errors='coerce')
            df = df.dropna(subset=['trade_time']).sort_values('trade_time')
            
            # Calculate rolling win rate (10 trade window)
            window_size = min(10, len(df) // 2)
            df['rolling_wins'] = df['pnl_pips'].apply(lambda x: 1 if x > 0 else 0).rolling(window=window_size).mean()
            
            # Determine trend
            if len(df) >= window_size * 2:
                early_performance = df.iloc[:window_size]['rolling_wins'].mean()
                late_performance = df.iloc[-window_size:]['rolling_wins'].mean()
                
                if late_performance > early_performance + 0.1:
                    trend = "improving"
                elif late_performance < early_performance - 0.1:
                    trend = "declining"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            return {
                "trend": trend,
                "early_win_rate": early_performance * 100 if len(df) >= window_size * 2 else 0,
                "recent_win_rate": late_performance * 100 if len(df) >= window_size * 2 else 0,
                "data_points": len(df)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
            return {"trend": "error", "error": str(e)}
    
    def _format_time_ago(self, dt: datetime) -> str:
        """Format time ago string"""
        now = datetime.now()
        diff = now - dt.replace(tzinfo=None)
        
        if diff.total_seconds() < 60:
            return "Just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes}m ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            days = diff.days
            return f"{days}d ago"
    
    def _get_system_uptime(self) -> str:
        """Get system uptime info"""
        # Simplified uptime calculation based on oldest log entry
        try:
            db_stats = self.trade_logger._get_database_stats()
            earliest = db_stats.get('data_range', {}).get('earliest_signal')
            
            if earliest:
                start_time = datetime.fromisoformat(earliest.replace('Z', '+00:00'))
                uptime = datetime.now() - start_time.replace(tzinfo=None)
                
                days = uptime.days
                hours = uptime.seconds // 3600
                
                return f"{days} days, {hours} hours"
            else:
                return "Unknown"
        except:
            return "Unknown"
    
    def _assess_current_risk_status(self, risk_analysis: Dict) -> Dict:
        """Assess current risk status"""
        try:
            win_rate = risk_analysis.get('current_win_rate', 0)
            daily_pnl = risk_analysis.get('daily_pnl', 0)
            max_daily_risk = risk_analysis.get('max_daily_risk', 2.0)
            
            # Risk level assessment
            if win_rate > 65 and daily_pnl > -max_daily_risk:
                risk_level = "LOW"
                risk_color = "#28a745"
                risk_message = "System operating within safe parameters"
            elif win_rate > 50 and daily_pnl > -max_daily_risk * 1.5:
                risk_level = "MEDIUM"
                risk_color = "#ffc107"
                risk_message = "Moderate risk - monitor closely"
            else:
                risk_level = "HIGH"
                risk_color = "#dc3545"
                risk_message = "High risk detected - review parameters"
            
            return {
                "level": risk_level,
                "color": risk_color,
                "message": risk_message
            }
            
        except Exception as e:
            return {
                "level": "UNKNOWN",
                "color": "#6c757d",
                "message": f"Risk assessment error: {str(e)}"
            }
    
    def get_dashboard_html(self) -> str:
        """Return the dashboard HTML template"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Gold Scalper - Performance Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        .metric-card { min-height: 120px; }
        .profit { color: #28a745; }
        .loss { color: #dc3545; }
        .neutral { color: #6c757d; }
        .confidence.high { color: #28a745; }
        .confidence.medium { color: #ffc107; }
        .confidence.low { color: #dc3545; }
        .status-indicator { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
        .chart-container { height: 400px; }
        .table-sm td { padding: 0.25rem; }
        .refresh-btn { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
    </style>
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="#"><i class="fas fa-chart-line me-2"></i>AI Gold Scalper Dashboard</a>
            <span class="navbar-text">
                <span id="last-update">Loading...</span>
            </span>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <!-- System Health Row -->
        <div class="row mb-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="fas fa-heartbeat me-2"></i>System Health</h5>
                        <span id="health-status" class="badge">Loading...</span>
                    </div>
                    <div class="card-body">
                        <div class="row" id="health-content">
                            <div class="col-md-3">
                                <div class="text-center">
                                    <div id="health-score" class="h2 mb-1">--</div>
                                    <small class="text-muted">Health Score</small>
                                </div>
                            </div>
                            <div class="col-md-9">
                                <div id="health-alerts">Loading...</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Performance Metrics Row -->
        <div class="row mb-4">
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <i class="fas fa-percentage fa-2x text-primary mb-2"></i>
                        <div id="win-rate" class="h4 mb-1">--%</div>
                        <small class="text-muted">Win Rate</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <i class="fas fa-coins fa-2x text-success mb-2"></i>
                        <div id="total-pnl" class="h4 mb-1">-- pips</div>
                        <small class="text-muted">Total P&L</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <i class="fas fa-signal fa-2x text-info mb-2"></i>
                        <div id="total-signals" class="h4 mb-1">--</div>
                        <small class="text-muted">Total Signals</small>
                    </div>
                </div>
            </div>
            <div class="col-lg-3 col-md-6 mb-3">
                <div class="card metric-card">
                    <div class="card-body text-center">
                        <i class="fas fa-shield-alt fa-2x text-warning mb-2"></i>
                        <div id="risk-level" class="h4 mb-1">--</div>
                        <small class="text-muted">Risk Level</small>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts Row -->
        <div class="row mb-4">
            <div class="col-lg-8 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-chart-area me-2"></i>Performance Chart</h5>
                    </div>
                    <div class="card-body">
                        <div id="performance-chart" class="chart-container"></div>
                    </div>
                </div>
            </div>
            <div class="col-lg-4 mb-3">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-chart-pie me-2"></i>Signal Distribution</h5>
                    </div>
                    <div class="card-body">
                        <div id="signals-chart" class="chart-container"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Trades Row -->
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5 class="mb-0"><i class="fas fa-history me-2"></i>Recent Trades</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-hover">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Signal</th>
                                        <th>Source</th>
                                        <th>Confidence</th>
                                        <th>P&L</th>
                                        <th>Outcome</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-trades-table">
                                    <tr><td colspan="6" class="text-center">Loading...</td></tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Refresh Button -->
    <button class="btn btn-primary btn-sm refresh-btn" onclick="refreshDashboard()">
        <i class="fas fa-sync-alt"></i>
    </button>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let refreshInterval;

        async function fetchData(endpoint) {
            try {
                const response = await fetch(endpoint);
                return await response.json();
            } catch (error) {
                console.error('Error fetching data:', error);
                return { error: error.message };
            }
        }

        async function updateSystemHealth() {
            const health = await fetchData('/api/health');
            
            if (!health.error) {
                document.getElementById('health-score').textContent = health.health_score || '--';
                document.getElementById('health-status').textContent = health.status || 'Unknown';
                document.getElementById('health-status').className = 'badge';
                document.getElementById('health-status').style.backgroundColor = health.status_color || '#6c757d';
                
                const alertsHtml = health.alerts.length > 0 
                    ? health.alerts.map(alert => `<div class="alert alert-warning alert-sm py-1 px-2 mb-1">${alert}</div>`).join('')
                    : '<div class="text-success"><i class="fas fa-check-circle me-1"></i>All systems operational</div>';
                
                document.getElementById('health-alerts').innerHTML = alertsHtml;
            }
        }

        async function updatePerformanceMetrics() {
            const performance = await fetchData('/api/performance');
            
            if (!performance.error && performance.signal_performance) {
                const summary = performance.signal_performance.summary || {};
                
                document.getElementById('win-rate').textContent = `${(summary.overall_win_rate || 0).toFixed(1)}%`;
                document.getElementById('total-pnl').textContent = `${(summary.total_pnl_usd || 0).toFixed(1)} USD`;
                document.getElementById('total-signals').textContent = summary.total_signals || 0;
            }

            const risk = await fetchData('/api/risk_analysis');
            if (!risk.error && risk.risk_status) {
                document.getElementById('risk-level').textContent = risk.risk_status.level || '--';
                document.getElementById('risk-level').style.color = risk.risk_status.color || '#6c757d';
            }
        }

        async function updateCharts() {
            // Performance Chart
            const perfChart = await fetchData('/api/charts?type=performance&days=7');
            if (!perfChart.error && perfChart.chart) {
                const chartData = JSON.parse(perfChart.chart);
                Plotly.newPlot('performance-chart', chartData.data, chartData.layout, {responsive: true});
            }

            // Signals Chart
            const signalsChart = await fetchData('/api/charts?type=signals');
            if (!signalsChart.error && signalsChart.chart) {
                const chartData = JSON.parse(signalsChart.chart);
                Plotly.newPlot('signals-chart', chartData.data, chartData.layout, {responsive: true});
            }
        }

        async function updateRecentTrades() {
            const trades = await fetchData('/api/recent_trades?limit=10');
            
            if (!trades.error && trades.trades) {
                const tbody = document.getElementById('recent-trades-table');
                
                if (trades.trades.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center">No recent trades</td></tr>';
                    return;
                }
                
                const rows = trades.trades.map(trade => `
                    <tr>
                        <td><small>${trade.time_ago || 'Unknown'}</small></td>
                        <td><span class="badge bg-${trade.signal_type === 'BUY' ? 'success' : trade.signal_type === 'SELL' ? 'danger' : 'secondary'}">${trade.signal_type || 'N/A'}</span></td>
                        <td><small>${trade.source || 'Unknown'}</small></td>
                        <td><span class="confidence ${trade.confidence_class || 'low'}">${(trade.confidence || 0).toFixed(0)}%</span></td>
                        <td><span class="${trade.pnl_class || 'neutral'}">${trade.pnl_display || '0.0 pips'}</span></td>
                        <td><span class="badge bg-${trade.outcome === 'WIN' ? 'success' : trade.outcome === 'LOSS' ? 'danger' : 'secondary'}">${trade.outcome || 'N/A'}</span></td>
                    </tr>
                `).join('');
                
                tbody.innerHTML = rows;
            }
        }

        async function refreshDashboard() {
            document.getElementById('last-update').textContent = 'Refreshing...';
            
            await Promise.all([
                updateSystemHealth(),
                updatePerformanceMetrics(),
                updateCharts(),
                updateRecentTrades()
            ]);
            
            document.getElementById('last-update').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        }

        // Initial load
        refreshDashboard();

        // Auto refresh every 30 seconds
        refreshInterval = setInterval(refreshDashboard, 30000);

        // Refresh charts when window is resized
        window.addEventListener('resize', () => {
            setTimeout(updateCharts, 100);
        });
    </script>
</body>
</html>
        """
    
    def start_background_refresh(self):
        """Start background data refresh thread"""
        if self.data_refresh_thread is None or not self.data_refresh_thread.is_alive():
            self.data_refresh_thread = threading.Thread(target=self._background_refresh_loop)
            self.data_refresh_thread.daemon = True
            self.data_refresh_thread.start()
            self.logger.info("Background data refresh started")
    
    def _background_refresh_loop(self):
        """Background loop to refresh data"""
        while not self.stop_refresh.is_set():
            try:
                # Refresh cache every 60 seconds
                self.performance_cache.clear()
                self.cache_timestamp = datetime.min
                time.sleep(60)
            except Exception as e:
                self.logger.error(f"Error in background refresh: {e}")
                time.sleep(60)
    
    def run(self, debug: bool = False):
        """Start the dashboard server"""
        try:
            self.logger.info(f"Starting Performance Dashboard on port {self.port}")
            
            # Start background refresh
            self.start_background_refresh()
            
            print("="*60)
            print("🚀 AI GOLD SCALPER - PERFORMANCE DASHBOARD STARTING")
            print("="*60)
            print(f"📊 Dashboard URL: http://localhost:{self.port}")
            print(f"🔄 Auto-refresh enabled (30 seconds)")
            print(f"📈 Real-time performance monitoring active")
            print("="*60)
            
            # Run Flask app
            self.app.run(host='0.0.0.0', port=self.port, debug=debug, threaded=True)
            
        except Exception as e:
            self.logger.error(f"Error starting dashboard: {e}")
            print(f"❌ Failed to start dashboard: {e}")
        finally:
            self.stop_refresh.set()

def main():
    """Main function for testing dashboard"""
    print("="*70)
    print("AI GOLD SCALPER - PERFORMANCE DASHBOARD")
    print("Phase 2.2: Performance Dashboard Creation")
    print("="*70)
    print()
    
    # Create dashboard instance
    dashboard = PerformanceDashboard(port=5555)
    
    try:
        # Start the dashboard
        dashboard.run(debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"\n❌ Dashboard error: {e}")

if __name__ == "__main__":
    main()
