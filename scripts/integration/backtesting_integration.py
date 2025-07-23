#!/usr/bin/env python3
"""
AI Gold Scalper - Backtesting Integration

Connects the comprehensive backtesting system with existing AI Gold Scalper components
including Phase 4 intelligence, ensemble models, and market regime detection.

This module provides seamless integration between:
- Backtesting framework
- Phase 4 AI controller
- Ensemble model system
- Market regime detector
- Risk parameter optimizer
- Performance dashboard
"""
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

class BacktestingIntegration:
    """Integration layer between backtesting and AI Gold Scalper systems"""
    
    def __init__(self, config_path: str = "config/backtesting_config.json"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.setup_logging()
        
        # Initialize components
        self.backtesting_system = None
        self.phase4_controller = None
        self.ensemble_system = None
        self.regime_detector = None
        
        self.logger.info("Backtesting Integration initialized")
    
    def load_config(self) -> Dict:
        """Load backtesting integration configuration"""
        default_config = {
            "backtesting": {
                "default_start_date": "2023-01-01",
                "default_end_date": "2023-12-31",
                "initial_balance": 10000,
                "position_size_value": 0.02,
                "commission": 0.0001,
                "slippage": 0.0001,
                "max_positions": 5,
                "confidence_threshold": 0.6
            },
            "ai_integration": {
                "use_phase4_controller": True,
                "use_ensemble_models": True,
                "use_regime_detection": True,
                "model_validation_enabled": True,
                "walk_forward_analysis": True
            },
            "performance_analysis": {
                "benchmark_symbol": "SPY",
                "risk_free_rate": 0.02,
                "calculate_advanced_metrics": True,
                "generate_reports": True,
                "save_results": True
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Merge with defaults
                for section, values in user_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                
                return default_config
                
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return default_config
        else:
            # Create default config file
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def setup_logging(self):
        """Setup logging for backtesting integration"""
        log_path = Path("logs/backtesting")
        log_path.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path / f"integration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('BacktestingIntegration')
    
    def initialize_components(self):
        """Initialize all AI Gold Scalper components for backtesting"""
        
        try:
            # Import backtesting system
            from scripts.backtesting.comprehensive_backtester import (
                ComprehensiveBacktester, 
                BacktestConfig
            )
            
            # Create backtesting configuration
            bt_config = BacktestConfig(
                start_date=self.config['backtesting']['default_start_date'],
                end_date=self.config['backtesting']['default_end_date'],
                initial_balance=self.config['backtesting']['initial_balance'],
                position_size_value=self.config['backtesting']['position_size_value'],
                commission=self.config['backtesting']['commission'],
                slippage=self.config['backtesting']['slippage'],
                max_positions=self.config['backtesting']['max_positions']
            )
            
            self.backtesting_system = ComprehensiveBacktester(bt_config)
            self.logger.info("✅ Backtesting system initialized")
            
        except ImportError as e:
            self.logger.error(f"Failed to import backtesting system: {e}")
            return False
        
        # Initialize AI components if requested
        if self.config['ai_integration']['use_phase4_controller']:
            try:
                from scripts.integration.phase4_integration import Phase4Controller
                self.phase4_controller = Phase4Controller()
                self.logger.info("✅ Phase 4 controller initialized")
            except ImportError as e:
                self.logger.warning(f"Phase 4 controller not available: {e}")
        
        if self.config['ai_integration']['use_ensemble_models']:
            try:
                from scripts.ai.ensemble_models import EnsembleModelSystem
                self.ensemble_system = EnsembleModelSystem()
                self.logger.info("✅ Ensemble model system initialized")
            except ImportError as e:
                self.logger.warning(f"Ensemble models not available: {e}")
        
        if self.config['ai_integration']['use_regime_detection']:
            try:
                from scripts.ai.market_regime_detector import MarketRegimeDetector
                self.regime_detector = MarketRegimeDetector()
                self.logger.info("✅ Market regime detector initialized")
            except ImportError as e:
                self.logger.warning(f"Regime detector not available: {e}")
        
        return True
    
    def run_comprehensive_backtest(self, 
                                  symbol: str = "XAUUSD",
                                  start_date: str = None,
                                  end_date: str = None,
                                  strategy_type: str = "ai_integrated") -> Dict:
        """Run comprehensive backtest with full AI integration"""
        
        if not self.backtesting_system:
            if not self.initialize_components():
                return {'error': 'Failed to initialize components'}
        
        # Use provided dates or defaults
        start_date = start_date or self.config['backtesting']['default_start_date']
        end_date = end_date or self.config['backtesting']['default_end_date']
        
        self.logger.info(f"Starting comprehensive backtest: {symbol} ({start_date} to {end_date})")
        
        # Update backtesting config
        self.backtesting_system.config.start_date = start_date
        self.backtesting_system.config.end_date = end_date
        
        # Integrate AI models into backtesting system
        if self.phase4_controller:
            self.backtesting_system.ai_backtester.models['phase4'] = self.phase4_controller
        
        if self.ensemble_system:
            self.backtesting_system.ai_backtester.models['ensemble'] = self.ensemble_system
        
        if self.regime_detector:
            self.backtesting_system.ai_backtester.models['regime'] = self.regime_detector
        
        # Choose model based on availability
        model_name = 'mock'  # Default fallback
        if self.phase4_controller:
            model_name = 'phase4'
        elif self.ensemble_system:
            model_name = 'ensemble'
        
        # Run the backtest
        try:
            results = self.backtesting_system.run_backtest(
                symbol=symbol,
                strategy_type="ai_model",
                model_name=model_name
            )
            
            if 'error' in results:
                self.logger.error(f"Backtest failed: {results['error']}")
                return results
            
            # Enhance results with AI-specific metrics
            enhanced_results = self.enhance_results_with_ai_metrics(results)
            
            # Generate comprehensive report
            if self.config['performance_analysis']['generate_reports']:
                report = self.generate_comprehensive_report(enhanced_results)
                enhanced_results['comprehensive_report'] = report
            
            # Save results if configured
            if self.config['performance_analysis']['save_results']:
                self.save_backtest_results(enhanced_results, symbol, model_name)
            
            self.logger.info("Comprehensive backtest completed successfully")
            return enhanced_results
            
        except Exception as e:
            self.logger.error(f"Error during backtesting: {e}")
            return {'error': f'Backtesting failed: {e}'}
    
    def enhance_results_with_ai_metrics(self, results: Dict) -> Dict:
        """Enhance backtest results with AI-specific metrics"""
        
        enhanced = results.copy()
        
        # Add AI-specific analysis
        trades = results.get('trades_summary', [])
        
        if trades:
            # Analyze confidence distribution
            confidences = [t.get('confidence', 0.5) for t in trades if t.get('confidence')]
            if confidences:
                enhanced['ai_metrics'] = {
                    'avg_confidence': sum(confidences) / len(confidences),
                    'high_confidence_trades': len([c for c in confidences if c > 0.7]),
                    'low_confidence_trades': len([c for c in confidences if c < 0.5]),
                    'confidence_distribution': {
                        'high (>0.7)': len([c for c in confidences if c > 0.7]),
                        'medium (0.5-0.7)': len([c for c in confidences if 0.5 <= c <= 0.7]),
                        'low (<0.5)': len([c for c in confidences if c < 0.5])
                    }
                }
            
            # Analyze regime performance
            regimes = [t.get('regime', 'unknown') for t in trades]
            regime_analysis = {}
            
            for regime in set(regimes):
                regime_trades = [t for t in trades if t.get('regime') == regime]
                if regime_trades:
                    regime_pnls = [t.get('pnl', 0) for t in regime_trades if t.get('pnl')]
                    if regime_pnls:
                        regime_analysis[regime] = {
                            'total_trades': len(regime_trades),
                            'total_pnl': sum(regime_pnls),
                            'avg_pnl': sum(regime_pnls) / len(regime_pnls),
                            'win_rate': len([p for p in regime_pnls if p > 0]) / len(regime_pnls) * 100
                        }
            
            enhanced['regime_analysis'] = regime_analysis
            
            # Model performance analysis
            models = [t.get('model', 'unknown') for t in trades]
            model_analysis = {}
            
            for model in set(models):
                model_trades = [t for t in trades if t.get('model') == model]
                if model_trades:
                    model_pnls = [t.get('pnl', 0) for t in model_trades if t.get('pnl')]
                    if model_pnls:
                        model_analysis[model] = {
                            'total_trades': len(model_trades),
                            'total_pnl': sum(model_pnls),
                            'avg_pnl': sum(model_pnls) / len(model_pnls),
                            'win_rate': len([p for p in model_pnls if p > 0]) / len(model_pnls) * 100
                        }
            
            enhanced['model_analysis'] = model_analysis
        
        return enhanced
    
    def generate_comprehensive_report(self, results: Dict) -> Dict:
        """Generate comprehensive performance report"""
        
        report = {
            'report_generated': datetime.now().isoformat(),
            'executive_summary': {},
            'detailed_analysis': {},
            'recommendations': []
        }
        
        # Executive Summary
        backtest_info = results.get('backtest_info', {})
        summary = results.get('summary', {})
        
        report['executive_summary'] = {
            'strategy_performance': {
                'total_return': f"{backtest_info.get('total_return_pct', 0):.2f}%",
                'is_profitable': summary.get('profitable', False),
                'win_rate': f"{summary.get('win_rate', 0):.1f}%",
                'profit_factor': f"{summary.get('profit_factor', 0):.2f}",
                'sharpe_ratio': f"{summary.get('sharpe_ratio', 0):.2f}",
                'max_drawdown': f"{summary.get('max_drawdown', 0):.2f}%"
            }
        }
        
        # AI-specific insights
        if 'ai_metrics' in results:
            ai_metrics = results['ai_metrics']
            report['executive_summary']['ai_insights'] = {
                'average_confidence': f"{ai_metrics.get('avg_confidence', 0):.2f}",
                'high_confidence_percentage': f"{ai_metrics.get('high_confidence_trades', 0) / max(1, len(results.get('trades_summary', []))) * 100:.1f}%",
                'confidence_quality': 'High' if ai_metrics.get('avg_confidence', 0) > 0.7 else 'Medium' if ai_metrics.get('avg_confidence', 0) > 0.5 else 'Low'
            }
        
        # Detailed Analysis
        return_metrics = results.get('return_metrics', {})
        trade_metrics = results.get('trade_metrics', {})
        
        report['detailed_analysis'] = {
            'risk_adjusted_returns': {
                'sharpe_ratio': return_metrics.get('sharpe_ratio', 0),
                'sortino_ratio': return_metrics.get('sortino_ratio', 0),
                'calmar_ratio': return_metrics.get('calmar_ratio', 0)
            },
            'trade_analysis': {
                'total_trades': trade_metrics.get('total_trades', 0),
                'winning_trades': trade_metrics.get('winning_trades', 0),
                'losing_trades': trade_metrics.get('losing_trades', 0),
                'average_win': trade_metrics.get('avg_win', 0),
                'average_loss': trade_metrics.get('avg_loss', 0),
                'largest_win': trade_metrics.get('largest_win', 0),
                'largest_loss': trade_metrics.get('largest_loss', 0)
            }
        }
        
        # Generate Recommendations
        recommendations = []
        
        if summary.get('win_rate', 0) < 50:
            recommendations.append("Consider improving signal quality - win rate below 50%")
        
        if summary.get('profit_factor', 0) < 1.2:
            recommendations.append("Profit factor suggests room for improvement in risk/reward ratio")
        
        if summary.get('sharpe_ratio', 0) < 1.0:
            recommendations.append("Low Sharpe ratio indicates poor risk-adjusted returns")
        
        if results.get('ai_metrics', {}).get('avg_confidence', 0) < 0.6:
            recommendations.append("Low average confidence suggests AI model needs retraining")
        
        if len(recommendations) == 0:
            recommendations.append("Strategy shows good performance across all metrics")
        
        report['recommendations'] = recommendations
        
        return report
    
    def save_backtest_results(self, results: Dict, symbol: str, model_name: str):
        """Save backtest results with proper naming and organization"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backtest_{symbol}_{model_name}_{timestamp}.json"
        
        results_path = Path("logs/backtesting/results")
        results_path.mkdir(parents=True, exist_ok=True)
        
        # Convert datetime objects for JSON serialization
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            with open(results_path / filename, 'w') as f:
                json.dump(results, f, indent=2, default=json_serializer)
            
            self.logger.info(f"Results saved to: {results_path / filename}")
            
        except Exception as e:
            self.logger.error(f"Failed to save results: {e}")
    
    def run_strategy_comparison(self, 
                              symbol: str = "XAUUSD",
                              strategies: List[str] = None) -> Dict:
        """Run comparison between multiple strategies"""
        
        if not strategies:
            strategies = ["ai_model", "rsi_strategy", "buy_and_hold"]
        
        if not self.initialize_components():
            return {'error': 'Failed to initialize components'}
        
        self.logger.info(f"Running strategy comparison for {symbol}")
        
        comparison_results = {
            'comparison_date': datetime.now().isoformat(),
            'symbol': symbol,
            'strategies': {},
            'comparison_summary': {}
        }
        
        # Run each strategy
        for strategy in strategies:
            self.logger.info(f"Testing strategy: {strategy}")
            
            try:
                if strategy == "ai_model" and self.phase4_controller:
                    result = self.backtesting_system.run_backtest(
                        symbol=symbol,
                        strategy_type="ai_model",
                        model_name="phase4"
                    )
                else:
                    result = self.backtesting_system.run_backtest(
                        symbol=symbol,
                        strategy_type=strategy
                    )
                
                if 'error' not in result:
                    comparison_results['strategies'][strategy] = result
                    self.logger.info(f"✅ {strategy} completed successfully")
                else:
                    self.logger.error(f"❌ {strategy} failed: {result['error']}")
                    
            except Exception as e:
                self.logger.error(f"Error testing {strategy}: {e}")
        
        # Generate comparison summary
        if comparison_results['strategies']:
            comparison_results['comparison_summary'] = self.generate_comparison_summary(
                comparison_results['strategies']
            )
        
        # Save comparison results
        if self.config['performance_analysis']['save_results']:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"strategy_comparison_{symbol}_{timestamp}.json"
            
            results_path = Path("logs/backtesting/comparisons")
            results_path.mkdir(parents=True, exist_ok=True)
            
            try:
                def json_serializer(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                
                with open(results_path / filename, 'w') as f:
                    json.dump(comparison_results, f, indent=2, default=json_serializer)
                
                self.logger.info(f"Comparison saved to: {results_path / filename}")
                
            except Exception as e:
                self.logger.error(f"Failed to save comparison: {e}")
        
        return comparison_results
    
    def generate_comparison_summary(self, strategies: Dict) -> Dict:
        """Generate summary comparing multiple strategies"""
        
        summary = {
            'best_strategy': {},
            'performance_ranking': [],
            'key_metrics_comparison': {}
        }
        
        # Extract key metrics for each strategy
        strategy_metrics = {}
        
        for name, results in strategies.items():
            backtest_info = results.get('backtest_info', {})
            trade_summary = results.get('summary', {})
            
            strategy_metrics[name] = {
                'total_return': backtest_info.get('total_return_pct', 0),
                'win_rate': trade_summary.get('win_rate', 0),
                'profit_factor': trade_summary.get('profit_factor', 0),
                'sharpe_ratio': trade_summary.get('sharpe_ratio', 0),
                'max_drawdown': trade_summary.get('max_drawdown', 0),
                'total_trades': trade_summary.get('total_trades', 0)
            }
        
        # Rank strategies by total return
        ranking = sorted(
            strategy_metrics.items(),
            key=lambda x: x[1]['total_return'],
            reverse=True
        )
        
        summary['performance_ranking'] = [
            {
                'rank': i + 1,
                'strategy': name,
                'total_return': f"{metrics['total_return']:.2f}%",
                'win_rate': f"{metrics['win_rate']:.1f}%",
                'sharpe_ratio': f"{metrics['sharpe_ratio']:.2f}"
            }
            for i, (name, metrics) in enumerate(ranking)
        ]
        
        # Best strategy
        if ranking:
            best_name, best_metrics = ranking[0]
            summary['best_strategy'] = {
                'name': best_name,
                'total_return': f"{best_metrics['total_return']:.2f}%",
                'win_rate': f"{best_metrics['win_rate']:.1f}%",
                'profit_factor': f"{best_metrics['profit_factor']:.2f}",
                'sharpe_ratio': f"{best_metrics['sharpe_ratio']:.2f}"
            }
        
        # Key metrics comparison
        summary['key_metrics_comparison'] = strategy_metrics
        
        return summary

def main():
    """Main function for testing backtesting integration"""
    
    print("🚀 AI Gold Scalper - Backtesting Integration Test")
    print("=" * 70)
    
    # Initialize integration
    integration = BacktestingIntegration()
    
    # Run comprehensive backtest
    print("📊 Running comprehensive integrated backtest...")
    
    results = integration.run_comprehensive_backtest(
        symbol="XAUUSD",
        start_date="2023-06-01",
        end_date="2023-09-01"
    )
    
    if 'error' in results:
        print(f"❌ Backtest failed: {results['error']}")
        return
    
    print("✅ Comprehensive backtest completed!")
    
    # Display results
    backtest_info = results.get('backtest_info', {})
    summary = results.get('summary', {})
    
    print(f"\n📈 Results Summary:")
    print(f"   Total Return: {backtest_info.get('total_return_pct', 0):.2f}%")
    print(f"   Win Rate: {summary.get('win_rate', 0):.1f}%")
    print(f"   Profit Factor: {summary.get('profit_factor', 0):.2f}")
    print(f"   Sharpe Ratio: {summary.get('sharpe_ratio', 0):.2f}")
    print(f"   Total Trades: {summary.get('total_trades', 0)}")
    
    # Display AI metrics if available
    if 'ai_metrics' in results:
        ai_metrics = results['ai_metrics']
        print(f"\n🤖 AI Performance:")
        print(f"   Average Confidence: {ai_metrics.get('avg_confidence', 0):.2f}")
        print(f"   High Confidence Trades: {ai_metrics.get('high_confidence_trades', 0)}")
    
    # Run strategy comparison
    print("\n📊 Running strategy comparison...")
    
    comparison = integration.run_strategy_comparison()
    
    if 'error' not in comparison and comparison.get('comparison_summary'):
        ranking = comparison['comparison_summary'].get('performance_ranking', [])
        
        print(f"\n🏆 Strategy Performance Ranking:")
        for rank_info in ranking:
            print(f"   {rank_info['rank']}. {rank_info['strategy']}: {rank_info['total_return']} (WR: {rank_info['win_rate']})")
    
    print("\n✅ Backtesting integration test completed!")

if __name__ == "__main__":
    main()
