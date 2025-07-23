#!/usr/bin/env python3
"""
AI Gold Scalper - Adaptive Learning System
Continuously learns from trading results and improves model performance
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

# Import our model registry
from model_registry import ModelRegistry, ModelMetadata

@dataclass
class LearningConfig:
    """Configuration for adaptive learning"""
    min_trades_for_update: int = 50
    retraining_frequency_hours: int = 24
    performance_threshold: float = 0.6  # Min win rate to consider model good
    feature_importance_threshold: float = 0.01
    max_features_to_keep: int = 20
    ensemble_models_count: int = 3
    validation_split: float = 0.2

class FeatureEngineering:
    """Advanced feature engineering for trading signals"""
    
    def __init__(self):
        self.feature_cache = {}
        
    def create_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create technical analysis features from price data"""
        features_df = df.copy()
        
        # Price-based features
        features_df['price_change'] = df['close'].pct_change()
        features_df['price_change_2'] = df['close'].pct_change(2)
        features_df['price_change_5'] = df['close'].pct_change(5)
        
        # Volume features
        if 'volume' in df.columns:
            features_df['volume_change'] = df['volume'].pct_change()
            features_df['price_volume_trend'] = features_df['price_change'] * df['volume']
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            features_df[f'ma_{window}'] = df['close'].rolling(window).mean()
            features_df[f'ma_{window}_ratio'] = df['close'] / features_df[f'ma_{window}']
        
        # Bollinger Bands
        bb_window = 20
        bb_std = 2
        features_df['bb_middle'] = df['close'].rolling(bb_window).mean()
        bb_std_val = df['close'].rolling(bb_window).std()
        features_df['bb_upper'] = features_df['bb_middle'] + (bb_std_val * bb_std)
        features_df['bb_lower'] = features_df['bb_middle'] - (bb_std_val * bb_std)
        features_df['bb_position'] = (df['close'] - features_df['bb_lower']) / (features_df['bb_upper'] - features_df['bb_lower'])
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        features_df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        features_df['macd'] = exp1 - exp2
        features_df['macd_signal'] = features_df['macd'].ewm(span=9).mean()
        features_df['macd_histogram'] = features_df['macd'] - features_df['macd_signal']
        
        # Volatility
        features_df['volatility'] = df['close'].rolling(20).std()
        features_df['volatility_ratio'] = features_df['volatility'] / features_df['volatility'].rolling(50).mean()
        
        # Support/Resistance levels
        features_df['high_20'] = df['high'].rolling(20).max()
        features_df['low_20'] = df['low'].rolling(20).min()
        features_df['support_distance'] = (df['close'] - features_df['low_20']) / df['close']
        features_df['resistance_distance'] = (features_df['high_20'] - df['close']) / df['close']
        
        # Time-based features
        if 'timestamp' in df.columns:
            df_time = pd.to_datetime(df['timestamp'])
            features_df['hour'] = df_time.dt.hour
            features_df['day_of_week'] = df_time.dt.dayofweek
            features_df['is_market_hours'] = ((df_time.dt.hour >= 9) & (df_time.dt.hour <= 16)).astype(int)
        
        return features_df
    
    def create_sentiment_features(self, df: pd.DataFrame, trade_logs_db: str) -> pd.DataFrame:
        """Create sentiment-based features from recent trading outcomes"""
        features_df = df.copy()
        
        try:
            conn = sqlite3.connect(trade_logs_db)
            
            # Recent win rate
            recent_trades = pd.read_sql_query("""
                SELECT outcome, profit_loss, timestamp 
                FROM trade_executions 
                WHERE timestamp >= datetime('now', '-24 hours')
                ORDER BY timestamp DESC
            """, conn)
            
            if not recent_trades.empty:
                features_df['recent_win_rate'] = (recent_trades['outcome'] == 'win').mean()
                features_df['recent_avg_profit'] = recent_trades['profit_loss'].mean()
                features_df['recent_volatility'] = recent_trades['profit_loss'].std()
                features_df['trades_last_hour'] = len(recent_trades[
                    recent_trades['timestamp'] >= (datetime.now() - timedelta(hours=1)).isoformat()
                ])
            else:
                features_df['recent_win_rate'] = 0.5
                features_df['recent_avg_profit'] = 0.0
                features_df['recent_volatility'] = 0.0
                features_df['trades_last_hour'] = 0
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️  Could not create sentiment features: {e}")
            features_df['recent_win_rate'] = 0.5
            features_df['recent_avg_profit'] = 0.0
            features_df['recent_volatility'] = 0.0
            features_df['trades_last_hour'] = 0
        
        return features_df
    
    def select_best_features(self, X: pd.DataFrame, y: pd.Series, max_features: int = 20) -> List[str]:
        """Select the most important features using multiple methods"""
        from sklearn.feature_selection import SelectKBest, f_classif, RFE
        from sklearn.ensemble import RandomForestClassifier
        
        # Remove non-numeric and infinity values
        X_clean = X.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Method 1: Statistical test
        selector_stats = SelectKBest(score_func=f_classif, k=min(max_features, X_clean.shape[1]))
        selector_stats.fit(X_clean, y)
        stats_features = X_clean.columns[selector_stats.get_support()].tolist()
        
        # Method 2: Random Forest importance
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_clean, y)
        rf_importance = pd.DataFrame({
            'feature': X_clean.columns,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        rf_features = rf_importance.head(max_features)['feature'].tolist()
        
        # Method 3: Recursive Feature Elimination
        rfe = RFE(estimator=rf, n_features_to_select=min(max_features, X_clean.shape[1]))
        rfe.fit(X_clean, y)
        rfe_features = X_clean.columns[rfe.support_].tolist()
        
        # Combine and rank features
        feature_votes = {}
        for feature in stats_features:
            feature_votes[feature] = feature_votes.get(feature, 0) + 3
        for feature in rf_features:
            feature_votes[feature] = feature_votes.get(feature, 0) + 2
        for feature in rfe_features:
            feature_votes[feature] = feature_votes.get(feature, 0) + 1
        
        # Sort by votes and return top features
        best_features = sorted(feature_votes.items(), key=lambda x: x[1], reverse=True)
        selected_features = [feature for feature, _ in best_features[:max_features]]
        
        print(f"✅ Selected {len(selected_features)} best features")
        print(f"   Top 5: {selected_features[:5]}")
        
        return selected_features

class AdaptiveLearningSystem:
    """Main adaptive learning system that continuously improves models"""
    
    def __init__(self, trade_logs_db: str = "scripts/monitoring/trade_logs.db", 
                 config: LearningConfig = None):
        self.trade_logs_db = trade_logs_db
        self.config = config or LearningConfig()
        self.model_registry = ModelRegistry("models")
        self.feature_engineer = FeatureEngineering()
        self.scaler = StandardScaler()
        
        # Create learning database
        self.learning_db = "models/adaptive_learning.db"
        self._init_learning_database()
        
    def _init_learning_database(self):
        """Initialize database for learning system"""
        os.makedirs("models", exist_ok=True)
        
        conn = sqlite3.connect(self.learning_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_start TIMESTAMP NOT NULL,
            session_end TIMESTAMP,
            trades_analyzed INTEGER NOT NULL,
            new_model_created BOOLEAN DEFAULT 0,
            model_id TEXT,
            performance_improvement REAL DEFAULT 0.0,
            features_selected TEXT,  -- JSON
            learning_notes TEXT DEFAULT ""
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_importance_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            feature_name TEXT NOT NULL,
            importance_score REAL NOT NULL,
            model_id TEXT NOT NULL,
            selection_method TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def gather_training_data(self, lookback_hours: int = 48) -> Tuple[pd.DataFrame, pd.Series]:
        """Gather recent trading data for training"""
        try:
            conn = sqlite3.connect(self.trade_logs_db)
            
            # Get recent trades with their signals
            query = """
            SELECT 
                te.timestamp,
                te.signal_type,
                te.entry_price,
                te.exit_price,
                te.profit_loss,
                te.outcome,
                ts.confidence,
                ts.technical_indicators,
                ts.market_conditions
            FROM trade_executions te
            JOIN trade_signals ts ON te.signal_id = ts.id
            WHERE te.timestamp >= datetime('now', '-{} hours')
            ORDER BY te.timestamp ASC
            """.format(lookback_hours)
            
            trades_df = pd.read_sql_query(query, conn)
            conn.close()
            
            if trades_df.empty:
                print("⚠️  No recent trades found for training")
                return None, None
            
            # Create features from trade data
            features_df = self._create_features_from_trades(trades_df)
            
            # Create target variable (1 for successful trades, 0 for losses)
            y = (trades_df['outcome'] == 'win').astype(int)
            
            print(f"✅ Gathered {len(features_df)} trades for training")
            print(f"   Win rate: {y.mean():.2%}")
            
            return features_df, y
            
        except Exception as e:
            print(f"❌ Error gathering training data: {e}")
            return None, None
    
    def _create_features_from_trades(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Create features from trade execution data"""
        features = []
        
        for _, trade in trades_df.iterrows():
            feature_row = {}
            
            # Basic trade features
            feature_row['signal_type_buy'] = 1 if trade['signal_type'] == 'buy' else 0
            feature_row['signal_type_sell'] = 1 if trade['signal_type'] == 'sell' else 0
            feature_row['confidence'] = trade['confidence']
            feature_row['entry_price'] = trade['entry_price']
            
            # Parse technical indicators
            try:
                tech_indicators = json.loads(trade['technical_indicators'])
                for key, value in tech_indicators.items():
                    if isinstance(value, (int, float)):
                        feature_row[f'tech_{key}'] = value
            except:
                pass
            
            # Parse market conditions
            try:
                market_conditions = json.loads(trade['market_conditions'])
                for key, value in market_conditions.items():
                    if isinstance(value, (int, float)):
                        feature_row[f'market_{key}'] = value
            except:
                pass
            
            # Time-based features
            timestamp = pd.to_datetime(trade['timestamp'])
            feature_row['hour'] = timestamp.hour
            feature_row['day_of_week'] = timestamp.dayofweek
            feature_row['is_market_hours'] = 1 if 9 <= timestamp.hour <= 16 else 0
            
            features.append(feature_row)
        
        features_df = pd.DataFrame(features).fillna(0)
        
        # Add recent performance features
        features_df = self._add_recent_performance_features(features_df, trades_df)
        
        return features_df
    
    def _add_recent_performance_features(self, features_df: pd.DataFrame, trades_df: pd.DataFrame) -> pd.DataFrame:
        """Add features based on recent performance"""
        features_df = features_df.copy()
        
        # Calculate rolling statistics
        trades_df['profit_loss_roll_mean_5'] = trades_df['profit_loss'].rolling(5, min_periods=1).mean()
        trades_df['profit_loss_roll_std_5'] = trades_df['profit_loss'].rolling(5, min_periods=1).std().fillna(0)
        trades_df['win_rate_roll_10'] = (trades_df['outcome'] == 'win').rolling(10, min_periods=1).mean()
        
        # Add to features
        features_df['recent_avg_profit'] = trades_df['profit_loss_roll_mean_5'].values
        features_df['recent_profit_volatility'] = trades_df['profit_loss_roll_std_5'].values
        features_df['recent_win_rate'] = trades_df['win_rate_roll_10'].values
        
        return features_df
    
    def train_improved_model(self, X: pd.DataFrame, y: pd.Series) -> Optional[str]:
        """Train an improved model using the latest data"""
        if len(X) < self.config.min_trades_for_update:
            print(f"⚠️  Not enough trades ({len(X)}) for model update (min: {self.config.min_trades_for_update})")
            return None
        
        # Feature selection
        selected_features = self.feature_engineer.select_best_features(
            X, y, self.config.max_features_to_keep
        )
        X_selected = X[selected_features]
        
        # Clean data
        X_clean = X_selected.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_clean, y, test_size=self.config.validation_split, random_state=42, stratify=y
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train multiple model types
        models_to_try = {
            'random_forest': RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42),
            'gradient_boost': GradientBoostingClassifier(n_estimators=100, max_depth=6, random_state=42),
            'logistic': LogisticRegression(random_state=42, max_iter=1000)
        }
        
        best_model = None
        best_score = 0
        best_name = ""
        
        model_results = {}
        
        for name, model in models_to_try.items():
            try:
                if name == 'logistic':
                    model.fit(X_train_scaled, y_train)
                    y_pred = model.predict(X_test_scaled)
                else:
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                
                accuracy = accuracy_score(y_test, y_pred)
                model_results[name] = accuracy
                
                if accuracy > best_score:
                    best_score = accuracy
                    best_model = model
                    best_name = name
                    
                print(f"   {name}: {accuracy:.3f}")
                
            except Exception as e:
                print(f"   {name}: Failed - {e}")
        
        if best_model is None:
            print("❌ No model could be trained successfully")
            return None
        
        print(f"🏆 Best model: {best_name} (accuracy: {best_score:.3f})")
        
        # Create model metadata
        metadata = ModelMetadata(
            model_id="",
            name=f"Adaptive {best_name.title()} Model",
            version=f"auto_{datetime.now().strftime('%Y%m%d_%H%M')}",
            created_at=datetime.now(),
            model_type="sklearn",
            features_used=selected_features,
            hyperparameters=best_model.get_params(),
            training_data_hash=str(hash(str(X_clean.values.tobytes()))),
            file_path="",
            accuracy=best_score,
            win_rate=y.mean(),  # Use training win rate as baseline
            profit_factor=1.0,  # Will be updated with real trading
        )
        
        # Register the model
        model_id = self.model_registry.register_model(best_model, metadata)
        
        # Save the scaler alongside the model
        scaler_path = f"models/stored_models/{model_id}_scaler.pkl"
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Log learning session
        self._log_learning_session(len(X), model_id, selected_features, best_score)
        
        return model_id
    
    def evaluate_model_performance(self, model_id: str, lookback_hours: int = 24) -> Dict[str, float]:
        """Evaluate model performance on recent trades"""
        try:
            conn = sqlite3.connect(self.trade_logs_db)
            
            # Get recent trades where this model was used
            query = """
            SELECT outcome, profit_loss, confidence
            FROM trade_executions te
            JOIN trade_signals ts ON te.signal_id = ts.id
            WHERE te.timestamp >= datetime('now', '-{} hours')
            AND ts.model_id = ?
            """.format(lookback_hours)
            
            trades_df = pd.read_sql_query(query, conn, params=[model_id])
            conn.close()
            
            if trades_df.empty:
                return {"error": "No trades found for this model"}
            
            # Calculate performance metrics
            wins = (trades_df['outcome'] == 'win').sum()
            total_trades = len(trades_df)
            win_rate = wins / total_trades
            
            profits = trades_df[trades_df['outcome'] == 'win']['profit_loss'].sum()
            losses = abs(trades_df[trades_df['outcome'] == 'loss']['profit_loss'].sum())
            profit_factor = profits / losses if losses > 0 else float('inf')
            
            avg_confidence = trades_df['confidence'].mean()
            
            metrics = {
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_trades': total_trades,
                'total_profit': trades_df['profit_loss'].sum(),
                'avg_confidence': avg_confidence
            }
            
            # Update model performance in registry
            self.model_registry.update_model_performance(model_id, metrics)
            
            return metrics
            
        except Exception as e:
            print(f"❌ Error evaluating model performance: {e}")
            return {"error": str(e)}
    
    def run_adaptive_learning_cycle(self) -> Dict[str, Any]:
        """Run a complete adaptive learning cycle"""
        print("🧠 Starting adaptive learning cycle...")
        
        cycle_results = {
            'start_time': datetime.now(),
            'trades_analyzed': 0,
            'new_model_created': False,
            'model_id': None,
            'performance_improvement': 0.0,
            'errors': []
        }
        
        try:
            # 1. Gather training data
            X, y = self.gather_training_data(self.config.retraining_frequency_hours)
            
            if X is None or len(X) < self.config.min_trades_for_update:
                cycle_results['errors'].append("Insufficient training data")
                return cycle_results
            
            cycle_results['trades_analyzed'] = len(X)
            
            # 2. Check if current model needs improvement
            current_win_rate = y.mean()
            if current_win_rate >= self.config.performance_threshold:
                # Get current active model performance
                active_model, active_metadata = self.model_registry.get_active_model()
                
                if active_metadata and active_metadata.win_rate >= current_win_rate:
                    print(f"✅ Current model performing well (win rate: {active_metadata.win_rate:.2%})")
                    return cycle_results
            
            # 3. Train improved model
            print("🔄 Training improved model...")
            new_model_id = self.train_improved_model(X, y)
            
            if new_model_id:
                cycle_results['new_model_created'] = True
                cycle_results['model_id'] = new_model_id
                
                # 4. Evaluate performance improvement
                new_metadata = self.model_registry.get_model_metadata(new_model_id)
                active_model, active_metadata = self.model_registry.get_active_model()
                
                if active_metadata:
                    improvement = new_metadata.accuracy - active_metadata.accuracy
                    cycle_results['performance_improvement'] = improvement
                    
                    if improvement > 0.02:  # 2% improvement threshold
                        print(f"🎯 Significant improvement detected ({improvement:.2%})")
                        print(f"   Setting new model as active...")
                        self.model_registry.set_active_model(new_model_id)
                    else:
                        print(f"📊 Model improvement marginal ({improvement:.2%})")
                else:
                    # No active model, set this as active
                    self.model_registry.set_active_model(new_model_id)
                    print("🎯 Set new model as active (no previous active model)")
            
            cycle_results['end_time'] = datetime.now()
            
        except Exception as e:
            cycle_results['errors'].append(str(e))
            print(f"❌ Error in learning cycle: {e}")
        
        return cycle_results
    
    def _log_learning_session(self, trades_count: int, model_id: str, 
                             features_used: List[str], performance: float):
        """Log the learning session to database"""
        conn = sqlite3.connect(self.learning_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO learning_sessions 
        (session_start, trades_analyzed, new_model_created, model_id, 
         performance_improvement, features_selected)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(), trades_count, True, model_id,
            performance, json.dumps(features_used)
        ))
        
        conn.commit()
        conn.close()
    
    def schedule_learning(self, run_immediately: bool = False) -> bool:
        """Schedule or run adaptive learning based on configuration"""
        if run_immediately:
            results = self.run_adaptive_learning_cycle()
            print(f"📊 Learning cycle completed:")
            print(f"   Trades analyzed: {results['trades_analyzed']}")
            print(f"   New model created: {results['new_model_created']}")
            if results['new_model_created']:
                print(f"   Model ID: {results['model_id']}")
                print(f"   Performance improvement: {results['performance_improvement']:.2%}")
            return results['new_model_created']
        
        # Check if it's time for scheduled learning
        conn = sqlite3.connect(self.learning_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT MAX(session_start) 
        FROM learning_sessions 
        WHERE new_model_created = 1
        ''')
        
        last_session = cursor.fetchone()[0]
        conn.close()
        
        if last_session:
            last_session_time = datetime.fromisoformat(last_session)
            hours_since = (datetime.now() - last_session_time).total_seconds() / 3600
            
            if hours_since >= self.config.retraining_frequency_hours:
                print(f"⏰ Scheduled learning triggered ({hours_since:.1f}h since last session)")
                return self.schedule_learning(run_immediately=True)
        else:
            # No previous sessions, run now
            print("🎯 First learning session - running now")
            return self.schedule_learning(run_immediately=True)
        
        return False
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get summary of learning system performance"""
        conn = sqlite3.connect(self.learning_db)
        
        # Get learning sessions
        sessions_df = pd.read_sql_query('''
        SELECT * FROM learning_sessions 
        ORDER BY session_start DESC 
        LIMIT 10
        ''', conn)
        
        # Get model registry summary
        model_summary = self.model_registry.export_model_summary()
        
        conn.close()
        
        summary = {
            'total_learning_sessions': len(sessions_df),
            'models_created': sessions_df['new_model_created'].sum() if not sessions_df.empty else 0,
            'avg_trades_analyzed': sessions_df['trades_analyzed'].mean() if not sessions_df.empty else 0,
            'last_session': sessions_df.iloc[0]['session_start'] if not sessions_df.empty else None,
            'model_registry': model_summary,
            'recent_sessions': sessions_df.to_dict('records') if not sessions_df.empty else []
        }
        
        return summary

# Testing and demonstration
if __name__ == "__main__":
    print("🧠 AI Gold Scalper - Adaptive Learning System Test")
    print("=" * 60)
    
    # Initialize adaptive learning system
    learning_system = AdaptiveLearningSystem()
    
    # Run immediate learning cycle for testing
    results = learning_system.schedule_learning(run_immediately=True)
    
    # Display summary
    summary = learning_system.get_learning_summary()
    print(f"\n📊 Learning System Summary:")
    print(f"   Total Sessions: {summary['total_learning_sessions']}")
    print(f"   Models Created: {summary['models_created']}")
    print(f"   Avg Trades Analyzed: {summary['avg_trades_analyzed']:.1f}")
    
    # Show model registry status
    registry_summary = summary['model_registry']
    print(f"\n🤖 Model Registry Summary:")
    print(f"   Total Models: {registry_summary['total_models']}")
    print(f"   Active Models: {registry_summary['active_models']}")
    print(f"   Production Models: {registry_summary['production_models']}")
