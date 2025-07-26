#!/usr/bin/env python3
"""
AI Gold Scalper - Advanced Strategy Generator
Comprehensive framework for generating, testing, and optimizing trading strategies on local machine.

Features:
- Multi-timeframe strategy generation
- Technical indicator combinations
- ML-based pattern recognition
- Strategy performance optimization
- Automated backtesting pipeline
- Strategy ranking and selection
"""

import pandas as pd
import numpy as np
import talib
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# ML imports
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib

# Plotting
import matplotlib.pyplot as plt
import seaborn as sns

class StrategyGenerator:
    """Advanced strategy generation and optimization framework"""
    
    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = Path(data_dir)
        self.strategies = {}
        self.backtest_results = {}
        self.models = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Strategy templates
        self.strategy_templates = {
            'trend_following': self._generate_trend_strategies,
            'mean_reversion': self._generate_mean_reversion_strategies,
            'momentum': self._generate_momentum_strategies,
            'breakout': self._generate_breakout_strategies,
            'ml_ensemble': self._generate_ml_strategies,
            'multi_timeframe': self._generate_mtf_strategies
        }
        
        self.logger.info("Strategy Generator initialized")
    
    def load_data(self, timeframe: str = "1h") -> pd.DataFrame:
        """Load historical data for specified timeframe"""
        try:
            file_path = self.data_dir / f"XAU_{timeframe}_data.csv"
            if not file_path.exists():
                raise FileNotFoundError(f"Data file not found: {file_path}")
            
            df = pd.read_csv(file_path)
            
            # Standardize column names
            expected_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            if 'time' in df.columns:
                df = df.rename(columns={'time': 'timestamp'})
            
            # Convert timestamp
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            # Ensure numeric columns
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.dropna(inplace=True)
            
            self.logger.info(f"Loaded {len(df)} records for {timeframe} timeframe")
            return df
            
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add comprehensive technical indicators"""
        try:
            # Price-based indicators
            df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
            df['sma_200'] = talib.SMA(df['close'], timeperiod=200)
            df['ema_12'] = talib.EMA(df['close'], timeperiod=12)
            df['ema_26'] = talib.EMA(df['close'], timeperiod=26)
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
            
            # RSI
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            
            # Bollinger Bands
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = talib.STOCH(df['high'], df['low'], df['close'])
            
            # ADX
            df['adx'] = talib.ADX(df['high'], df['low'], df['close'])
            
            # Williams %R
            df['williams_r'] = talib.WILLR(df['high'], df['low'], df['close'])
            
            # CCI
            df['cci'] = talib.CCI(df['high'], df['low'], df['close'])
            
            # ATR
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'])
            
            # Volume indicators
            if 'volume' in df.columns:
                df['volume_sma'] = talib.SMA(df['volume'], timeperiod=20)
                df['ad'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])
                df['obv'] = talib.OBV(df['close'], df['volume'])
            
            # Price patterns
            df['price_change'] = df['close'].pct_change()
            df['volatility'] = df['price_change'].rolling(20).std()
            df['price_momentum'] = df['close'] / df['close'].shift(10) - 1
            
            # Support/Resistance levels
            df['resistance'] = df['high'].rolling(20).max()
            df['support'] = df['low'].rolling(20).min()
            df['support_resistance_ratio'] = (df['close'] - df['support']) / (df['resistance'] - df['support'])
            
            return df.dropna()
            
        except Exception as e:
            self.logger.error(f"Error adding technical indicators: {e}")
            return df
    
    def _generate_trend_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trend-following strategies"""
        strategies = {}
        
        # Strategy 1: SMA Crossover
        strategies['sma_crossover'] = {
            'name': 'SMA Crossover',
            'signals': self._sma_crossover_signals(df),
            'type': 'trend_following',
            'description': 'Buy when SMA20 crosses above SMA50, sell when opposite'
        }
        
        # Strategy 2: EMA + MACD
        strategies['ema_macd'] = {
            'name': 'EMA + MACD Trend',
            'signals': self._ema_macd_signals(df),
            'type': 'trend_following',
            'description': 'Trend following using EMA and MACD confirmation'
        }
        
        # Strategy 3: ADX Trend Strength
        strategies['adx_trend'] = {
            'name': 'ADX Trend Strength',
            'signals': self._adx_trend_signals(df),
            'type': 'trend_following',
            'description': 'Enter trends when ADX shows strong trend'
        }
        
        return strategies
    
    def _generate_mean_reversion_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate mean reversion strategies"""
        strategies = {}
        
        # Strategy 1: Bollinger Bands
        strategies['bollinger_reversion'] = {
            'name': 'Bollinger Band Reversion',
            'signals': self._bollinger_reversion_signals(df),
            'type': 'mean_reversion',
            'description': 'Buy oversold at lower band, sell overbought at upper band'
        }
        
        # Strategy 2: RSI Reversion
        strategies['rsi_reversion'] = {
            'name': 'RSI Mean Reversion',
            'signals': self._rsi_reversion_signals(df),
            'type': 'mean_reversion',
            'description': 'Buy when RSI oversold, sell when overbought'
        }
        
        return strategies
    
    def _generate_momentum_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate momentum-based strategies"""
        strategies = {}
        
        # Strategy 1: Price Momentum
        strategies['price_momentum'] = {
            'name': 'Price Momentum',
            'signals': self._price_momentum_signals(df),
            'type': 'momentum',
            'description': 'Follow strong price momentum with confirmation'
        }
        
        # Strategy 2: Volume-Price Momentum
        strategies['volume_momentum'] = {
            'name': 'Volume-Price Momentum',
            'signals': self._volume_momentum_signals(df),
            'type': 'momentum',
            'description': 'Momentum strategy with volume confirmation'
        }
        
        return strategies
    
    def _generate_breakout_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate breakout strategies"""
        strategies = {}
        
        # Strategy 1: Support/Resistance Breakout
        strategies['sr_breakout'] = {
            'name': 'Support/Resistance Breakout',
            'signals': self._sr_breakout_signals(df),
            'type': 'breakout',
            'description': 'Trade breakouts from support/resistance levels'
        }
        
        return strategies
    
    def _generate_ml_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate ML-based strategies"""
        strategies = {}
        
        # Prepare features for ML
        feature_columns = [
            'sma_20', 'sma_50', 'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower',
            'stoch_k', 'stoch_d', 'adx', 'williams_r', 'cci', 'atr', 'volatility',
            'price_momentum', 'support_resistance_ratio'
        ]
        
        # Create target variable (next period price direction)
        df['target'] = (df['close'].shift(-1) > df['close']).astype(int)
        
        # Prepare data
        ml_df = df[feature_columns + ['target']].dropna()
        
        if len(ml_df) > 100:  # Ensure sufficient data
            X = ml_df[feature_columns]
            y = ml_df['target']
            
            # Train models
            strategies['rf_classifier'] = self._train_rf_strategy(X, y, df)
            strategies['gb_classifier'] = self._train_gb_strategy(X, y, df)
            strategies['neural_network'] = self._train_nn_strategy(X, y, df)
        
        return strategies
    
    def _generate_mtf_strategies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate multi-timeframe strategies"""
        strategies = {}
        
        # Load different timeframes
        timeframes = ['4h', '1d']
        mtf_data = {}
        
        for tf in timeframes:
            mtf_data[tf] = self.load_data(tf)
            if not mtf_data[tf].empty:
                mtf_data[tf] = self.add_technical_indicators(mtf_data[tf])
        
        # Strategy: Higher timeframe trend with lower timeframe entry
        if mtf_data:
            strategies['mtf_trend'] = {
                'name': 'Multi-Timeframe Trend',
                'signals': self._mtf_trend_signals(df, mtf_data),
                'type': 'multi_timeframe',
                'description': 'Higher TF trend direction with lower TF entry timing'
            }
        
        return strategies
    
    # Signal generation methods
    def _sma_crossover_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate SMA crossover signals"""
        signals = pd.Series(0, index=df.index)
        
        # Buy when SMA20 crosses above SMA50
        buy_condition = (df['sma_20'] > df['sma_50']) & (df['sma_20'].shift(1) <= df['sma_50'].shift(1))
        sell_condition = (df['sma_20'] < df['sma_50']) & (df['sma_20'].shift(1) >= df['sma_50'].shift(1))
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _ema_macd_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate EMA + MACD signals"""
        signals = pd.Series(0, index=df.index)
        
        # Buy: Price above EMA12 and MACD crosses above signal
        buy_condition = (df['close'] > df['ema_12']) & \
                       (df['macd'] > df['macd_signal']) & \
                       (df['macd'].shift(1) <= df['macd_signal'].shift(1))
        
        # Sell: Price below EMA12 and MACD crosses below signal
        sell_condition = (df['close'] < df['ema_12']) & \
                        (df['macd'] < df['macd_signal']) & \
                        (df['macd'].shift(1) >= df['macd_signal'].shift(1))
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _adx_trend_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate ADX trend signals"""
        signals = pd.Series(0, index=df.index)
        
        # Strong trend when ADX > 25
        strong_trend = df['adx'] > 25
        
        # Buy: Strong uptrend
        buy_condition = strong_trend & (df['close'] > df['sma_20']) & (df['sma_20'] > df['sma_50'])
        # Sell: Strong downtrend  
        sell_condition = strong_trend & (df['close'] < df['sma_20']) & (df['sma_20'] < df['sma_50'])
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _bollinger_reversion_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate Bollinger Band reversion signals"""
        signals = pd.Series(0, index=df.index)
        
        # Buy at lower band (oversold)
        buy_condition = df['close'] <= df['bb_lower']
        # Sell at upper band (overbought)
        sell_condition = df['close'] >= df['bb_upper']
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _rsi_reversion_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate RSI reversion signals"""
        signals = pd.Series(0, index=df.index)
        
        # Buy when RSI oversold
        buy_condition = df['rsi'] <= 30
        # Sell when RSI overbought
        sell_condition = df['rsi'] >= 70
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _price_momentum_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate price momentum signals"""
        signals = pd.Series(0, index=df.index)
        
        # Strong positive momentum
        buy_condition = (df['price_momentum'] > 0.02) & (df['rsi'] > 50)
        # Strong negative momentum
        sell_condition = (df['price_momentum'] < -0.02) & (df['rsi'] < 50)
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _volume_momentum_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate volume-confirmed momentum signals"""
        signals = pd.Series(0, index=df.index)
        
        if 'volume' in df.columns:
            # High volume momentum
            high_volume = df['volume'] > df['volume_sma'] * 1.5
            
            buy_condition = (df['price_momentum'] > 0.01) & high_volume & (df['rsi'] > 45)
            sell_condition = (df['price_momentum'] < -0.01) & high_volume & (df['rsi'] < 55)
            
            signals[buy_condition] = 1
            signals[sell_condition] = -1
        
        return signals
    
    def _sr_breakout_signals(self, df: pd.DataFrame) -> pd.Series:
        """Generate support/resistance breakout signals"""
        signals = pd.Series(0, index=df.index)
        
        # Breakout above resistance
        buy_condition = (df['close'] > df['resistance']) & (df['close'].shift(1) <= df['resistance'].shift(1))
        # Breakdown below support
        sell_condition = (df['close'] < df['support']) & (df['close'].shift(1) >= df['support'].shift(1))
        
        signals[buy_condition] = 1
        signals[sell_condition] = -1
        
        return signals
    
    def _train_rf_strategy(self, X: pd.DataFrame, y: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """Train Random Forest strategy"""
        try:
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train model
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X_scaled, y)
            
            # Generate predictions
            predictions = rf.predict(X_scaled)
            
            # Convert to signals
            signals = pd.Series(0, index=df.index)
            valid_indices = X.index.intersection(signals.index)
            
            # Map predictions to signals
            signal_values = []
            for i, pred in enumerate(predictions):
                if i < len(valid_indices):
                    if pred == 1:
                        signal_values.append(1)  # Buy
                    else:
                        signal_values.append(-1)  # Sell
            
            signals.loc[valid_indices[:len(signal_values)]] = signal_values
            
            # Store model
            model_data = {
                'model': rf,
                'scaler': scaler,
                'feature_columns': X.columns.tolist(),
                'accuracy': accuracy_score(y, predictions)
            }
            self.models['rf_classifier'] = model_data
            
            return {
                'name': 'Random Forest Classifier',
                'signals': signals,
                'type': 'ml_ensemble',
                'description': f'ML Random Forest strategy (Accuracy: {model_data["accuracy"]:.3f})',
                'model_info': model_data
            }
            
        except Exception as e:
            self.logger.error(f"Error training RF strategy: {e}")
            return {}
    
    def _train_gb_strategy(self, X: pd.DataFrame, y: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """Train Gradient Boosting strategy"""
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            gb = GradientBoostingClassifier(n_estimators=100, random_state=42)
            gb.fit(X_scaled, y)
            
            predictions = gb.predict(X_scaled)
            
            signals = pd.Series(0, index=df.index)
            valid_indices = X.index.intersection(signals.index)
            
            signal_values = []
            for i, pred in enumerate(predictions):
                if i < len(valid_indices):
                    signal_values.append(1 if pred == 1 else -1)
            
            signals.loc[valid_indices[:len(signal_values)]] = signal_values
            
            model_data = {
                'model': gb,
                'scaler': scaler,
                'feature_columns': X.columns.tolist(),
                'accuracy': accuracy_score(y, predictions)
            }
            self.models['gb_classifier'] = model_data
            
            return {
                'name': 'Gradient Boosting Classifier',
                'signals': signals,
                'type': 'ml_ensemble',
                'description': f'ML Gradient Boosting strategy (Accuracy: {model_data["accuracy"]:.3f})',
                'model_info': model_data
            }
            
        except Exception as e:
            self.logger.error(f"Error training GB strategy: {e}")
            return {}
    
    def _train_nn_strategy(self, X: pd.DataFrame, y: pd.Series, df: pd.DataFrame) -> Dict[str, Any]:
        """Train Neural Network strategy"""
        try:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            nn = MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
            nn.fit(X_scaled, y)
            
            predictions = nn.predict(X_scaled)
            
            signals = pd.Series(0, index=df.index)
            valid_indices = X.index.intersection(signals.index)
            
            signal_values = []
            for i, pred in enumerate(predictions):
                if i < len(valid_indices):
                    signal_values.append(1 if pred == 1 else -1)
            
            signals.loc[valid_indices[:len(signal_values)]] = signal_values
            
            model_data = {
                'model': nn,
                'scaler': scaler,
                'feature_columns': X.columns.tolist(),
                'accuracy': accuracy_score(y, predictions)
            }
            self.models['neural_network'] = model_data
            
            return {
                'name': 'Neural Network Classifier',
                'signals': signals,
                'type': 'ml_ensemble',
                'description': f'ML Neural Network strategy (Accuracy: {model_data["accuracy"]:.3f})',
                'model_info': model_data
            }
            
        except Exception as e:
            self.logger.error(f"Error training NN strategy: {e}")
            return {}
    
    def _mtf_trend_signals(self, df: pd.DataFrame, mtf_data: Dict) -> pd.Series:
        """Generate multi-timeframe trend signals"""
        signals = pd.Series(0, index=df.index)
        
        # Use daily timeframe for trend direction
        if '1d' in mtf_data and not mtf_data['1d'].empty:
            daily_df = mtf_data['1d']
            
            # Determine daily trend
            daily_trend = pd.Series(0, index=daily_df.index)
            daily_uptrend = (daily_df['sma_20'] > daily_df['sma_50']) & (daily_df['macd'] > daily_df['macd_signal'])
            daily_downtrend = (daily_df['sma_20'] < daily_df['sma_50']) & (daily_df['macd'] < daily_df['macd_signal'])
            
            daily_trend[daily_uptrend] = 1
            daily_trend[daily_downtrend] = -1
            
            # Apply to hourly signals
            for idx in df.index:
                # Find corresponding daily trend
                daily_idx = daily_trend.index[daily_trend.index.date <= idx.date()]
                if len(daily_idx) > 0:
                    latest_daily = daily_idx[-1]
                    trend_direction = daily_trend[latest_daily]
                    
                    if trend_direction == 1:  # Daily uptrend
                        # Buy on hourly pullback
                        if df.loc[idx, 'rsi'] < 45 and df.loc[idx, 'close'] > df.loc[idx, 'sma_20']:
                            signals[idx] = 1
                    elif trend_direction == -1:  # Daily downtrend
                        # Sell on hourly bounce
                        if df.loc[idx, 'rsi'] > 55 and df.loc[idx, 'close'] < df.loc[idx, 'sma_20']:
                            signals[idx] = -1
        
        return signals
    
    def generate_all_strategies(self, timeframe: str = "1h") -> Dict[str, Any]:
        """Generate all strategy types"""
        self.logger.info(f"Generating strategies for {timeframe} timeframe...")
        
        # Load and prepare data
        df = self.load_data(timeframe)
        if df.empty:
            self.logger.error(f"No data loaded for {timeframe}")
            return {}
        
        df = self.add_technical_indicators(df)
        
        # Generate all strategy types
        all_strategies = {}
        for strategy_type, generator_func in self.strategy_templates.items():
            try:
                strategies = generator_func(df)
                all_strategies.update(strategies)
                self.logger.info(f"Generated {len(strategies)} {strategy_type} strategies")
            except Exception as e:
                self.logger.error(f"Error generating {strategy_type} strategies: {e}")
        
        self.strategies[timeframe] = all_strategies
        return all_strategies
    
    def save_strategies(self, filename: str = None):
        """Save generated strategies to file"""
        if not filename:
            filename = f"strategies_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path("results") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        # Convert signals to lists for JSON serialization
        serializable_strategies = {}
        for tf, strategies in self.strategies.items():
            serializable_strategies[tf] = {}
            for name, strategy in strategies.items():
                serializable_strategies[tf][name] = {
                    'name': strategy['name'],
                    'type': strategy['type'],
                    'description': strategy['description'],
                    'signal_count': int(strategy['signals'].abs().sum()) if hasattr(strategy['signals'], 'sum') else 0
                }
        
        with open(filepath, 'w') as f:
            json.dump(serializable_strategies, f, indent=2)
        
        self.logger.info(f"Strategies saved to {filepath}")
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """Get summary of generated strategies"""
        summary = {
            'total_strategies': 0,
            'by_timeframe': {},
            'by_type': {}
        }
        
        for tf, strategies in self.strategies.items():
            summary['by_timeframe'][tf] = len(strategies)
            summary['total_strategies'] += len(strategies)
            
            for name, strategy in strategies.items():
                strategy_type = strategy['type']
                if strategy_type not in summary['by_type']:
                    summary['by_type'][strategy_type] = 0
                summary['by_type'][strategy_type] += 1
        
        return summary

def main():
    """Main execution function"""
    print("🚀 AI Gold Scalper - Strategy Generator")
    print("=" * 50)
    
    # Initialize generator
    generator = StrategyGenerator()
    
    # Generate strategies for different timeframes
    timeframes = ['1h', '4h', '1d']
    
    for tf in timeframes:
        print(f"\n📊 Generating strategies for {tf} timeframe...")
        strategies = generator.generate_all_strategies(tf)
        
        if strategies:
            print(f"✅ Generated {len(strategies)} strategies:")
            for name, strategy in strategies.items():
                signal_count = strategy['signals'].abs().sum() if hasattr(strategy['signals'], 'sum') else 0
                print(f"   • {strategy['name']}: {signal_count} signals ({strategy['type']})")
    
    # Save strategies
    generator.save_strategies()
    
    # Print summary
    summary = generator.get_strategy_summary()
    print(f"\n📈 Strategy Generation Summary:")
    print(f"   • Total Strategies: {summary['total_strategies']}")
    print(f"   • By Timeframe: {summary['by_timeframe']}")
    print(f"   • By Type: {summary['by_type']}")
    
    print("\n🎉 Strategy generation completed!")
    print("💡 Next steps:")
    print("   1. Run backtesting on generated strategies")
    print("   2. Optimize best performing strategies")
    print("   3. Deploy top strategies for live trading")

if __name__ == "__main__":
    main()
