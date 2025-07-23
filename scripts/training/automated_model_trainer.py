#!/usr/bin/env python3
"""
AI Gold Scalper - Automated Model Trainer
Phase 6: Production Integration & Infrastructure

Automated model training system that continuously monitors performance,
retrains models when needed, and manages model lifecycle.
"""

import asyncio
import json
import logging
import pandas as pd
import numpy as np
import sqlite3
import pickle
import joblib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import schedule
import threading
import time

# ML Libraries
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import optuna
import warnings
warnings.filterwarnings('ignore')

# Import our existing components
import sys
sys.path.append('scripts')
from models.model_registry import ModelRegistry, ModelMetadata
from monitoring.trade_postmortem_analyzer import TradePostmortemAnalyzer

@dataclass
class TrainingConfig:
    """Training configuration"""
    min_samples: int = 100
    retrain_threshold: float = 0.05  # Performance degradation threshold
    max_training_time: int = 300  # Max training time in seconds
    feature_lookback: int = 50  # Historical periods for features
    validation_split: float = 0.2
    cv_folds: int = 5
    hyperopt_trials: int = 50
    models_to_train: List[str] = None
    
    def __post_init__(self):
        if self.models_to_train is None:
            self.models_to_train = ['random_forest', 'gradient_boosting', 'ridge']

@dataclass
class TrainingResult:
    """Training result data"""
    model_name: str
    model_version: str
    training_score: float
    validation_score: float
    cross_val_score: float
    feature_importance: Dict[str, float]
    training_time: float
    sample_count: int
    parameters: Dict[str, Any]
    metrics: Dict[str, float]
    success: bool
    error_message: Optional[str] = None

class FeatureEngineering:
    """Advanced feature engineering for trading models"""
    
    @staticmethod
    def create_technical_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create technical indicator features"""
        features = df.copy()
        
        # Price-based features
        features['returns'] = features['close'].pct_change()
        features['log_returns'] = np.log(features['close'] / features['close'].shift(1))
        features['price_change'] = features['close'] - features['open']
        features['price_range'] = features['high'] - features['low']
        features['body_size'] = abs(features['close'] - features['open'])
        features['upper_shadow'] = features['high'] - np.maximum(features['open'], features['close'])
        features['lower_shadow'] = np.minimum(features['open'], features['close']) - features['low']
        
        # Moving averages
        for period in [5, 10, 20, 50]:
            features[f'sma_{period}'] = features['close'].rolling(period).mean()
            features[f'ema_{period}'] = features['close'].ewm(span=period).mean()
            features[f'price_to_sma_{period}'] = features['close'] / features[f'sma_{period}']
        
        # Volatility features
        features['volatility_5'] = features['returns'].rolling(5).std()
        features['volatility_20'] = features['returns'].rolling(20).std()
        features['atr_14'] = (features['high'] - features['low']).rolling(14).mean()
        
        # Momentum indicators
        features['rsi_14'] = calculate_rsi(features['close'], 14)
        features['roc_10'] = ((features['close'] - features['close'].shift(10)) / features['close'].shift(10)) * 100
        
        # Volume features (if available)
        if 'volume' in features.columns:
            features['volume_sma_10'] = features['volume'].rolling(10).mean()
            features['volume_ratio'] = features['volume'] / features['volume_sma_10']
            features['price_volume'] = features['close'] * features['volume']
        
        # Trend features
        features['trend_strength'] = abs(features['close'].rolling(10).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0]
        ))
        
        # Pattern features
        features['doji'] = (abs(features['close'] - features['open']) / features['price_range'] < 0.1).astype(int)
        features['hammer'] = ((features['lower_shadow'] > 2 * features['body_size']) & 
                             (features['upper_shadow'] < features['body_size'])).astype(int)
        
        # Lag features
        for lag in [1, 2, 3, 5, 10]:
            features[f'close_lag_{lag}'] = features['close'].shift(lag)
            features[f'returns_lag_{lag}'] = features['returns'].shift(lag)
            features[f'volume_lag_{lag}'] = features.get('volume', pd.Series(0, index=features.index)).shift(lag)
        
        return features
    
    @staticmethod
    def create_market_regime_features(df: pd.DataFrame) -> pd.DataFrame:
        """Create market regime features"""
        features = df.copy()
        
        # Regime detection based on volatility
        vol_short = features['returns'].rolling(5).std()
        vol_long = features['returns'].rolling(20).std()
        features['volatility_regime'] = (vol_short > vol_long * 1.5).astype(int)
        
        # Trend regime
        sma_short = features['close'].rolling(10).mean()
        sma_long = features['close'].rolling(30).mean()
        features['trend_regime'] = (sma_short > sma_long).astype(int)
        
        # Market hours (assuming UTC)
        features['hour'] = pd.to_datetime(features.index).hour
        features['day_of_week'] = pd.to_datetime(features.index).dayofweek
        features['is_trading_hours'] = ((features['hour'] >= 8) & (features['hour'] <= 17)).astype(int)
        
        return features

def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

class ModelTrainer:
    """Individual model trainer"""
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model_class = self._get_model_class()
        self.default_params = self._get_default_params()
    
    def _get_model_class(self):
        """Get model class by name"""
        model_classes = {
            'random_forest': RandomForestRegressor,
            'gradient_boosting': GradientBoostingRegressor,
            'linear_regression': LinearRegression,
            'ridge': Ridge
        }
        return model_classes.get(self.model_name, RandomForestRegressor)
    
    def _get_default_params(self) -> Dict[str, Any]:
        """Get default parameters for model"""
        defaults = {
            'random_forest': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2,
                'random_state': 42
            },
            'gradient_boosting': {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 6,
                'random_state': 42
            },
            'linear_regression': {},
            'ridge': {
                'alpha': 1.0,
                'random_state': 42
            }
        }
        return defaults.get(self.model_name, {})
    
    def optimize_hyperparameters(self, X: pd.DataFrame, y: pd.Series, 
                                config: TrainingConfig) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna"""
        try:
            def objective(trial):
                params = self._suggest_params(trial)
                model = self.model_class(**params)
                
                # Use time series split for validation
                tscv = TimeSeriesSplit(n_splits=config.cv_folds)
                scores = cross_val_score(model, X, y, cv=tscv, 
                                       scoring='neg_mean_squared_error', n_jobs=-1)
                return -scores.mean()
            
            study = optuna.create_study(direction='minimize')
            study.optimize(objective, n_trials=config.hyperopt_trials, timeout=120)
            
            best_params = study.best_params
            logging.info(f"Best params for {self.model_name}: {best_params}")
            return best_params
            
        except Exception as e:
            logging.error(f"Hyperparameter optimization failed for {self.model_name}: {e}")
            return self.default_params
    
    def _suggest_params(self, trial) -> Dict[str, Any]:
        """Suggest hyperparameters for optimization"""
        if self.model_name == 'random_forest':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                'max_depth': trial.suggest_int('max_depth', 5, 20),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5),
                'random_state': 42
            }
        elif self.model_name == 'gradient_boosting':
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'random_state': 42
            }
        elif self.model_name == 'ridge':
            return {
                'alpha': trial.suggest_float('alpha', 0.1, 10.0),
                'random_state': 42
            }
        else:
            return self.default_params
    
    def train(self, X: pd.DataFrame, y: pd.Series, 
              config: TrainingConfig) -> TrainingResult:
        """Train the model"""
        start_time = time.time()
        
        try:
            # Split data
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=config.validation_split, 
                shuffle=False  # Important for time series
            )
            
            # Optimize hyperparameters
            best_params = self.optimize_hyperparameters(X_train, y_train, config)
            
            # Train final model
            model = self.model_class(**best_params)
            model.fit(X_train, y_train)
            
            # Evaluate
            train_score = model.score(X_train, y_train)
            val_score = model.score(X_val, y_val)
            
            # Cross-validation
            tscv = TimeSeriesSplit(n_splits=config.cv_folds)
            cv_scores = cross_val_score(model, X, y, cv=tscv, scoring='r2')
            cv_score = cv_scores.mean()
            
            # Predictions for detailed metrics
            y_pred = model.predict(X_val)
            mse = mean_squared_error(y_val, y_pred)
            mae = mean_absolute_error(y_val, y_pred)
            
            # Feature importance
            feature_importance = {}
            if hasattr(model, 'feature_importances_'):
                for feature, importance in zip(X.columns, model.feature_importances_):
                    feature_importance[feature] = float(importance)
            elif hasattr(model, 'coef_'):
                for feature, coef in zip(X.columns, model.coef_):
                    feature_importance[feature] = float(abs(coef))
            
            training_time = time.time() - start_time
            
            # Create version string
            version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            result = TrainingResult(
                model_name=self.model_name,
                model_version=version,
                training_score=train_score,
                validation_score=val_score,
                cross_val_score=cv_score,
                feature_importance=feature_importance,
                training_time=training_time,
                sample_count=len(X),
                parameters=best_params,
                metrics={
                    'mse': mse,
                    'mae': mae,
                    'rmse': np.sqrt(mse)
                },
                success=True
            )
            
            # Save model
            model_path = Path(f"models/{self.model_name}_{version}.pkl")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(model, model_path)
            
            logging.info(f"Model {self.model_name} trained successfully. "
                        f"Validation score: {val_score:.4f}, CV score: {cv_score:.4f}")
            
            return result
            
        except Exception as e:
            logging.error(f"Training failed for {self.model_name}: {e}")
            return TrainingResult(
                model_name=self.model_name,
                model_version="failed",
                training_score=0.0,
                validation_score=0.0,
                cross_val_score=0.0,
                feature_importance={},
                training_time=time.time() - start_time,
                sample_count=0,
                parameters={},
                metrics={},
                success=False,
                error_message=str(e)
            )

class AutomatedModelTrainer:
    """Main automated training system"""
    
    def __init__(self, config: TrainingConfig = None):
        self.config = config or TrainingConfig()
        self.model_registry = ModelRegistry()
        self.is_running = False
        self.scheduler_thread = None
        
        # Data sources
        self.data_db_path = Path("data/market_data.db")
        self.trades_db_path = Path("data/trades.db")
        
        # Feature engineering
        self.feature_engine = FeatureEngineering()
        self.scaler = StandardScaler()
        
        # Performance tracking
        self.training_history = []
        
        logging.info("Automated Model Trainer initialized")
    
    def _load_market_data(self, lookback_days: int = 30) -> pd.DataFrame:
        """Load market data for training"""
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            with sqlite3.connect(self.data_db_path) as conn:
                query = """
                    SELECT timestamp, open, high, low, close, volume
                    FROM ohlc_1m 
                    WHERE timestamp >= ?
                    ORDER BY timestamp
                """
                df = pd.read_sql_query(query, conn, params=(cutoff_date,))
                
            if df.empty:
                logging.warning("No market data found")
                return pd.DataFrame()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            logging.info(f"Loaded {len(df)} market data records")
            return df
            
        except Exception as e:
            logging.error(f"Failed to load market data: {e}")
            return pd.DataFrame()
    
    def _load_trade_data(self, lookback_days: int = 30) -> pd.DataFrame:
        """Load trade data for training labels"""
        try:
            cutoff_date = datetime.now() - timedelta(days=lookback_days)
            
            with sqlite3.connect(self.trades_db_path) as conn:
                query = """
                    SELECT timestamp, symbol, entry_price, exit_price, 
                           profit_loss, trade_type, duration_minutes
                    FROM trades 
                    WHERE timestamp >= ? AND status = 'completed'
                    ORDER BY timestamp
                """
                df = pd.read_sql_query(query, conn, params=(cutoff_date,))
                
            if df.empty:
                logging.warning("No trade data found")
                return pd.DataFrame()
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['profit_pct'] = (df['exit_price'] - df['entry_price']) / df['entry_price']
            
            logging.info(f"Loaded {len(df)} completed trades")
            return df
            
        except Exception as e:
            logging.error(f"Failed to load trade data: {e}")
            return pd.DataFrame()
    
    def _prepare_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare features and target for training"""
        # Load data
        market_data = self._load_market_data()
        trade_data = self._load_trade_data()
        
        if market_data.empty:
            return pd.DataFrame(), pd.Series()
        
        # Engineer features
        features = self.feature_engine.create_technical_features(market_data)
        features = self.feature_engine.create_market_regime_features(features)
        
        # Create target variable (next period return)
        features['target'] = features['returns'].shift(-1)
        
        # If we have trade data, use actual trade outcomes
        if not trade_data.empty:
            # Align trade outcomes with market data
            trade_outcomes = trade_data.set_index('timestamp')['profit_pct'].resample('1min').mean()
            features['trade_outcome'] = trade_outcomes
            features['target'] = features['trade_outcome'].fillna(features['target'])
        
        # Clean and select features
        feature_cols = [col for col in features.columns 
                       if col not in ['target', 'trade_outcome'] 
                       and not col.startswith('close_lag_')  # Avoid data leakage
                       and features[col].dtype in ['int64', 'float64']]
        
        X = features[feature_cols].dropna()
        y = features.loc[X.index, 'target'].dropna()
        
        # Align X and y
        common_index = X.index.intersection(y.index)
        X = X.loc[common_index]
        y = y.loc[common_index]
        
        logging.info(f"Prepared {len(X)} samples with {len(X.columns)} features")
        return X, y
    
    def _should_retrain_model(self, model_name: str) -> bool:
        """Check if model needs retraining"""
        try:
            # Get current model performance
            current_model = self.model_registry.get_model(model_name)
            if not current_model:
                logging.info(f"No existing model found for {model_name}, training new one")
                return True
            
            # Check last training date
            metadata = self.model_registry.get_model_metadata(model_name)
            if not metadata:
                return True
            
            last_trained = datetime.fromisoformat(metadata.created_at)
            days_since_training = (datetime.now() - last_trained).days
            
            # Retrain if model is old
            if days_since_training > 7:  # Weekly retraining
                logging.info(f"Model {model_name} is {days_since_training} days old, retraining")
                return True
            
            # Check performance degradation
            recent_performance = self._evaluate_recent_performance(model_name)
            if recent_performance and recent_performance < (metadata.validation_score - self.config.retrain_threshold):
                logging.info(f"Model {model_name} performance degraded, retraining")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Error checking retrain condition for {model_name}: {e}")
            return True
    
    def _evaluate_recent_performance(self, model_name: str) -> Optional[float]:
        """Evaluate recent model performance"""
        try:
            # Get recent market data
            recent_data = self._load_market_data(lookback_days=7)
            if recent_data.empty:
                return None
            
            # Prepare features
            features = self.feature_engine.create_technical_features(recent_data)
            features = self.feature_engine.create_market_regime_features(features)
            
            # Get model
            model = self.model_registry.get_model(model_name)
            if not model:
                return None
            
            # Select features (match training features)
            feature_cols = [col for col in features.columns 
                           if col not in ['target', 'trade_outcome', 'returns']
                           and features[col].dtype in ['int64', 'float64']]
            
            X_recent = features[feature_cols].dropna()
            y_recent = features.loc[X_recent.index, 'returns'].shift(-1).dropna()
            
            # Align data
            common_index = X_recent.index.intersection(y_recent.index)
            if len(common_index) < 10:  # Need minimum samples
                return None
            
            X_recent = X_recent.loc[common_index]
            y_recent = y_recent.loc[common_index]
            
            # Evaluate
            score = model.score(X_recent, y_recent)
            return score
            
        except Exception as e:
            logging.error(f"Error evaluating recent performance for {model_name}: {e}")
            return None
    
    def train_model(self, model_name: str) -> TrainingResult:
        """Train a single model"""
        logging.info(f"Starting training for model: {model_name}")
        
        # Prepare data
        X, y = self._prepare_training_data()
        
        if X.empty or len(X) < self.config.min_samples:
            logging.warning(f"Insufficient data for training {model_name}: {len(X)} samples")
            return TrainingResult(
                model_name=model_name,
                model_version="failed",
                training_score=0.0,
                validation_score=0.0,
                cross_val_score=0.0,
                feature_importance={},
                training_time=0.0,
                sample_count=len(X),
                parameters={},
                metrics={},
                success=False,
                error_message="Insufficient training data"
            )
        
        # Scale features
        X_scaled = pd.DataFrame(
            self.scaler.fit_transform(X),
            columns=X.columns,
            index=X.index
        )
        
        # Train model
        trainer = ModelTrainer(model_name)
        result = trainer.train(X_scaled, y, self.config)
        
        # Register model if successful
        if result.success:
            try:
                model_path = Path(f"models/{model_name}_{result.model_version}.pkl")
                
                metadata = ModelMetadata(
                    name=model_name,
                    version=result.model_version,
                    model_type="regression",
                    framework="sklearn",
                    file_path=str(model_path),
                    training_score=result.training_score,
                    validation_score=result.validation_score,
                    feature_count=len(X.columns),
                    sample_count=result.sample_count,
                    parameters=result.parameters,
                    created_at=datetime.now().isoformat(),
                    metrics=result.metrics
                )
                
                self.model_registry.register_model(metadata, model_path)
                logging.info(f"Model {model_name} registered successfully")
                
            except Exception as e:
                logging.error(f"Failed to register model {model_name}: {e}")
        
        # Save training result
        self.training_history.append(result)
        
        return result
    
    def train_all_models(self) -> List[TrainingResult]:
        """Train all configured models"""
        results = []
        
        for model_name in self.config.models_to_train:
            if self._should_retrain_model(model_name):
                result = self.train_model(model_name)
                results.append(result)
            else:
                logging.info(f"Skipping {model_name} - no retraining needed")
        
        return results
    
    def _scheduled_training(self):
        """Scheduled training job"""
        try:
            logging.info("Starting scheduled training cycle")
            results = self.train_all_models()
            
            # Log results
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]
            
            logging.info(f"Training cycle completed: {len(successful)} successful, {len(failed)} failed")
            
            # Save training report
            self._save_training_report(results)
            
        except Exception as e:
            logging.error(f"Scheduled training failed: {e}")
    
    def _save_training_report(self, results: List[TrainingResult]):
        """Save training report to file"""
        try:
            report_path = Path("logs/training_reports")
            report_path.mkdir(parents=True, exist_ok=True)
            
            report_file = report_path / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            report_data = {
                'timestamp': datetime.now().isoformat(),
                'total_models': len(results),
                'successful': len([r for r in results if r.success]),
                'failed': len([r for r in results if not r.success]),
                'results': []
            }
            
            for result in results:
                result_data = {
                    'model_name': result.model_name,
                    'model_version': result.model_version,
                    'success': result.success,
                    'training_score': result.training_score,
                    'validation_score': result.validation_score,
                    'cross_val_score': result.cross_val_score,
                    'training_time': result.training_time,
                    'sample_count': result.sample_count,
                    'error_message': result.error_message
                }
                report_data['results'].append(result_data)
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            logging.info(f"Training report saved: {report_file}")
            
        except Exception as e:
            logging.error(f"Failed to save training report: {e}")
    
    def start_scheduler(self, interval_hours: int = 24):
        """Start automated training scheduler"""
        if self.is_running:
            logging.warning("Training scheduler already running")
            return
        
        logging.info(f"Starting training scheduler (every {interval_hours} hours)")
        
        # Schedule training
        schedule.every(interval_hours).hours.do(self._scheduled_training)
        
        # Run scheduler in thread
        def run_scheduler():
            self.is_running = True
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler)
        self.scheduler_thread.start()
        
        logging.info("Training scheduler started")
    
    def stop_scheduler(self):
        """Stop automated training scheduler"""
        logging.info("Stopping training scheduler")
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=30)
        
        schedule.clear()
        logging.info("Training scheduler stopped")
    
    def get_training_status(self) -> Dict[str, Any]:
        """Get current training status"""
        recent_results = self.training_history[-10:] if self.training_history else []
        
        status = {
            'is_running': self.is_running,
            'total_training_runs': len(self.training_history),
            'recent_results': len(recent_results),
            'recent_success_rate': len([r for r in recent_results if r.success]) / len(recent_results) if recent_results else 0,
            'models_configured': len(self.config.models_to_train),
            'last_training': None
        }
        
        if self.training_history:
            last_result = self.training_history[-1]
            status['last_training'] = {
                'timestamp': datetime.now().isoformat(),  # Approximate
                'model': last_result.model_name,
                'success': last_result.success,
                'validation_score': last_result.validation_score
            }
        
        return status

async def main():
    """Test the automated trainer"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create trainer
    config = TrainingConfig(
        min_samples=50,  # Lower for testing
        retrain_threshold=0.1,
        hyperopt_trials=10,  # Faster for testing
        models_to_train=['random_forest', 'ridge']
    )
    
    trainer = AutomatedModelTrainer(config)
    
    try:
        # Test training
        logging.info("Testing automated training...")
        results = trainer.train_all_models()
        
        # Show results
        for result in results:
            print(f"\nModel: {result.model_name}")
            print(f"Success: {result.success}")
            print(f"Validation Score: {result.validation_score:.4f}")
            print(f"Training Time: {result.training_time:.2f}s")
            print(f"Sample Count: {result.sample_count}")
            if result.error_message:
                print(f"Error: {result.error_message}")
        
        # Show status
        status = trainer.get_training_status()
        print(f"\nTraining Status: {json.dumps(status, indent=2)}")
        
        # Test scheduler (briefly)
        print("\nTesting scheduler for 30 seconds...")
        trainer.start_scheduler(interval_hours=24)
        await asyncio.sleep(30)
        trainer.stop_scheduler()
        
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        trainer.stop_scheduler()

if __name__ == "__main__":
    asyncio.run(main())
