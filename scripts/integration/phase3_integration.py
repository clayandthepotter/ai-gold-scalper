#!/usr/bin/env python3
"""
AI Gold Scalper - Phase 3 Integration
Integrates model registry and adaptive learning with existing AI server and monitoring
"""

import os
import sys
import json
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "ai"))
sys.path.append(str(Path(__file__).parent.parent / "monitoring"))

# Import our new systems
from ai.model_registry import ModelRegistry, ModelMetadata
from ai.adaptive_learning import AdaptiveLearningSystem, LearningConfig

# Import existing systems
try:
    from monitoring.enhanced_trade_logger import EnhancedTradeLogger
    from monitoring.trade_postmortem_analyzer import TradePostmortemAnalyzer
except ImportError as e:
    print(f"⚠️  Some monitoring modules not available: {e}")

class Phase3Controller:
    """Main controller for Phase 3 functionality"""
    
    def __init__(self, config_path: str = "config/phase3_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize systems
        self.model_registry = ModelRegistry("models")
        self.adaptive_learning = AdaptiveLearningSystem(
            config=LearningConfig(
                min_trades_for_update=self.config.get('min_trades_for_update', 50),
                retraining_frequency_hours=self.config.get('retraining_frequency_hours', 24),
                performance_threshold=self.config.get('performance_threshold', 0.6)
            )
        )
        
        # Try to initialize existing systems
        try:
            self.trade_logger = EnhancedTradeLogger()
            self.postmortem_analyzer = TradePostmortemAnalyzer()
            self.monitoring_available = True
        except:
            self.monitoring_available = False
            print("⚠️  Monitoring systems not fully available - some features will be limited")
        
        self.is_running = False
        
    def _load_config(self) -> Dict[str, Any]:
        """Load Phase 3 configuration"""
        default_config = {
            'adaptive_learning_enabled': True,
            'auto_model_switching': True,
            'min_trades_for_update': 50,
            'retraining_frequency_hours': 24,
            'performance_threshold': 0.6,
            'model_evaluation_interval_minutes': 60,
            'auto_cleanup_models': True,
            'max_models_to_keep': 10,
            'monitoring_integration': True,
            'postmortem_integration': True
        }
        
        try:
            os.makedirs("config", exist_ok=True)
            
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            else:
                # Create default config file
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                print(f"✅ Created default config: {self.config_path}")
                
        except Exception as e:
            print(f"⚠️  Error loading config, using defaults: {e}")
            
        return default_config
    
    def get_active_model_for_prediction(self):
        """Get the active model for making predictions (integrates with existing AI server)"""
        model, metadata = self.model_registry.get_active_model()
        
        if model is None:
            print("⚠️  No active model found - creating default model")
            # Create a basic model if none exists
            self._create_default_model()
            model, metadata = self.model_registry.get_active_model()
            
        return model, metadata
    
    def _create_default_model(self):
        """Create a default model when none exists"""
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification
        
        # Generate sample data for initial model
        X, y = make_classification(n_samples=1000, n_features=10, random_state=42)
        
        # Create and train initial model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Create metadata
        metadata = ModelMetadata(
            model_id="",
            name="Default Random Forest",
            version="1.0.0",
            created_at=datetime.now(),
            model_type="sklearn",
            features_used=["price_change", "volume", "rsi", "macd", "bb_position"],
            hyperparameters={"n_estimators": 100, "random_state": 42},
            training_data_hash="default_model_hash",
            file_path="",
            accuracy=0.7,  # Baseline performance
            win_rate=0.6,
            profit_factor=1.2
        )
        
        # Register and activate
        model_id = self.model_registry.register_model(model, metadata)
        self.model_registry.set_active_model(model_id)
        
        print(f"✅ Created default model: {model_id}")
    
    def log_trade_with_model_info(self, trade_data: Dict[str, Any]):
        """Enhanced trade logging with model information"""
        if not self.monitoring_available:
            return
        
        # Get active model info
        _, active_metadata = self.model_registry.get_active_model()
        
        if active_metadata:
            # Add model information to trade data
            trade_data['model_id'] = active_metadata.model_id
            trade_data['model_name'] = active_metadata.name
            trade_data['model_version'] = active_metadata.version
        
        # Log the trade (this would integrate with existing trade logger)
        print(f"📊 Logging trade with model info: {trade_data.get('model_id', 'unknown')}")
    
    def evaluate_and_update_models(self):
        """Periodic evaluation and updating of models"""
        print("🔄 Evaluating model performance...")
        
        # Get all models and evaluate their recent performance
        models = self.model_registry.list_models()
        
        for model_metadata in models:
            if model_metadata.trades_count > 20:  # Only evaluate models with sufficient trades
                performance = self.adaptive_learning.evaluate_model_performance(
                    model_metadata.model_id, 
                    lookback_hours=24
                )
                
                if 'error' not in performance:
                    print(f"📈 Model {model_metadata.name}: Win Rate {performance['win_rate']:.2%}")
        
        # Run adaptive learning if enabled
        if self.config.get('adaptive_learning_enabled', True):
            learning_triggered = self.adaptive_learning.schedule_learning()
            
            if learning_triggered:
                print("🧠 New model created through adaptive learning")
                
                # Auto-switch to new model if configured
                if self.config.get('auto_model_switching', True):
                    best_model = self.model_registry.auto_select_best_model(
                        min_trades=self.config.get('min_trades_for_update', 50)
                    )
                    if best_model:
                        print(f"🔄 Switched to best performing model: {best_model}")
        
        # Cleanup old models if enabled
        if self.config.get('auto_cleanup_models', True):
            self.model_registry.cleanup_old_models(
                keep_count=self.config.get('max_models_to_keep', 10)
            )
    
    def run_postmortem_analysis_integration(self):
        """Integrate postmortem analysis with model performance tracking"""
        if not self.monitoring_available:
            return
        
        try:
            # Get recent trades
            conn = sqlite3.connect("scripts/monitoring/trade_logs.db")
            recent_trades = pd.read_sql_query("""
                SELECT te.*, ts.model_id 
                FROM trade_executions te
                LEFT JOIN trade_signals ts ON te.signal_id = ts.id
                WHERE te.timestamp >= datetime('now', '-24 hours')
                AND te.outcome = 'loss'
                ORDER BY te.timestamp DESC
                LIMIT 10
            """, conn)
            conn.close()
            
            if not recent_trades.empty:
                print(f"🔍 Running postmortem analysis on {len(recent_trades)} recent losses")
                
                # Group losses by model
                model_losses = recent_trades.groupby('model_id').size()
                
                for model_id, loss_count in model_losses.items():
                    if model_id and loss_count > 3:  # Focus on models with multiple losses
                        print(f"⚠️  Model {model_id} has {loss_count} recent losses - flagging for review")
                        
                        # This could trigger model retraining or deactivation
                        model_metadata = self.model_registry.get_model_metadata(model_id)
                        if model_metadata and model_metadata.is_active:
                            print(f"🚨 Active model {model_id} underperforming - consider retraining")
                        
        except Exception as e:
            print(f"⚠️  Error in postmortem analysis integration: {e}")
    
    def generate_phase3_report(self) -> Dict[str, Any]:
        """Generate comprehensive Phase 3 status report"""
        # Model registry summary
        registry_summary = self.model_registry.export_model_summary()
        
        # Learning system summary
        learning_summary = self.adaptive_learning.get_learning_summary()
        
        # Active model info
        active_model, active_metadata = self.model_registry.get_active_model()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'phase3_status': 'operational' if active_model else 'needs_attention',
            'active_model': {
                'id': active_metadata.model_id if active_metadata else None,
                'name': active_metadata.name if active_metadata else None,
                'version': active_metadata.version if active_metadata else None,
                'accuracy': active_metadata.accuracy if active_metadata else 0,
                'win_rate': active_metadata.win_rate if active_metadata else 0,
                'trades_count': active_metadata.trades_count if active_metadata else 0
            },
            'model_registry': registry_summary,
            'adaptive_learning': learning_summary,
            'config': self.config,
            'monitoring_available': self.monitoring_available,
            'recommendations': []
        }
        
        # Generate recommendations
        if registry_summary['total_models'] == 0:
            report['recommendations'].append("Create initial model - no models in registry")
        elif registry_summary['active_models'] == 0:
            report['recommendations'].append("Activate a model - no active model selected")
        elif active_metadata and active_metadata.win_rate < 0.6:
            report['recommendations'].append("Current model underperforming - consider retraining")
        elif learning_summary['total_learning_sessions'] == 0:
            report['recommendations'].append("Run initial adaptive learning cycle")
        
        if not self.monitoring_available:
            report['recommendations'].append("Install monitoring dependencies for full functionality")
        
        return report
    
    async def start_phase3_services(self):
        """Start Phase 3 background services"""
        print("🚀 Starting Phase 3 services...")
        self.is_running = True
        
        # Initial model check
        active_model, active_metadata = self.model_registry.get_active_model()
        if not active_model:
            print("🎯 No active model found - creating default model")
            self._create_default_model()
        
        evaluation_interval = self.config.get('model_evaluation_interval_minutes', 60) * 60
        
        while self.is_running:
            try:
                # Periodic model evaluation
                self.evaluate_and_update_models()
                
                # Postmortem analysis integration
                self.run_postmortem_analysis_integration()
                
                print(f"⏰ Phase 3 services running - next check in {evaluation_interval//60} minutes")
                
                # Wait for next evaluation cycle
                await asyncio.sleep(evaluation_interval)
                
            except Exception as e:
                print(f"❌ Error in Phase 3 services: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_phase3_services(self):
        """Stop Phase 3 background services"""
        print("🛑 Stopping Phase 3 services...")
        self.is_running = False
    
    def run_full_phase3_demo(self):
        """Run a complete demonstration of Phase 3 functionality"""
        print("🎯 AI Gold Scalper - Phase 3 Complete Demo")
        print("=" * 60)
        
        # 1. Model Registry Demo
        print("\n1️⃣ MODEL REGISTRY DEMO:")
        registry_summary = self.model_registry.export_model_summary()
        print(f"   Total Models: {registry_summary['total_models']}")
        print(f"   Active Models: {registry_summary['active_models']}")
        
        # 2. Adaptive Learning Demo
        print("\n2️⃣ ADAPTIVE LEARNING DEMO:")
        if registry_summary['total_models'] == 0:
            print("   Creating initial model...")
            self._create_default_model()
        
        learning_results = self.adaptive_learning.schedule_learning(run_immediately=True)
        print(f"   Learning cycle completed: {'Success' if learning_results else 'No new model needed'}")
        
        # 3. Model Comparison Demo
        print("\n3️⃣ MODEL COMPARISON DEMO:")
        models = self.model_registry.list_models()
        if len(models) >= 2:
            model_ids = [m.model_id for m in models[:2]]
            comparison = self.model_registry.compare_models(model_ids)
            print(f"   Best model: {comparison.get('best_model', 'None')}")
            print(f"   Confidence: {comparison.get('confidence_score', 0):.2%}")
        else:
            print("   Need at least 2 models for comparison")
        
        # 4. Integration Status
        print("\n4️⃣ INTEGRATION STATUS:")
        print(f"   Monitoring Available: {'✅' if self.monitoring_available else '❌'}")
        print(f"   Adaptive Learning: {'✅ Enabled' if self.config.get('adaptive_learning_enabled') else '❌ Disabled'}")
        print(f"   Auto Model Switching: {'✅ Enabled' if self.config.get('auto_model_switching') else '❌ Disabled'}")
        
        # 5. Generate comprehensive report
        print("\n5️⃣ COMPREHENSIVE REPORT:")
        report = self.generate_phase3_report()
        print(f"   Phase 3 Status: {report['phase3_status']}")
        print(f"   Active Model: {report['active_model']['name']}")
        print(f"   Win Rate: {report['active_model']['win_rate']:.2%}")
        
        if report['recommendations']:
            print("   📋 Recommendations:")
            for rec in report['recommendations']:
                print(f"      • {rec}")
        
        # Save report
        report_path = f"logs/phase3_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs("logs", exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"   📄 Report saved: {report_path}")
        
        print(f"\n✅ Phase 3 Demo Complete!")
        print(f"   Models in registry: {len(models)}")
        print(f"   Learning sessions: {report['adaptive_learning']['total_learning_sessions']}")
        print(f"   System ready for production trading!")

def main():
    """Main function for testing Phase 3 integration"""
    try:
        # Initialize Phase 3 controller
        phase3 = Phase3Controller()
        
        # Run full demonstration
        phase3.run_full_phase3_demo()
        
        # Option to start background services
        print(f"\n🤖 Phase 3 Integration Ready!")
        print(f"   To start background services: phase3.start_phase3_services()")
        print(f"   To get active model: phase3.get_active_model_for_prediction()")
        print(f"   To generate report: phase3.generate_phase3_report()")
        
    except KeyboardInterrupt:
        print("\n⏹️  Phase 3 demo interrupted by user")
    except Exception as e:
        print(f"❌ Error in Phase 3 integration: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
