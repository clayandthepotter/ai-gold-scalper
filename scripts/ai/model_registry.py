#!/usr/bin/env python3
"""
AI Gold Scalper - Model Registry & Management System
Manages multiple AI models, tracks performance, and handles model switching
"""

import os
import json
import pickle
import sqlite3
import hashlib
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

@dataclass
class ModelMetadata:
    """Model metadata for tracking and comparison"""
    model_id: str
    name: str
    version: str
    created_at: datetime
    model_type: str  # 'sklearn', 'neural_net', 'ensemble'
    features_used: List[str]
    hyperparameters: Dict[str, Any]
    training_data_hash: str
    file_path: str
    
    # Performance metrics
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    
    # Trading performance
    trades_count: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    # Status
    is_active: bool = False
    is_production: bool = False
    last_updated: Optional[datetime] = None
    notes: str = ""

class ModelRegistry:
    """Centralized model management and performance tracking"""
    
    def __init__(self, base_path: str = "models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        self.registry_db = self.base_path / "model_registry.db"
        self.models_dir = self.base_path / "stored_models"
        self.models_dir.mkdir(exist_ok=True)
        
        self._init_database()
        self.active_model_id = None
        
    def _init_database(self):
        """Initialize model registry database"""
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS models (
            model_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            version TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            model_type TEXT NOT NULL,
            features_used TEXT NOT NULL,  -- JSON
            hyperparameters TEXT NOT NULL,  -- JSON
            training_data_hash TEXT NOT NULL,
            file_path TEXT NOT NULL,
            
            -- Performance metrics
            accuracy REAL DEFAULT 0.0,
            precision_score REAL DEFAULT 0.0,
            recall_score REAL DEFAULT 0.0,
            f1_score REAL DEFAULT 0.0,
            
            -- Trading performance
            trades_count INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0,
            profit_factor REAL DEFAULT 0.0,
            sharpe_ratio REAL DEFAULT 0.0,
            max_drawdown REAL DEFAULT 0.0,
            
            -- Status
            is_active BOOLEAN DEFAULT 0,
            is_production BOOLEAN DEFAULT 0,
            last_updated TIMESTAMP,
            notes TEXT DEFAULT ""
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_performance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            period_start TIMESTAMP NOT NULL,
            period_end TIMESTAMP NOT NULL,
            trades_analyzed INTEGER DEFAULT 0,
            FOREIGN KEY (model_id) REFERENCES models (model_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comparison_date TIMESTAMP NOT NULL,
            models_compared TEXT NOT NULL,  -- JSON array of model_ids
            winner_model_id TEXT NOT NULL,
            comparison_metrics TEXT NOT NULL,  -- JSON
            confidence_score REAL NOT NULL,
            notes TEXT DEFAULT ""
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def register_model(self, model: Any, metadata: ModelMetadata) -> str:
        """Register a new model in the registry"""
        
        # Generate unique model ID
        model_id = self._generate_model_id(metadata)
        metadata.model_id = model_id
        
        # Save model file
        model_file_path = self.models_dir / f"{model_id}.pkl"
        with open(model_file_path, 'wb') as f:
            pickle.dump(model, f)
        
        metadata.file_path = str(model_file_path)
        
        # Store metadata in database
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO models (
            model_id, name, version, created_at, model_type,
            features_used, hyperparameters, training_data_hash, file_path,
            accuracy, precision_score, recall_score, f1_score,
            trades_count, win_rate, profit_factor, sharpe_ratio, max_drawdown,
            is_active, is_production, last_updated, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metadata.model_id, metadata.name, metadata.version, metadata.created_at,
            metadata.model_type, json.dumps(metadata.features_used),
            json.dumps(metadata.hyperparameters), metadata.training_data_hash,
            metadata.file_path, metadata.accuracy, metadata.precision,
            metadata.recall, metadata.f1_score, metadata.trades_count,
            metadata.win_rate, metadata.profit_factor, metadata.sharpe_ratio,
            metadata.max_drawdown, metadata.is_active, metadata.is_production,
            metadata.last_updated, metadata.notes
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Model registered: {metadata.name} v{metadata.version}")
        print(f"   Model ID: {model_id}")
        
        return model_id
    
    def load_model(self, model_id: str) -> Optional[Any]:
        """Load a model by its ID"""
        metadata = self.get_model_metadata(model_id)
        if not metadata:
            return None
        
        try:
            with open(metadata.file_path, 'rb') as f:
                model = pickle.load(f)
            return model
        except FileNotFoundError:
            print(f"❌ Model file not found: {metadata.file_path}")
            return None
    
    def get_model_metadata(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID"""
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM models WHERE model_id = ?', (model_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return ModelMetadata(
            model_id=row[0], name=row[1], version=row[2],
            created_at=datetime.fromisoformat(row[3]), model_type=row[4],
            features_used=json.loads(row[5]), hyperparameters=json.loads(row[6]),
            training_data_hash=row[7], file_path=row[8],
            accuracy=row[9], precision=row[10], recall=row[11], f1_score=row[12],
            trades_count=row[13], win_rate=row[14], profit_factor=row[15],
            sharpe_ratio=row[16], max_drawdown=row[17], is_active=bool(row[18]),
            is_production=bool(row[19]),
            last_updated=datetime.fromisoformat(row[20]) if row[20] else None,
            notes=row[21]
        )
    
    def list_models(self, active_only: bool = False, production_only: bool = False) -> List[ModelMetadata]:
        """List all registered models"""
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        query = 'SELECT * FROM models WHERE 1=1'
        params = []
        
        if active_only:
            query += ' AND is_active = 1'
        if production_only:
            query += ' AND is_production = 1'
            
        query += ' ORDER BY created_at DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        models = []
        for row in rows:
            models.append(ModelMetadata(
                model_id=row[0], name=row[1], version=row[2],
                created_at=datetime.fromisoformat(row[3]), model_type=row[4],
                features_used=json.loads(row[5]), hyperparameters=json.loads(row[6]),
                training_data_hash=row[7], file_path=row[8],
                accuracy=row[9], precision=row[10], recall=row[11], f1_score=row[12],
                trades_count=row[13], win_rate=row[14], profit_factor=row[15],
                sharpe_ratio=row[16], max_drawdown=row[17], is_active=bool(row[18]),
                is_production=bool(row[19]),
                last_updated=datetime.fromisoformat(row[20]) if row[20] else None,
                notes=row[21]
            ))
        
        return models
    
    def set_active_model(self, model_id: str) -> bool:
        """Set a model as the active model"""
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        # Deactivate all models
        cursor.execute('UPDATE models SET is_active = 0')
        
        # Activate selected model
        cursor.execute('UPDATE models SET is_active = 1 WHERE model_id = ?', (model_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return False
        
        conn.commit()
        conn.close()
        
        self.active_model_id = model_id
        print(f"✅ Active model set to: {model_id}")
        return True
    
    def get_active_model(self) -> Tuple[Optional[Any], Optional[ModelMetadata]]:
        """Get the currently active model and its metadata"""
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT model_id FROM models WHERE is_active = 1')
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None, None
        
        model_id = result[0]
        model = self.load_model(model_id)
        metadata = self.get_model_metadata(model_id)
        
        return model, metadata
    
    def update_model_performance(self, model_id: str, performance_metrics: Dict[str, float]):
        """Update model performance metrics"""
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        # Update main metrics
        update_fields = []
        update_values = []
        
        metric_mapping = {
            'accuracy': 'accuracy',
            'precision': 'precision_score',
            'recall': 'recall_score',
            'f1_score': 'f1_score',
            'win_rate': 'win_rate',
            'profit_factor': 'profit_factor',
            'sharpe_ratio': 'sharpe_ratio',
            'max_drawdown': 'max_drawdown',
            'trades_count': 'trades_count'
        }
        
        for metric, db_field in metric_mapping.items():
            if metric in performance_metrics:
                update_fields.append(f'{db_field} = ?')
                update_values.append(performance_metrics[metric])
        
        if update_fields:
            update_values.append(datetime.now())
            update_values.append(model_id)
            
            query = f'''
            UPDATE models SET 
            {', '.join(update_fields)}, 
            last_updated = ? 
            WHERE model_id = ?
            '''
            
            cursor.execute(query, update_values)
        
        # Store historical performance
        for metric, value in performance_metrics.items():
            cursor.execute('''
            INSERT INTO model_performance_history 
            (model_id, timestamp, metric_name, metric_value, period_start, period_end)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                model_id, datetime.now(), metric,
                value, datetime.now() - timedelta(hours=1), datetime.now()
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Performance updated for model: {model_id}")
    
    def compare_models(self, model_ids: List[str], comparison_metrics: List[str] = None) -> Dict[str, Any]:
        """Compare multiple models across various metrics"""
        if not comparison_metrics:
            comparison_metrics = ['accuracy', 'win_rate', 'profit_factor', 'sharpe_ratio']
        
        models_data = []
        for model_id in model_ids:
            metadata = self.get_model_metadata(model_id)
            if metadata:
                models_data.append(metadata)
        
        if len(models_data) < 2:
            return {"error": "Need at least 2 models to compare"}
        
        comparison_results = {
            "comparison_date": datetime.now(),
            "models": {},
            "rankings": {},
            "best_model": None,
            "confidence_score": 0.0
        }
        
        # Collect metrics for each model
        for model in models_data:
            comparison_results["models"][model.model_id] = {
                "name": f"{model.name} v{model.version}",
                "metrics": {}
            }
            
            for metric in comparison_metrics:
                if hasattr(model, metric):
                    value = getattr(model, metric)
                    comparison_results["models"][model.model_id]["metrics"][metric] = value
        
        # Calculate rankings for each metric
        for metric in comparison_metrics:
            metric_values = []
            for model_id in comparison_results["models"]:
                value = comparison_results["models"][model_id]["metrics"].get(metric, 0)
                metric_values.append((model_id, value))
            
            # Sort descending (higher is better)
            metric_values.sort(key=lambda x: x[1], reverse=True)
            comparison_results["rankings"][metric] = [model_id for model_id, _ in metric_values]
        
        # Determine overall best model
        model_scores = {model_id: 0 for model_id in model_ids}
        
        for metric, ranking in comparison_results["rankings"].items():
            for i, model_id in enumerate(ranking):
                model_scores[model_id] += (len(ranking) - i)
        
        best_model_id = max(model_scores, key=model_scores.get)
        comparison_results["best_model"] = best_model_id
        
        # Calculate confidence score
        max_score = max(model_scores.values())
        second_max = sorted(model_scores.values())[-2] if len(model_scores) > 1 else 0
        comparison_results["confidence_score"] = (max_score - second_max) / max_score if max_score > 0 else 0
        
        # Store comparison in database
        conn = sqlite3.connect(self.registry_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO model_comparisons 
        (comparison_date, models_compared, winner_model_id, comparison_metrics, confidence_score)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            datetime.now(), json.dumps(model_ids), best_model_id,
            json.dumps(comparison_results), comparison_results["confidence_score"]
        ))
        
        conn.commit()
        conn.close()
        
        return comparison_results
    
    def auto_select_best_model(self, min_trades: int = 100, min_confidence: float = 0.7) -> Optional[str]:
        """Automatically select the best performing model"""
        models = self.list_models()
        
        # Filter models with enough trading data
        eligible_models = []
        for model in models:
            if model.trades_count >= min_trades:
                eligible_models.append(model.model_id)
        
        if len(eligible_models) < 2:
            print("⚠️  Not enough models with sufficient trading data for comparison")
            return None
        
        # Compare eligible models
        comparison = self.compare_models(eligible_models)
        
        if comparison.get("confidence_score", 0) >= min_confidence:
            best_model_id = comparison["best_model"]
            self.set_active_model(best_model_id)
            print(f"🏆 Auto-selected best model: {best_model_id}")
            print(f"   Confidence: {comparison['confidence_score']:.2%}")
            return best_model_id
        else:
            print(f"⚠️  Best model confidence ({comparison.get('confidence_score', 0):.2%}) below threshold ({min_confidence:.2%})")
            return None
    
    def cleanup_old_models(self, keep_count: int = 10, keep_production: bool = True):
        """Clean up old model files, keeping only the most recent ones"""
        models = self.list_models()
        
        # Separate production and non-production models
        production_models = [m for m in models if m.is_production]
        other_models = [m for m in models if not m.is_production]
        
        # Sort by creation date
        other_models.sort(key=lambda x: x.created_at, reverse=True)
        
        models_to_keep = set()
        
        # Always keep production models if specified
        if keep_production:
            models_to_keep.update(m.model_id for m in production_models)
        
        # Keep the most recent non-production models
        models_to_keep.update(m.model_id for m in other_models[:keep_count])
        
        # Delete old models
        deleted_count = 0
        for model in models:
            if model.model_id not in models_to_keep:
                # Delete model file
                if os.path.exists(model.file_path):
                    os.remove(model.file_path)
                
                # Remove from database
                conn = sqlite3.connect(self.registry_db)
                cursor = conn.cursor()
                cursor.execute('DELETE FROM models WHERE model_id = ?', (model.model_id,))
                cursor.execute('DELETE FROM model_performance_history WHERE model_id = ?', (model.model_id,))
                conn.commit()
                conn.close()
                
                deleted_count += 1
        
        print(f"🧹 Cleaned up {deleted_count} old models")
        print(f"   Kept: {len(models_to_keep)} models")
    
    def _generate_model_id(self, metadata: ModelMetadata) -> str:
        """Generate a unique model ID"""
        id_components = [
            metadata.name,
            metadata.version,
            metadata.model_type,
            str(metadata.created_at),
            metadata.training_data_hash
        ]
        
        id_string = "_".join(id_components)
        return hashlib.md5(id_string.encode()).hexdigest()[:16]
    
    def export_model_summary(self) -> Dict[str, Any]:
        """Export a summary of all models for reporting"""
        models = self.list_models()
        
        summary = {
            "total_models": len(models),
            "active_models": len([m for m in models if m.is_active]),
            "production_models": len([m for m in models if m.is_production]),
            "model_types": {},
            "performance_summary": {},
            "models": []
        }
        
        # Count model types
        for model in models:
            summary["model_types"][model.model_type] = summary["model_types"].get(model.model_type, 0) + 1
        
        # Performance summary
        if models:
            accuracies = [m.accuracy for m in models if m.accuracy > 0]
            win_rates = [m.win_rate for m in models if m.win_rate > 0]
            
            summary["performance_summary"] = {
                "avg_accuracy": np.mean(accuracies) if accuracies else 0,
                "best_accuracy": max(accuracies) if accuracies else 0,
                "avg_win_rate": np.mean(win_rates) if win_rates else 0,
                "best_win_rate": max(win_rates) if win_rates else 0,
            }
        
        # Model details
        for model in models:
            summary["models"].append({
                "id": model.model_id,
                "name": f"{model.name} v{model.version}",
                "type": model.model_type,
                "created": model.created_at.isoformat(),
                "accuracy": model.accuracy,
                "win_rate": model.win_rate,
                "trades": model.trades_count,
                "is_active": model.is_active,
                "is_production": model.is_production
            })
        
        return summary

import time
import sys
import argparse

def run_service_mode(registry):
    """Run model registry as a persistent service"""
    print("[OK] Model Registry Service Started")
    print("   Monitoring for model updates and performance tracking...")
    
    try:
        while True:
            # Service loop - the registry is available for other components to use
            # In a real implementation, this would handle:
            # - Performance metric updates from trading components
            # - Model comparison requests
            # - Health checks
            
            time.sleep(30)  # Check every 30 seconds
            
            # Periodic maintenance (could be expanded)
            # For now, just ensure the registry is responsive
            models = registry.list_models()
            if len(models) > 0:
                # Registry is working properly
                pass
                
    except KeyboardInterrupt:
        print("\n[OK] Model Registry Service stopped")
    except Exception as e:
        print(f"[ERROR] Error in model registry service: {e}")
        sys.exit(1)

# Testing and demonstration
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Gold Scalper Model Registry")
    parser.add_argument('--service', action='store_true', help='Run as a persistent service')
    parser.add_argument('--demo', action='store_true', help='Run demo and exit')
    
    args = parser.parse_args()
    
    # Initialize registry
    registry = ModelRegistry("models")
    
    if args.service:
        # Service mode - keep running
        run_service_mode(registry)
    else:
        # Demo mode or default behavior
        # Create sample model metadata
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.datasets import make_classification
        
        # Generate sample data
        X, y = make_classification(n_samples=1000, n_features=10, random_state=42)
        
        # Create and train sample model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        
        # Create metadata
        metadata = ModelMetadata(
            model_id="",  # Will be generated
            name="Random Forest Gold Predictor",
            version="1.0.0",
            created_at=datetime.now(),
            model_type="sklearn",
            features_used=["price_change", "volume", "rsi", "macd", "bb_position"],
            hyperparameters={"n_estimators": 100, "random_state": 42},
            training_data_hash="abc123def456",
            file_path="",  # Will be set by registry
            accuracy=0.85,
            win_rate=0.72,
            profit_factor=1.45
        )
        
        # Register model
        model_id = registry.register_model(model, metadata)
        
        # Set as active
        registry.set_active_model(model_id)
        
        # Load active model
        active_model, active_metadata = registry.get_active_model()
        
        print(f"\n✅ Active model loaded: {active_metadata.name}")
        print(f"   Accuracy: {active_metadata.accuracy:.2%}")
        print(f"   Win Rate: {active_metadata.win_rate:.2%}")
        
        # Export summary
        summary = registry.export_model_summary()
        print(f"\n📊 Registry Summary:")
        print(f"   Total Models: {summary['total_models']}")
        print(f"   Active Models: {summary['active_models']}")
        print(f"   Average Accuracy: {summary['performance_summary']['avg_accuracy']:.2%}")
        
        if not args.demo:
            # If not explicitly demo mode, run as service
            print("\n🔄 Switching to service mode...")
            run_service_mode(registry)
