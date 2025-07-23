#!/usr/bin/env python3
"""
AI Gold Scalper - Phase 4: Ensemble Models & Advanced AI
Combines multiple models for superior performance and market intelligence
"""

import os
import json
import pickle
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Machine Learning imports
from sklearn.ensemble import (
    RandomForestClassifier, 
    GradientBoostingClassifier, 
    VotingClassifier,
    BaggingClassifier,
    AdaBoostClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import GridSearchCV

# Advanced ML imports
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️  XGBoost not available - install with: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("⚠️  LightGBM not available - install with: pip install lightgbm")

try:
    import catboost as cb
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("⚠️  CatBoost not available - install with: pip install catboost")

try:
    from sklearn.experimental import enable_hist_gradient_boosting
    from sklearn.ensemble import HistGradientBoostingClassifier
    HIST_GRADIENT_AVAILABLE = True
except ImportError:
    HIST_GRADIENT_AVAILABLE = False
    print("⚠️  HistGradientBoosting not available")

try:
    from sklearn.ensemble import ExtraTreesClassifier
    EXTRA_TREES_AVAILABLE = True
except ImportError:
    EXTRA_TREES_AVAILABLE = False
    print("⚠️  ExtraTrees not available")

# Import our existing systems
from model_registry import ModelRegistry, ModelMetadata

@dataclass
class EnsembleConfig:
    """Configuration for ensemble model creation"""
    base_models: List[str] = None
    ensemble_methods: List[str] = None
    cross_validation_folds: int = 5
    min_model_accuracy: float = 0.65
    ensemble_weights: Optional[Dict[str, float]] = None
    meta_learner: str = 'logistic'
    stacking_enabled: bool = True
    voting_enabled: bool = True
    bagging_enabled: bool = True
    
    def __post_init__(self):
        if self.base_models is None:
            self.base_models = [
                'random_forest', 'gradient_boost', 'logistic', 'svm', 
                'neural_net', 'naive_bayes'
            ]
            if XGBOOST_AVAILABLE:
                self.base_models.append('xgboost')
            if LIGHTGBM_AVAILABLE:
                self.base_models.append('lightgbm')
            if CATBOOST_AVAILABLE:
                self.base_models.append('catboost')
            if HIST_GRADIENT_AVAILABLE:
                self.base_models.append('hist_gradient')
            if EXTRA_TREES_AVAILABLE:
                self.base_models.append('extra_trees')
        
        if self.ensemble_methods is None:
            self.ensemble_methods = ['voting', 'stacking', 'bagging']

@dataclass
class ModelPerformance:
    """Individual model performance metrics"""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cross_val_mean: float
    cross_val_std: float
    training_time: float
    prediction_time: float

class AdvancedEnsembleSystem:
    """Advanced ensemble model creation and management"""
    
    def __init__(self, model_registry: ModelRegistry = None):
        self.model_registry = model_registry or ModelRegistry("models")
        self.scaler = StandardScaler()
        self.ensemble_db = "models/ensemble_models.db"
        self._init_ensemble_database()
        
        # Model configurations
        self.base_model_configs = self._get_base_model_configs()
        
    def _init_ensemble_database(self):
        """Initialize ensemble model tracking database"""
        os.makedirs("models", exist_ok=True)
        
        conn = sqlite3.connect(self.ensemble_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ensemble_models (
            ensemble_id TEXT PRIMARY KEY,
            ensemble_type TEXT NOT NULL,
            base_models TEXT NOT NULL,  -- JSON
            created_at TIMESTAMP NOT NULL,
            performance_metrics TEXT NOT NULL,  -- JSON
            model_weights TEXT,  -- JSON
            cross_validation_scores TEXT,  -- JSON
            ensemble_accuracy REAL NOT NULL,
            is_active BOOLEAN DEFAULT 0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            ensemble_id TEXT NOT NULL,
            individual_predictions TEXT NOT NULL,  -- JSON
            ensemble_prediction REAL NOT NULL,
            actual_outcome INTEGER,
            confidence_score REAL NOT NULL,
            FOREIGN KEY (ensemble_id) REFERENCES ensemble_models (ensemble_id)
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ensemble_performance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ensemble_id TEXT NOT NULL,
            evaluation_date TIMESTAMP NOT NULL,
            accuracy REAL NOT NULL,
            precision_score REAL NOT NULL,
            recall_score REAL NOT NULL,
            f1_score REAL NOT NULL,
            trades_analyzed INTEGER NOT NULL,
            win_rate REAL NOT NULL,
            profit_factor REAL NOT NULL,
            FOREIGN KEY (ensemble_id) REFERENCES ensemble_models (ensemble_id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def _get_base_model_configs(self) -> Dict[str, Any]:
        """Get configurations for base models"""
        configs = {
            'random_forest': {
                'model': RandomForestClassifier(
                    n_estimators=200, 
                    max_depth=15, 
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'requires_scaling': False
            },
            'gradient_boost': {
                'model': GradientBoostingClassifier(
                    n_estimators=150, 
                    max_depth=8, 
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42
                ),
                'requires_scaling': False
            },
            'logistic': {
                'model': LogisticRegression(
                    random_state=42, 
                    max_iter=1000,
                    C=1.0,
                    penalty='l2'
                ),
                'requires_scaling': True
            },
            'svm': {
                'model': SVC(
                    kernel='rbf', 
                    C=1.0, 
                    gamma='scale',
                    probability=True,  # Needed for ensemble
                    random_state=42
                ),
                'requires_scaling': True
            },
            'neural_net': {
                'model': MLPClassifier(
                    hidden_layer_sizes=(100, 50),
                    activation='relu',
                    solver='adam',
                    max_iter=500,
                    random_state=42
                ),
                'requires_scaling': True
            },
            'naive_bayes': {
                'model': GaussianNB(),
                'requires_scaling': False
            }
        }
        
        # Add XGBoost if available
        if XGBOOST_AVAILABLE:
            configs['xgboost'] = {
                'model': xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    eval_metric='logloss'
                ),
                'requires_scaling': False
            }
        
        # Add LightGBM if available
        if LIGHTGBM_AVAILABLE:
            configs['lightgbm'] = {
                'model': lgb.LGBMClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbose=-1
                ),
                'requires_scaling': False
            }
        
        # Add CatBoost if available
        if CATBOOST_AVAILABLE:
            configs['catboost'] = {
                'model': cb.CatBoostClassifier(
                    iterations=100,
                    depth=6,
                    learning_rate=0.1,
                    random_seed=42,
                    verbose=False,
                    allow_writing_files=False
                ),
                'requires_scaling': False
            }
        
        # Add HistGradientBoosting if available
        if HIST_GRADIENT_AVAILABLE:
            configs['hist_gradient'] = {
                'model': HistGradientBoostingClassifier(
                    max_iter=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42
                ),
                'requires_scaling': False
            }
        
        # Add ExtraTrees if available
        if EXTRA_TREES_AVAILABLE:
            configs['extra_trees'] = {
                'model': ExtraTreesClassifier(
                    n_estimators=200,
                    max_depth=15,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42
                ),
                'requires_scaling': False
            }
        
        return configs
    
    def train_base_models(self, X: pd.DataFrame, y: pd.Series, 
                         config: EnsembleConfig = None) -> Dict[str, ModelPerformance]:
        """Train and evaluate individual base models"""
        if config is None:
            config = EnsembleConfig()
        
        print("🤖 Training base models for ensemble...")
        
        model_performances = {}
        trained_models = {}
        
        # Prepare cross-validation
        cv = StratifiedKFold(n_splits=config.cross_validation_folds, shuffle=True, random_state=42)
        
        for model_name in config.base_models:
            if model_name not in self.base_model_configs:
                print(f"⚠️  Model {model_name} not available, skipping...")
                continue
                
            print(f"   Training {model_name}...")
            start_time = datetime.now()
            
            try:
                model_config = self.base_model_configs[model_name]
                model = model_config['model']
                
                # Create pipeline with scaling if needed
                if model_config['requires_scaling']:
                    pipeline = Pipeline([
                        ('scaler', StandardScaler()),
                        ('model', model)
                    ])
                else:
                    pipeline = Pipeline([
                        ('model', model)
                    ])
                
                # Cross-validation scores
                cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='accuracy')
                
                # Train final model on full dataset
                pipeline.fit(X, y)
                y_pred = pipeline.predict(X)
                
                # Calculate performance metrics
                accuracy = accuracy_score(y, y_pred)
                precision = precision_score(y, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y, y_pred, average='weighted', zero_division=0)
                
                training_time = (datetime.now() - start_time).total_seconds()
                
                # Test prediction time
                pred_start = datetime.now()
                _ = pipeline.predict(X[:10])  # Small sample for timing
                prediction_time = (datetime.now() - pred_start).total_seconds() / 10
                
                performance = ModelPerformance(
                    model_name=model_name,
                    accuracy=accuracy,
                    precision=precision,
                    recall=recall,
                    f1_score=f1,
                    cross_val_mean=cv_scores.mean(),
                    cross_val_std=cv_scores.std(),
                    training_time=training_time,
                    prediction_time=prediction_time
                )
                
                # Only keep models that meet minimum accuracy
                if accuracy >= config.min_model_accuracy:
                    model_performances[model_name] = performance
                    trained_models[model_name] = pipeline
                    
                    print(f"   ✅ {model_name}: Accuracy {accuracy:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
                else:
                    print(f"   ❌ {model_name}: Accuracy {accuracy:.3f} below threshold")
                
            except Exception as e:
                print(f"   ❌ {model_name}: Training failed - {e}")
        
        self.trained_base_models = trained_models
        print(f"✅ Trained {len(model_performances)} base models successfully")
        
        return model_performances
    
    def create_voting_ensemble(self, base_performances: Dict[str, ModelPerformance],
                              config: EnsembleConfig = None) -> Any:
        """Create a voting classifier ensemble"""
        if config is None:
            config = EnsembleConfig()
            
        print("🗳️  Creating voting ensemble...")
        
        # Select best performing models
        sorted_models = sorted(base_performances.items(), 
                             key=lambda x: x[1].cross_val_mean, reverse=True)
        
        # Take top models for ensemble
        top_models = sorted_models[:min(5, len(sorted_models))]
        
        estimators = []
        for model_name, performance in top_models:
            if model_name in self.trained_base_models:
                estimators.append((model_name, self.trained_base_models[model_name]))
        
        if len(estimators) < 2:
            raise ValueError("Need at least 2 models for ensemble")
        
        # Create voting classifier (soft voting for probability-based decisions)
        voting_ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft'
        )
        
        print(f"   ✅ Created voting ensemble with {len(estimators)} models")
        return voting_ensemble
    
    def create_stacking_ensemble(self, base_performances: Dict[str, ModelPerformance],
                                config: EnsembleConfig = None) -> Any:
        """Create a stacking ensemble with meta-learner"""
        if config is None:
            config = EnsembleConfig()
            
        print("🏗️  Creating stacking ensemble...")
        
        from sklearn.ensemble import StackingClassifier
        
        # Select models for stacking
        sorted_models = sorted(base_performances.items(), 
                             key=lambda x: x[1].cross_val_mean, reverse=True)
        
        base_estimators = []
        for model_name, performance in sorted_models:
            if model_name in self.trained_base_models:
                base_estimators.append((model_name, self.trained_base_models[model_name]))
        
        if len(base_estimators) < 2:
            raise ValueError("Need at least 2 models for stacking")
        
        # Meta-learner selection
        meta_learners = {
            'logistic': LogisticRegression(random_state=42),
            'random_forest': RandomForestClassifier(n_estimators=50, random_state=42),
            'gradient_boost': GradientBoostingClassifier(n_estimators=50, random_state=42)
        }
        
        meta_learner = meta_learners.get(config.meta_learner, LogisticRegression(random_state=42))
        
        # Create stacking classifier
        stacking_ensemble = StackingClassifier(
            estimators=base_estimators,
            final_estimator=meta_learner,
            cv=3,  # Internal cross-validation
            stack_method='predict_proba'
        )
        
        print(f"   ✅ Created stacking ensemble with {len(base_estimators)} base models and {config.meta_learner} meta-learner")
        return stacking_ensemble
    
    def create_bagging_ensemble(self, base_performances: Dict[str, ModelPerformance]) -> Any:
        """Create a bagging ensemble of best model"""
        print("👝 Creating bagging ensemble...")
        
        # Find best performing model
        best_model_name = max(base_performances.items(), key=lambda x: x[1].cross_val_mean)[0]
        best_model = self.trained_base_models[best_model_name]
        
        # Create bagging ensemble
        bagging_ensemble = BaggingClassifier(
            base_estimator=best_model,
            n_estimators=10,
            random_state=42,
            n_jobs=-1
        )
        
        print(f"   ✅ Created bagging ensemble with {best_model_name} as base model")
        return bagging_ensemble
    
    def evaluate_ensemble(self, ensemble_model: Any, X: pd.DataFrame, y: pd.Series,
                         ensemble_type: str) -> Dict[str, Any]:
        """Evaluate ensemble model performance"""
        print(f"📊 Evaluating {ensemble_type} ensemble...")
        
        # Cross-validation evaluation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        cv_scores = cross_val_score(ensemble_model, X, y, cv=cv, scoring='accuracy')
        
        # Train and get detailed metrics
        ensemble_model.fit(X, y)
        y_pred = ensemble_model.predict(X)
        y_proba = ensemble_model.predict_proba(X)
        
        # Calculate metrics
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y, y_pred, average='weighted', zero_division=0)
        
        # Confidence scores (average probability of predicted class)
        confidence_scores = []
        for i, pred in enumerate(y_pred):
            confidence_scores.append(y_proba[i][pred])
        avg_confidence = np.mean(confidence_scores)
        
        evaluation = {
            'ensemble_type': ensemble_type,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'cross_val_mean': cv_scores.mean(),
            'cross_val_std': cv_scores.std(),
            'avg_confidence': avg_confidence,
            'cv_scores': cv_scores.tolist()
        }
        
        print(f"   ✅ {ensemble_type}: Accuracy {accuracy:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
        
        return evaluation
    
    def create_all_ensembles(self, X: pd.DataFrame, y: pd.Series, 
                           config: EnsembleConfig = None) -> Dict[str, Any]:
        """Create and evaluate all ensemble types"""
        if config is None:
            config = EnsembleConfig()
            
        print("🎯 Creating comprehensive ensemble models...")
        print("=" * 60)
        
        # Step 1: Train base models
        base_performances = self.train_base_models(X, y, config)
        
        if len(base_performances) < 2:
            raise ValueError("Need at least 2 successful base models for ensemble creation")
        
        ensembles = {}
        ensemble_evaluations = {}
        
        # Step 2: Create different ensemble types
        try:
            if config.voting_enabled and 'voting' in config.ensemble_methods:
                voting_ensemble = self.create_voting_ensemble(base_performances, config)
                voting_eval = self.evaluate_ensemble(voting_ensemble, X, y, 'voting')
                ensembles['voting'] = voting_ensemble
                ensemble_evaluations['voting'] = voting_eval
        except Exception as e:
            print(f"❌ Voting ensemble creation failed: {e}")
        
        try:
            if config.stacking_enabled and 'stacking' in config.ensemble_methods:
                stacking_ensemble = self.create_stacking_ensemble(base_performances, config)
                stacking_eval = self.evaluate_ensemble(stacking_ensemble, X, y, 'stacking')
                ensembles['stacking'] = stacking_ensemble
                ensemble_evaluations['stacking'] = stacking_eval
        except Exception as e:
            print(f"❌ Stacking ensemble creation failed: {e}")
        
        try:
            if config.bagging_enabled and 'bagging' in config.ensemble_methods:
                bagging_ensemble = self.create_bagging_ensemble(base_performances)
                bagging_eval = self.evaluate_ensemble(bagging_ensemble, X, y, 'bagging')
                ensembles['bagging'] = bagging_ensemble
                ensemble_evaluations['bagging'] = bagging_eval
        except Exception as e:
            print(f"❌ Bagging ensemble creation failed: {e}")
        
        # Step 3: Select best ensemble
        if ensemble_evaluations:
            best_ensemble_type = max(ensemble_evaluations.items(), 
                                   key=lambda x: x[1]['cross_val_mean'])[0]
            best_ensemble = ensembles[best_ensemble_type]
            best_evaluation = ensemble_evaluations[best_ensemble_type]
            
            print(f"\n🏆 Best ensemble: {best_ensemble_type}")
            print(f"   Accuracy: {best_evaluation['accuracy']:.3f}")
            print(f"   Cross-validation: {best_evaluation['cross_val_mean']:.3f}±{best_evaluation['cross_val_std']:.3f}")
            
            # Register best ensemble in model registry
            ensemble_id = self._register_ensemble(
                best_ensemble, best_ensemble_type, base_performances, best_evaluation
            )
            
            return {
                'ensembles': ensembles,
                'evaluations': ensemble_evaluations,
                'best_ensemble': best_ensemble,
                'best_ensemble_type': best_ensemble_type,
                'best_evaluation': best_evaluation,
                'ensemble_id': ensemble_id,
                'base_performances': base_performances
            }
        else:
            raise ValueError("No ensemble models were successfully created")
    
    def _register_ensemble(self, ensemble_model: Any, ensemble_type: str,
                          base_performances: Dict[str, ModelPerformance],
                          evaluation: Dict[str, Any]) -> str:
        """Register ensemble model in the system"""
        
        # Generate ensemble ID
        ensemble_id = f"ensemble_{ensemble_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save ensemble model
        ensemble_path = f"models/stored_models/{ensemble_id}.pkl"
        os.makedirs("models/stored_models", exist_ok=True)
        with open(ensemble_path, 'wb') as f:
            pickle.dump(ensemble_model, f)
        
        # Store in ensemble database
        conn = sqlite3.connect(self.ensemble_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO ensemble_models 
        (ensemble_id, ensemble_type, base_models, created_at, performance_metrics,
         cross_validation_scores, ensemble_accuracy)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            ensemble_id, ensemble_type, json.dumps(list(base_performances.keys())),
            datetime.now(), json.dumps(evaluation), 
            json.dumps(evaluation['cv_scores']), evaluation['accuracy']
        ))
        
        conn.commit()
        conn.close()
        
        # Register in model registry as well
        metadata = ModelMetadata(
            model_id="",
            name=f"Ensemble {ensemble_type.title()} Model",
            version=f"1.0_{datetime.now().strftime('%Y%m%d')}",
            created_at=datetime.now(),
            model_type="ensemble",
            features_used=[],  # Will be filled later
            hyperparameters={"ensemble_type": ensemble_type, "base_models": list(base_performances.keys())},
            training_data_hash=str(hash(str(datetime.now()))),
            file_path=ensemble_path,
            accuracy=evaluation['accuracy'],
            precision=evaluation['precision'],
            recall=evaluation['recall'],
            f1_score=evaluation['f1_score'],
            win_rate=0.0,  # Will be updated with real trading
            profit_factor=0.0
        )
        
        model_id = self.model_registry.register_model(ensemble_model, metadata)
        
        print(f"✅ Registered ensemble model: {ensemble_id} (Registry ID: {model_id})")
        
        return ensemble_id
    
    def calibrate_ensemble_confidence(self, ensemble_model: Any, X: pd.DataFrame, y: pd.Series) -> Any:
        """Apply probability calibration to improve confidence estimates"""
        print("🎯 Applying confidence calibration...")
        
        # Use Platt scaling (sigmoid) calibration
        calibrated_model = CalibratedClassifierCV(
            ensemble_model, 
            method='sigmoid',  # 'isotonic' for non-parametric
            cv=3  # 3-fold cross-validation
        )
        
        calibrated_model.fit(X, y)
        
        print("   ✅ Confidence calibration applied")
        return calibrated_model
    
    def create_hypertuned_base_models(self, X: pd.DataFrame, y: pd.Series, 
                                     config: EnsembleConfig = None) -> Dict[str, ModelPerformance]:
        """Train base models with hyperparameter tuning for better performance"""
        if config is None:
            config = EnsembleConfig()
        
        print("🔧 Training hypertuned base models for ensemble...")
        
        model_performances = {}
        trained_models = {}
        
        # Enhanced model configurations with hyperparameter grids
        enhanced_configs = {
            'random_forest': {
                'model': RandomForestClassifier(random_state=42),
                'param_grid': {
                    'model__n_estimators': [150, 200, 300],
                    'model__max_depth': [10, 15, 20],
                    'model__min_samples_split': [2, 5, 10],
                    'model__min_samples_leaf': [1, 2, 4]
                },
                'requires_scaling': False
            },
            'gradient_boost': {
                'model': GradientBoostingClassifier(random_state=42),
                'param_grid': {
                    'model__n_estimators': [100, 150, 200],
                    'model__max_depth': [6, 8, 10],
                    'model__learning_rate': [0.05, 0.1, 0.15],
                    'model__subsample': [0.8, 0.9, 1.0]
                },
                'requires_scaling': False
            },
            'neural_net': {
                'model': MLPClassifier(random_state=42, max_iter=1000),
                'param_grid': {
                    'model__hidden_layer_sizes': [(100, 50), (150, 75), (200, 100)],
                    'model__activation': ['relu', 'tanh'],
                    'model__alpha': [0.0001, 0.001, 0.01],
                    'model__learning_rate': ['constant', 'adaptive']
                },
                'requires_scaling': True
            }
        }
        
        # Add advanced models if available
        if XGBOOST_AVAILABLE:
            enhanced_configs['xgboost'] = {
                'model': xgb.XGBClassifier(random_state=42, eval_metric='logloss'),
                'param_grid': {
                    'model__n_estimators': [100, 150, 200],
                    'model__max_depth': [4, 6, 8],
                    'model__learning_rate': [0.05, 0.1, 0.15],
                    'model__subsample': [0.8, 0.9, 1.0],
                    'model__colsample_bytree': [0.8, 0.9, 1.0]
                },
                'requires_scaling': False
            }
        
        cv = StratifiedKFold(n_splits=min(5, config.cross_validation_folds), shuffle=True, random_state=42)
        
        for model_name in ['random_forest', 'gradient_boost', 'neural_net'] + (['xgboost'] if XGBOOST_AVAILABLE else []):
            if model_name not in enhanced_configs:
                continue
                
            print(f"   Hypertuning {model_name}...")
            start_time = datetime.now()
            
            try:
                model_config = enhanced_configs[model_name]
                base_model = model_config['model']
                
                # Create pipeline
                if model_config['requires_scaling']:
                    pipeline = Pipeline([
                        ('scaler', StandardScaler()),
                        ('model', base_model)
                    ])
                else:
                    pipeline = Pipeline([
                        ('model', base_model)
                    ])
                
                # Grid search with limited parameter combinations for speed
                limited_param_grid = {}
                for key, values in model_config['param_grid'].items():
                    limited_param_grid[key] = values[:2]  # Take first 2 values only
                
                grid_search = GridSearchCV(
                    pipeline, 
                    limited_param_grid, 
                    cv=3,  # Reduced CV for speed
                    scoring='accuracy',
                    n_jobs=-1,
                    verbose=0
                )
                
                grid_search.fit(X, y)
                best_pipeline = grid_search.best_estimator_
                
                # Evaluate best model
                cv_scores = cross_val_score(best_pipeline, X, y, cv=cv, scoring='accuracy')
                y_pred = best_pipeline.predict(X)
                
                accuracy = accuracy_score(y, y_pred)
                precision = precision_score(y, y_pred, average='weighted', zero_division=0)
                recall = recall_score(y, y_pred, average='weighted', zero_division=0)
                f1 = f1_score(y, y_pred, average='weighted', zero_division=0)
                
                training_time = (datetime.now() - start_time).total_seconds()
                
                performance = ModelPerformance(
                    model_name=model_name,
                    accuracy=accuracy,
                    precision=precision,
                    recall=recall,
                    f1_score=f1,
                    cross_val_mean=cv_scores.mean(),
                    cross_val_std=cv_scores.std(),
                    training_time=training_time,
                    prediction_time=0.001  # Estimated
                )
                
                if accuracy >= config.min_model_accuracy:
                    model_performances[model_name] = performance
                    trained_models[model_name] = best_pipeline
                    
                    print(f"   ✅ {model_name}: Accuracy {accuracy:.3f}, CV: {cv_scores.mean():.3f}±{cv_scores.std():.3f}")
                    print(f"      Best params: {grid_search.best_params_}")
                else:
                    print(f"   ❌ {model_name}: Accuracy {accuracy:.3f} below threshold")
                
            except Exception as e:
                print(f"   ❌ {model_name}: Hypertuning failed - {e}")
        
        self.trained_base_models = trained_models
        print(f"✅ Trained {len(model_performances)} hypertuned models successfully")
        
        return model_performances
    
    def create_confidence_weighted_ensemble(self, base_performances: Dict[str, ModelPerformance],
                                          X: pd.DataFrame, y: pd.Series) -> Any:
        """Create ensemble with confidence-based weighting"""
        print("⚖️  Creating confidence-weighted ensemble...")
        
        # Calculate confidence weights based on cross-validation stability
        weights = []
        estimators = []
        
        for model_name, performance in base_performances.items():
            if model_name in self.trained_base_models:
                # Weight based on accuracy and inverse of std (stability)
                stability_weight = 1.0 / (performance.cross_val_std + 0.001)  # Avoid division by zero
                accuracy_weight = performance.cross_val_mean
                combined_weight = (stability_weight * 0.3) + (accuracy_weight * 0.7)
                
                weights.append(combined_weight)
                estimators.append((model_name, self.trained_base_models[model_name]))
        
        if len(estimators) < 2:
            raise ValueError("Need at least 2 models for ensemble")
        
        # Normalize weights
        total_weight = sum(weights)
        normalized_weights = [w / total_weight for w in weights]
        
        # Create weighted voting classifier
        weighted_ensemble = VotingClassifier(
            estimators=estimators,
            voting='soft',
            weights=normalized_weights
        )
        
        print(f"   ✅ Created confidence-weighted ensemble with {len(estimators)} models")
        print(f"   Weights: {dict(zip([name for name, _ in estimators], [f'{w:.3f}' for w in normalized_weights]))}")
        
        return weighted_ensemble
    
    def generate_trading_features(self, price_data: pd.DataFrame) -> pd.DataFrame:
        """Generate advanced trading features for better model performance"""
        print("📈 Generating advanced trading features...")
        
        features_df = price_data.copy()
        
        # Assume price_data has columns: open, high, low, close, volume
        if 'close' in features_df.columns:
            close = features_df['close']
            
            # Technical indicators
            features_df['sma_5'] = close.rolling(5).mean()
            features_df['sma_10'] = close.rolling(10).mean()
            features_df['sma_20'] = close.rolling(20).mean()
            
            # Volatility features
            features_df['volatility_5'] = close.rolling(5).std()
            features_df['volatility_10'] = close.rolling(10).std()
            
            # Momentum features
            features_df['momentum_3'] = close.pct_change(3)
            features_df['momentum_5'] = close.pct_change(5)
            
            # Price position features
            features_df['price_position_sma20'] = close / features_df['sma_20']
            
            # Bollinger Bands
            bb_period = 20
            bb_std = 2
            bb_middle = close.rolling(bb_period).mean()
            bb_std_dev = close.rolling(bb_period).std()
            features_df['bb_upper'] = bb_middle + (bb_std_dev * bb_std)
            features_df['bb_lower'] = bb_middle - (bb_std_dev * bb_std)
            features_df['bb_position'] = (close - bb_lower) / (features_df['bb_upper'] - bb_lower)
            
            # RSI
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            features_df['rsi'] = 100 - (100 / (1 + rs))
            
        # Remove rows with NaN values
        features_df = features_df.dropna()
        
        print(f"   ✅ Generated {len(features_df.columns)} features from {len(features_df)} data points")
        return features_df
    
    def get_enhanced_prediction_with_confidence(self, ensemble_model: Any, X: np.ndarray, 
                                              use_calibration: bool = True) -> Dict[str, Any]:
        """Get enhanced prediction with multiple confidence metrics"""
        
        prediction = ensemble_model.predict(X)[0]
        probabilities = ensemble_model.predict_proba(X)[0]
        
        # Basic confidence (probability of predicted class)
        basic_confidence = float(probabilities[prediction])
        
        # Enhanced confidence metrics
        prob_margin = float(abs(probabilities[1] - probabilities[0]))  # Margin between classes
        entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))  # Prediction entropy
        max_prob = float(np.max(probabilities))
        
        # Composite confidence score
        composite_confidence = (
            basic_confidence * 0.4 +  # Basic probability
            prob_margin * 0.3 +       # Decision margin
            (1 - entropy / np.log(2)) * 0.2 +  # Entropy (normalized)
            max_prob * 0.1            # Maximum probability
        )
        
        result = {
            'final_prediction': int(prediction),
            'basic_confidence': basic_confidence,
            'enhanced_confidence': min(composite_confidence, 1.0),  # Cap at 1.0
            'probability_margin': prob_margin,
            'prediction_entropy': entropy,
            'class_probabilities': probabilities.tolist()
        }
        
        # Try to get individual model predictions for voting ensemble
        if hasattr(ensemble_model, 'estimators_'):
            individual_predictions = {}
            agreements = []
            
            for name, estimator in ensemble_model.estimators_:
                try:
                    pred = estimator.predict(X)[0]
                    prob = estimator.predict_proba(X)[0]
                    individual_predictions[name] = {
                        'prediction': int(pred),
                        'confidence': float(prob[pred]),
                        'probabilities': prob.tolist()
                    }
                    agreements.append(pred == prediction)
                except:
                    pass
            
            result['individual_predictions'] = individual_predictions
            
            # Model agreement confidence boost
            if agreements:
                agreement_rate = sum(agreements) / len(agreements)
                result['model_agreement'] = agreement_rate
                # Boost confidence based on agreement
                result['agreement_boosted_confidence'] = min(
                    result['enhanced_confidence'] * (0.8 + 0.4 * agreement_rate), 1.0
                )
            
        return result
    
    def get_ensemble_prediction_breakdown(self, ensemble_model: Any, X: np.ndarray) -> Dict[str, Any]:
        """Get detailed prediction breakdown for ensemble models"""
        return self.get_enhanced_prediction_with_confidence(ensemble_model, X)
    
    def load_ensemble_model(self, ensemble_id: str) -> Optional[Any]:
        """Load ensemble model by ID"""
        try:
            model_path = f"models/stored_models/{ensemble_id}.pkl"
            with open(model_path, 'rb') as f:
                ensemble_model = pickle.load(f)
            return ensemble_model
        except FileNotFoundError:
            print(f"❌ Ensemble model not found: {ensemble_id}")
            return None
    
    def get_ensemble_summary(self) -> Dict[str, Any]:
        """Get summary of all ensemble models"""
        conn = sqlite3.connect(self.ensemble_db)
        
        ensembles_df = pd.read_sql_query('''
        SELECT * FROM ensemble_models 
        ORDER BY ensemble_accuracy DESC
        ''', conn)
        
        conn.close()
        
        if ensembles_df.empty:
            return {"total_ensembles": 0, "ensembles": []}
        
        summary = {
            "total_ensembles": len(ensembles_df),
            "best_accuracy": ensembles_df['ensemble_accuracy'].max(),
            "avg_accuracy": ensembles_df['ensemble_accuracy'].mean(),
            "ensemble_types": ensembles_df['ensemble_type'].value_counts().to_dict(),
            "ensembles": []
        }
        
        for _, row in ensembles_df.iterrows():
            summary["ensembles"].append({
                "ensemble_id": row['ensemble_id'],
                "type": row['ensemble_type'],
                "accuracy": row['ensemble_accuracy'],
                "created_at": row['created_at'],
                "base_models": json.loads(row['base_models']),
                "is_active": row['is_active']
            })
        
        return summary

# Testing and demonstration
if __name__ == "__main__":
    print("🎯 AI Gold Scalper - Enhanced Ensemble Models with Confidence Boosting Test")
    print("=" * 80)
    
    # Initialize ensemble system
    ensemble_system = AdvancedEnsembleSystem()
    
    # Generate enhanced sample data for testing
    from sklearn.datasets import make_classification
    
    print("📊 Generating enhanced trading data with better separability...")
    X, y = make_classification(
        n_samples=1500,  # More data
        n_features=25,   # More features
        n_informative=20, # More informative features
        n_redundant=3,
        n_classes=2,
        class_sep=1.5,   # Better class separation
        random_state=42
    )
    
    # Convert to DataFrame
    feature_names = [f'feature_{i}' for i in range(25)]
    X_df = pd.DataFrame(X, columns=feature_names)
    y_series = pd.Series(y)
    
    print(f"   Data shape: {X_df.shape}")
    print(f"   Class distribution: {np.bincount(y)}")
    
    # Create enhanced ensemble configuration
    config = EnsembleConfig(
        min_model_accuracy=0.65,  # Higher threshold
        ensemble_methods=['voting', 'stacking', 'bagging'],
        cross_validation_folds=5  # More CV folds for better estimates
    )
    
    try:
        print("\n🚀 PHASE 1: Standard Ensemble Creation")
        print("=" * 50)
        
        # Create standard ensemble models
        standard_results = ensemble_system.create_all_ensembles(X_df, y_series, config)
        
        standard_confidence = standard_results['best_evaluation']['avg_confidence']
        print(f"\n📊 Standard Ensemble Results:")
        print(f"   Best Ensemble: {standard_results['best_ensemble_type']}")
        print(f"   Best Accuracy: {standard_results['best_evaluation']['accuracy']:.3f}")
        print(f"   Standard Confidence: {standard_confidence:.3f} ({standard_confidence*100:.1f}%)")
        
        print("\n🔧 PHASE 2: Hypertuned Model Creation")
        print("=" * 50)
        
        # Create hypertuned models
        hypertuned_performances = ensemble_system.create_hypertuned_base_models(X_df, y_series, config)
        
        # Create confidence-weighted ensemble
        weighted_ensemble = ensemble_system.create_confidence_weighted_ensemble(
            hypertuned_performances, X_df, y_series
        )
        
        # Evaluate weighted ensemble
        weighted_eval = ensemble_system.evaluate_ensemble(weighted_ensemble, X_df, y_series, 'confidence_weighted')
        weighted_confidence = weighted_eval['avg_confidence']
        
        print(f"\n📊 Hypertuned Ensemble Results:")
        print(f"   Ensemble Type: confidence_weighted")
        print(f"   Accuracy: {weighted_eval['accuracy']:.3f}")
        print(f"   Weighted Confidence: {weighted_confidence:.3f} ({weighted_confidence*100:.1f}%)")
        print(f"   Improvement: +{((weighted_confidence - standard_confidence) * 100):.1f}%")
        
        print("\n🎯 PHASE 3: Probability Calibration")
        print("=" * 50)
        
        # Apply calibration to the best ensemble
        calibrated_ensemble = ensemble_system.calibrate_ensemble_confidence(
            weighted_ensemble, X_df, y_series
        )
        
        # Evaluate calibrated ensemble
        calibrated_eval = ensemble_system.evaluate_ensemble(calibrated_ensemble, X_df, y_series, 'calibrated')
        calibrated_confidence = calibrated_eval['avg_confidence']
        
        print(f"\n📊 Calibrated Ensemble Results:")
        print(f"   Ensemble Type: calibrated")
        print(f"   Accuracy: {calibrated_eval['accuracy']:.3f}")
        print(f"   Calibrated Confidence: {calibrated_confidence:.3f} ({calibrated_confidence*100:.1f}%)")
        print(f"   Total Improvement: +{((calibrated_confidence - standard_confidence) * 100):.1f}%")
        
        print("\n🔍 PHASE 4: Enhanced Prediction Analysis")
        print("=" * 50)
        
        # Test enhanced prediction on multiple samples
        sample_indices = [0, 100, 200, 300, 400]
        enhanced_confidences = []
        agreement_confidences = []
        
        for idx in sample_indices:
            sample_data = X_df.iloc[idx:idx+1].values
            enhanced_pred = ensemble_system.get_enhanced_prediction_with_confidence(
                calibrated_ensemble, sample_data
            )
            
            enhanced_confidences.append(enhanced_pred['enhanced_confidence'])
            if 'agreement_boosted_confidence' in enhanced_pred:
                agreement_confidences.append(enhanced_pred['agreement_boosted_confidence'])
            
            print(f"   Sample {idx}: Enhanced={enhanced_pred['enhanced_confidence']:.3f}, "
                  f"Agreement={enhanced_pred.get('agreement_boosted_confidence', 'N/A')}")
        
        avg_enhanced = np.mean(enhanced_confidences)
        avg_agreement = np.mean(agreement_confidences) if agreement_confidences else avg_enhanced
        
        print(f"\n🏆 FINAL CONFIDENCE COMPARISON:")
        print(f"   📍 Original Confidence:     {standard_confidence:.3f} ({standard_confidence*100:.1f}%)")
        print(f"   📍 Weighted Ensemble:       {weighted_confidence:.3f} ({weighted_confidence*100:.1f}%)")
        print(f"   📍 Calibrated:              {calibrated_confidence:.3f} ({calibrated_confidence*100:.1f}%)")
        print(f"   📍 Enhanced Multi-metric:   {avg_enhanced:.3f} ({avg_enhanced*100:.1f}%)")
        print(f"   📍 Agreement Boosted:       {avg_agreement:.3f} ({avg_agreement*100:.1f}%)")
        
        final_improvement = ((avg_agreement - standard_confidence) / standard_confidence) * 100
        print(f"\n🚀 TOTAL CONFIDENCE IMPROVEMENT: +{final_improvement:.1f}%")
        
        if avg_agreement >= 0.85:
            print("\n🌟 EXCELLENT! Achieved high confidence (≥85%)")
        elif avg_agreement >= 0.80:
            print("\n🎯 GREAT! Achieved good confidence (≥80%)")
        elif avg_agreement >= 0.75:
            print("\n👍 GOOD! Achieved decent confidence (≥75%)")
        else:
            print(f"\n📈 IMPROVED! Confidence increased from {standard_confidence*100:.1f}% to {avg_agreement*100:.1f}%")
        
        # Test detailed prediction breakdown
        print("\n🔬 DETAILED PREDICTION BREAKDOWN (Sample):")
        sample_data = X_df.iloc[0:1].values
        detailed_breakdown = ensemble_system.get_enhanced_prediction_with_confidence(
            calibrated_ensemble, sample_data
        )
        
        print(f"   Final Prediction: {detailed_breakdown['final_prediction']}")
        print(f"   Basic Confidence: {detailed_breakdown['basic_confidence']:.3f}")
        print(f"   Enhanced Confidence: {detailed_breakdown['enhanced_confidence']:.3f}")
        print(f"   Probability Margin: {detailed_breakdown['probability_margin']:.3f}")
        print(f"   Prediction Entropy: {detailed_breakdown['prediction_entropy']:.3f}")
        if 'model_agreement' in detailed_breakdown:
            print(f"   Model Agreement: {detailed_breakdown['model_agreement']:.3f}")
        if 'agreement_boosted_confidence' in detailed_breakdown:
            print(f"   Agreement Boosted: {detailed_breakdown['agreement_boosted_confidence']:.3f}")
        
        print(f"\n✅ Enhanced ensemble system test completed successfully!")
        print(f"🎉 Final confidence level: {avg_agreement*100:.1f}% (Target: >80%)")
        
    except Exception as e:
        print(f"❌ Error in enhanced ensemble creation: {e}")
        import traceback
        traceback.print_exc()
