#!/usr/bin/env python3
"""
AI Gold Scalper - Market Regime Detection System
Detects different market conditions and adapts model selection accordingly
"""

import os
import json
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Technical analysis imports
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.mixture import GaussianMixture
from sklearn.metrics import silhouette_score

# Statistical imports
import scipy.stats as stats
from scipy.signal import find_peaks

@dataclass
class MarketRegime:
    """Represents a market regime with its characteristics"""
    regime_id: str
    regime_name: str
    volatility_level: str  # 'low', 'medium', 'high'
    trend_direction: str   # 'bullish', 'bearish', 'sideways'
    volume_pattern: str    # 'normal', 'high', 'low'
    price_action: str      # 'trending', 'ranging', 'breakout', 'reversal'
    characteristics: Dict[str, float]
    optimal_models: List[str]
    confidence_score: float
    detected_at: datetime
    duration_hours: float = 0.0

@dataclass
class RegimeConfig:
    """Configuration for market regime detection"""
    lookback_periods: int = 100
    volatility_window: int = 20
    trend_window: int = 50
    volume_window: int = 20
    regime_change_threshold: float = 0.3
    min_regime_duration_hours: float = 2.0
    use_clustering: bool = True
    use_statistical_analysis: bool = True
    cluster_count: int = 4

class MarketRegimeDetector:
    """Advanced market regime detection and classification"""
    
    def __init__(self, config: RegimeConfig = None):
        self.config = config or RegimeConfig()
        self.regime_db = "models/market_regimes.db"
        self.scaler = StandardScaler()
        
        # Initialize components
        self._init_regime_database()
        self.current_regime = None
        self.regime_history = []
        
        # Clustering models
        self.kmeans_model = None
        self.gmm_model = None
        
    def _init_regime_database(self):
        """Initialize market regime tracking database"""
        os.makedirs("models", exist_ok=True)
        
        conn = sqlite3.connect(self.regime_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_regimes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regime_id TEXT NOT NULL,
            regime_name TEXT NOT NULL,
            volatility_level TEXT NOT NULL,
            trend_direction TEXT NOT NULL,
            volume_pattern TEXT NOT NULL,
            price_action TEXT NOT NULL,
            characteristics TEXT NOT NULL,  -- JSON
            optimal_models TEXT NOT NULL,   -- JSON
            confidence_score REAL NOT NULL,
            detected_at TIMESTAMP NOT NULL,
            ended_at TIMESTAMP,
            duration_hours REAL DEFAULT 0.0
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS regime_transitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_regime_id TEXT NOT NULL,
            to_regime_id TEXT NOT NULL,
            transition_time TIMESTAMP NOT NULL,
            transition_strength REAL NOT NULL,
            market_conditions TEXT NOT NULL  -- JSON
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS regime_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            regime_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            accuracy REAL NOT NULL,
            win_rate REAL NOT NULL,
            profit_factor REAL NOT NULL,
            trades_count INTEGER NOT NULL,
            evaluation_date TIMESTAMP NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def analyze_market_data(self, price_data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market data to extract regime characteristics"""
        
        if len(price_data) < self.config.lookback_periods:
            raise ValueError(f"Need at least {self.config.lookback_periods} data points")
        
        # Ensure we have required columns
        required_cols = ['close', 'high', 'low', 'open']
        if 'volume' not in price_data.columns:
            price_data['volume'] = 1.0  # Default volume if not available
            
        analysis = {}
        
        # 1. Volatility Analysis
        analysis.update(self._analyze_volatility(price_data))
        
        # 2. Trend Analysis
        analysis.update(self._analyze_trend(price_data))
        
        # 3. Volume Analysis
        analysis.update(self._analyze_volume(price_data))
        
        # 4. Price Action Analysis
        analysis.update(self._analyze_price_action(price_data))
        
        # 5. Statistical Properties
        analysis.update(self._analyze_statistical_properties(price_data))
        
        # 6. Market Microstructure
        analysis.update(self._analyze_microstructure(price_data))
        
        return analysis
    
    def _analyze_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volatility characteristics"""
        
        # Calculate different volatility measures
        returns = data['close'].pct_change().dropna()
        
        # Historical volatility (annualized)
        hist_vol = returns.std() * np.sqrt(252)
        
        # Rolling volatility
        rolling_vol = returns.rolling(self.config.volatility_window).std()
        
        # Volatility of volatility
        vol_of_vol = rolling_vol.std()
        
        # GARCH-like volatility clustering
        volatility_clustering = self._detect_volatility_clustering(returns)
        
        # Classify volatility level
        vol_percentiles = np.percentile(rolling_vol.dropna(), [33, 67])
        current_vol = rolling_vol.iloc[-1]
        
        if current_vol <= vol_percentiles[0]:
            vol_level = 'low'
        elif current_vol <= vol_percentiles[1]:
            vol_level = 'medium'
        else:
            vol_level = 'high'
        
        return {
            'historical_volatility': hist_vol,
            'current_volatility': current_vol,
            'volatility_level': vol_level,
            'volatility_of_volatility': vol_of_vol,
            'volatility_clustering': volatility_clustering,
            'volatility_percentile': stats.percentileofscore(rolling_vol.dropna(), current_vol)
        }
    
    def _analyze_trend(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trend characteristics"""
        
        closes = data['close']
        
        # Moving averages for trend detection
        ma_short = closes.rolling(10).mean()
        ma_medium = closes.rolling(20).mean()
        ma_long = closes.rolling(self.config.trend_window).mean()
        
        # Trend strength using linear regression
        x = np.arange(len(closes))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x[-self.config.trend_window:], 
                                                                      closes.iloc[-self.config.trend_window:])
        
        # ADX-like trend strength
        trend_strength = abs(r_value)
        
        # Determine trend direction
        current_price = closes.iloc[-1]
        ma_long_current = ma_long.iloc[-1]
        
        if slope > 0 and current_price > ma_long_current:
            trend_direction = 'bullish'
        elif slope < 0 and current_price < ma_long_current:
            trend_direction = 'bearish'
        else:
            trend_direction = 'sideways'
        
        # Trend consistency
        price_above_ma = (closes > ma_long).rolling(20).mean().iloc[-1]
        
        return {
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'trend_slope': slope,
            'trend_r_squared': r_value**2,
            'trend_consistency': price_above_ma,
            'ma_alignment': self._check_ma_alignment(ma_short, ma_medium, ma_long)
        }
    
    def _analyze_volume(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze volume patterns"""
        
        volume = data['volume']
        
        # Volume moving average
        volume_ma = volume.rolling(self.config.volume_window).mean()
        current_volume = volume.iloc[-1]
        avg_volume = volume_ma.iloc[-1]
        
        # Volume trend
        volume_trend = np.corrcoef(np.arange(len(volume)), volume)[0, 1]
        
        # Volume volatility
        volume_volatility = volume.pct_change().std()
        
        # Classify volume pattern
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio > 1.5:
            volume_pattern = 'high'
        elif volume_ratio < 0.5:
            volume_pattern = 'low'
        else:
            volume_pattern = 'normal'
        
        # Price-volume relationship
        price_volume_corr = np.corrcoef(data['close'].pct_change().dropna(), 
                                       volume.pct_change().dropna())[0, 1]
        
        return {
            'volume_pattern': volume_pattern,
            'volume_ratio': volume_ratio,
            'volume_trend': volume_trend,
            'volume_volatility': volume_volatility,
            'price_volume_correlation': price_volume_corr,
            'average_volume': avg_volume
        }
    
    def _analyze_price_action(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price action patterns"""
        
        # Calculate price action metrics
        closes = data['close']
        highs = data['high']
        lows = data['low']
        
        # Support and resistance levels
        support_resistance = self._find_support_resistance(highs, lows)
        
        # Breakout detection
        breakout_signals = self._detect_breakouts(data)
        
        # Range detection
        range_metrics = self._detect_ranging_market(closes)
        
        # Momentum indicators
        rsi = self._calculate_rsi(closes)
        macd = self._calculate_macd(closes)
        
        # Price action classification
        if breakout_signals['breakout_strength'] > 0.7:
            price_action = 'breakout'
        elif range_metrics['range_strength'] > 0.6:
            price_action = 'ranging'
        elif abs(macd['macd_signal']) > 0.5:
            price_action = 'trending'
        else:
            price_action = 'reversal'
        
        return {
            'price_action': price_action,
            'support_resistance': support_resistance,
            'breakout_signals': breakout_signals,
            'range_metrics': range_metrics,
            'rsi': rsi,
            'macd': macd,
            'price_efficiency': self._calculate_price_efficiency(closes)
        }
    
    def _analyze_statistical_properties(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze statistical properties of returns"""
        
        returns = data['close'].pct_change().dropna()
        
        # Distribution properties
        skewness = stats.skew(returns)
        kurtosis = stats.kurtosis(returns)
        
        # Normality tests
        shapiro_stat, shapiro_p = stats.shapiro(returns[-100:] if len(returns) > 100 else returns)
        
        # Autocorrelation
        autocorr_1 = returns.autocorr(lag=1) if len(returns) > 1 else 0
        autocorr_5 = returns.autocorr(lag=5) if len(returns) > 5 else 0
        
        # Hurst exponent (simplified)
        hurst = self._calculate_hurst_exponent(data['close'])
        
        return {
            'returns_skewness': skewness,
            'returns_kurtosis': kurtosis,
            'normality_test': shapiro_p,
            'autocorrelation_1': autocorr_1,
            'autocorrelation_5': autocorr_5,
            'hurst_exponent': hurst,
            'mean_reversion_tendency': 1 - hurst if hurst < 0.5 else 0
        }
    
    def _analyze_microstructure(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Analyze market microstructure patterns"""
        
        # Bid-ask spread proxy (high-low spread)
        spread = (data['high'] - data['low']) / data['close']
        avg_spread = spread.mean()
        
        # Price impact estimation
        returns = data['close'].pct_change()
        volume = data['volume']
        price_impact = abs(returns).corr(volume) if len(returns) > 10 else 0
        
        # Market efficiency proxy
        efficiency = self._calculate_market_efficiency(data['close'])
        
        return {
            'average_spread': avg_spread,
            'spread_volatility': spread.std(),
            'price_impact': price_impact,
            'market_efficiency': efficiency,
            'liquidity_proxy': 1 / avg_spread if avg_spread > 0 else 0
        }
    
    def detect_regime(self, price_data: pd.DataFrame) -> MarketRegime:
        """Main method to detect current market regime"""
        
        print("🔍 Analyzing market regime...")
        
        # Analyze market data
        analysis = self.analyze_market_data(price_data)
        
        # Regime classification approaches
        regimes = []
        
        # 1. Rule-based classification
        rule_based_regime = self._classify_regime_rule_based(analysis)
        regimes.append(rule_based_regime)
        
        # 2. Clustering-based classification (if enough data)
        if len(price_data) >= 200 and self.config.use_clustering:
            cluster_regime = self._classify_regime_clustering(analysis, price_data)
            if cluster_regime:
                regimes.append(cluster_regime)
        
        # 3. Statistical classification
        if self.config.use_statistical_analysis:
            stat_regime = self._classify_regime_statistical(analysis)
            regimes.append(stat_regime)
        
        # Combine regime predictions
        final_regime = self._combine_regime_predictions(regimes, analysis)
        
        # Store regime
        self._store_regime(final_regime)
        
        print(f"   Detected regime: {final_regime.regime_name}")
        print(f"   Confidence: {final_regime.confidence_score:.2f}")
        
        return final_regime
    
    def _classify_regime_rule_based(self, analysis: Dict[str, Any]) -> MarketRegime:
        """Rule-based regime classification"""
        
        # Extract key metrics
        vol_level = analysis['volatility_level']
        trend_dir = analysis['trend_direction']
        volume_pattern = analysis['volume_pattern']
        price_action = analysis['price_action']
        
        # Determine regime name and characteristics
        regime_components = []
        
        # Volatility component
        if vol_level == 'high':
            regime_components.append('High Vol')
        elif vol_level == 'low':
            regime_components.append('Low Vol')
        
        # Trend component
        if trend_dir == 'bullish' and analysis['trend_strength'] > 0.5:
            regime_components.append('Bull Trend')
        elif trend_dir == 'bearish' and analysis['trend_strength'] > 0.5:
            regime_components.append('Bear Trend')
        elif price_action == 'ranging':
            regime_components.append('Sideways')
        
        # Special conditions
        if price_action == 'breakout':
            regime_components.append('Breakout')
        elif analysis.get('volatility_clustering', 0) > 0.3:
            regime_components.append('Volatile')
        
        regime_name = ' '.join(regime_components) if regime_components else 'Normal Market'
        
        # Suggest optimal models based on regime
        optimal_models = self._suggest_optimal_models(analysis)
        
        # Calculate confidence based on strength of signals
        confidence = self._calculate_regime_confidence(analysis)
        
        return MarketRegime(
            regime_id=f"rule_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            regime_name=regime_name,
            volatility_level=vol_level,
            trend_direction=trend_dir,
            volume_pattern=volume_pattern,
            price_action=price_action,
            characteristics=analysis,
            optimal_models=optimal_models,
            confidence_score=confidence,
            detected_at=datetime.now()
        )
    
    def _classify_regime_clustering(self, analysis: Dict[str, Any], 
                                   price_data: pd.DataFrame) -> Optional[MarketRegime]:
        """Clustering-based regime classification"""
        
        try:
            # Prepare features for clustering
            features = self._prepare_clustering_features(analysis, price_data)
            
            if len(features) < 50:  # Need sufficient data
                return None
            
            # Standardize features
            features_scaled = self.scaler.fit_transform(features)
            
            # Apply K-means clustering
            self.kmeans_model = KMeans(n_clusters=self.config.cluster_count, random_state=42)
            cluster_labels = self.kmeans_model.fit_predict(features_scaled)
            
            # Get current regime cluster
            current_cluster = cluster_labels[-1]
            
            # Characterize the cluster
            cluster_characteristics = self._characterize_cluster(features, cluster_labels, current_cluster)
            
            # Generate regime name based on cluster characteristics
            regime_name = f"Cluster {current_cluster} - {cluster_characteristics['dominant_pattern']}"
            
            # Calculate silhouette score for confidence
            silhouette = silhouette_score(features_scaled, cluster_labels)
            
            return MarketRegime(
                regime_id=f"cluster_{current_cluster}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                regime_name=regime_name,
                volatility_level=cluster_characteristics['volatility_level'],
                trend_direction=cluster_characteristics['trend_direction'],
                volume_pattern=cluster_characteristics['volume_pattern'],
                price_action=cluster_characteristics['price_action'],
                characteristics=cluster_characteristics,
                optimal_models=cluster_characteristics['optimal_models'],
                confidence_score=silhouette,
                detected_at=datetime.now()
            )
            
        except Exception as e:
            print(f"⚠️  Clustering classification failed: {e}")
            return None
    
    def _classify_regime_statistical(self, analysis: Dict[str, Any]) -> MarketRegime:
        """Statistical regime classification"""
        
        # Use statistical properties to classify regime
        hurst = analysis.get('hurst_exponent', 0.5)
        skewness = analysis.get('returns_skewness', 0)
        kurtosis = analysis.get('returns_kurtosis', 0)
        autocorr = analysis.get('autocorrelation_1', 0)
        
        # Regime classification based on statistical properties
        if hurst > 0.6:
            stat_regime = 'Trending'
        elif hurst < 0.4:
            stat_regime = 'Mean Reverting'
        elif abs(skewness) > 1:
            stat_regime = 'Skewed Distribution'
        elif kurtosis > 3:
            stat_regime = 'Heavy Tails'
        else:
            stat_regime = 'Normal Distribution'
        
        # Confidence based on statistical significance
        confidence = min(abs(hurst - 0.5) * 2, 1.0)
        
        return MarketRegime(
            regime_id=f"stat_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            regime_name=f"Statistical: {stat_regime}",
            volatility_level=analysis['volatility_level'],
            trend_direction=analysis['trend_direction'],
            volume_pattern=analysis['volume_pattern'],
            price_action=analysis['price_action'],
            characteristics=analysis,
            optimal_models=self._suggest_optimal_models(analysis),
            confidence_score=confidence,
            detected_at=datetime.now()
        )
    
    def _combine_regime_predictions(self, regimes: List[MarketRegime], 
                                   analysis: Dict[str, Any]) -> MarketRegime:
        """Combine multiple regime predictions into final prediction"""
        
        if len(regimes) == 1:
            return regimes[0]
        
        # Weight regimes by confidence
        total_weight = sum(r.confidence_score for r in regimes)
        
        if total_weight == 0:
            return regimes[0]  # Fallback
        
        # Combine regime names
        regime_names = [r.regime_name for r in regimes]
        combined_name = f"Combined: {', '.join(regime_names[:2])}"  # Limit length
        
        # Use highest confidence regime's characteristics as base
        best_regime = max(regimes, key=lambda r: r.confidence_score)
        
        # Average confidence
        avg_confidence = total_weight / len(regimes)
        
        return MarketRegime(
            regime_id=f"combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            regime_name=combined_name,
            volatility_level=best_regime.volatility_level,
            trend_direction=best_regime.trend_direction,
            volume_pattern=best_regime.volume_pattern,
            price_action=best_regime.price_action,
            characteristics=analysis,
            optimal_models=best_regime.optimal_models,
            confidence_score=avg_confidence,
            detected_at=datetime.now()
        )
    
    def _suggest_optimal_models(self, analysis: Dict[str, Any]) -> List[str]:
        """Suggest optimal models for the detected regime"""
        
        optimal_models = []
        
        # Volatility-based suggestions
        if analysis['volatility_level'] == 'high':
            optimal_models.extend(['gradient_boost', 'xgboost', 'neural_net'])
        elif analysis['volatility_level'] == 'low':
            optimal_models.extend(['logistic', 'svm', 'naive_bayes'])
        else:
            optimal_models.extend(['random_forest', 'ensemble'])
        
        # Trend-based suggestions
        if analysis['trend_direction'] in ['bullish', 'bearish'] and analysis['trend_strength'] > 0.5:
            optimal_models.extend(['gradient_boost', 'xgboost'])
        elif analysis['price_action'] == 'ranging':
            optimal_models.extend(['svm', 'neural_net'])
        
        # Statistical property-based suggestions
        hurst = analysis.get('hurst_exponent', 0.5)
        if hurst > 0.6:  # Trending
            optimal_models.extend(['random_forest', 'gradient_boost'])
        elif hurst < 0.4:  # Mean reverting
            optimal_models.extend(['logistic', 'svm'])
        
        # Remove duplicates and return top suggestions
        optimal_models = list(set(optimal_models))
        return optimal_models[:3]  # Return top 3
    
    def _calculate_regime_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for regime detection"""
        
        confidence_factors = []
        
        # Trend strength confidence
        trend_strength = analysis.get('trend_strength', 0)
        confidence_factors.append(trend_strength)
        
        # Volatility consistency
        vol_percentile = analysis.get('volatility_percentile', 50)
        vol_confidence = abs(vol_percentile - 50) / 50  # Distance from median
        confidence_factors.append(vol_confidence)
        
        # Statistical significance
        normality_p = analysis.get('normality_test', 0.5)
        stat_confidence = 1 - normality_p if normality_p < 0.05 else 0.5
        confidence_factors.append(stat_confidence)
        
        # Price action clarity
        if analysis.get('price_action') == 'breakout':
            breakout_strength = analysis.get('breakout_signals', {}).get('breakout_strength', 0)
            confidence_factors.append(breakout_strength)
        elif analysis.get('price_action') == 'ranging':
            range_strength = analysis.get('range_metrics', {}).get('range_strength', 0)
            confidence_factors.append(range_strength)
        
        # Average confidence with minimum baseline
        avg_confidence = np.mean(confidence_factors) if confidence_factors else 0.5
        return max(0.3, min(0.95, avg_confidence))  # Clamp between 30% and 95%
    
    # Helper methods (simplified implementations)
    def _detect_volatility_clustering(self, returns: pd.Series) -> float:
        """Detect volatility clustering using ARCH effects"""
        if len(returns) < 20:
            return 0.0
        
        # Simple proxy: correlation between absolute returns and their lag
        abs_returns = abs(returns)
        clustering = abs_returns.autocorr(lag=1) if len(abs_returns) > 1 else 0
        return max(0, clustering) if not np.isnan(clustering) else 0
    
    def _check_ma_alignment(self, ma_short, ma_medium, ma_long) -> str:
        """Check moving average alignment"""
        current_short = ma_short.iloc[-1]
        current_medium = ma_medium.iloc[-1]
        current_long = ma_long.iloc[-1]
        
        if current_short > current_medium > current_long:
            return 'bullish_aligned'
        elif current_short < current_medium < current_long:
            return 'bearish_aligned'
        else:
            return 'mixed'
    
    def _find_support_resistance(self, highs: pd.Series, lows: pd.Series) -> Dict[str, float]:
        """Find support and resistance levels"""
        # Simplified implementation using recent highs/lows
        recent_high = highs.tail(20).max()
        recent_low = lows.tail(20).min()
        
        return {
            'resistance': recent_high,
            'support': recent_low,
            'range_size': (recent_high - recent_low) / recent_low
        }
    
    def _detect_breakouts(self, data: pd.DataFrame) -> Dict[str, float]:
        """Detect breakout patterns"""
        # Simplified breakout detection
        closes = data['close']
        current_price = closes.iloc[-1]
        
        # Bollinger Bands breakout
        rolling_mean = closes.rolling(20).mean().iloc[-1]
        rolling_std = closes.rolling(20).std().iloc[-1]
        
        upper_band = rolling_mean + 2 * rolling_std
        lower_band = rolling_mean - 2 * rolling_std
        
        if current_price > upper_band:
            breakout_strength = (current_price - upper_band) / rolling_std
        elif current_price < lower_band:
            breakout_strength = (lower_band - current_price) / rolling_std
        else:
            breakout_strength = 0
        
        return {
            'breakout_strength': min(1.0, abs(breakout_strength) / 2),
            'direction': 'up' if breakout_strength > 0 else 'down' if breakout_strength < 0 else 'none'
        }
    
    def _detect_ranging_market(self, closes: pd.Series) -> Dict[str, float]:
        """Detect ranging market conditions"""
        # Price efficiency as range indicator
        efficiency = self._calculate_price_efficiency(closes)
        
        # Standard deviation of returns
        returns_std = closes.pct_change().std()
        
        range_strength = (1 - efficiency) * (1 / (1 + returns_std)) if returns_std > 0 else 0
        
        return {
            'range_strength': min(1.0, range_strength * 2),
            'price_efficiency': efficiency
        }
    
    def _calculate_rsi(self, closes: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        if len(closes) < period + 1:
            return 50.0  # Neutral
            
        delta = closes.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else 50.0
    
    def _calculate_macd(self, closes: pd.Series) -> Dict[str, float]:
        """Calculate MACD"""
        if len(closes) < 26:
            return {'macd': 0, 'signal': 0, 'macd_signal': 0}
            
        exp1 = closes.ewm(span=12).mean()
        exp2 = closes.ewm(span=26).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9).mean()
        
        return {
            'macd': macd.iloc[-1] if not np.isnan(macd.iloc[-1]) else 0,
            'signal': signal.iloc[-1] if not np.isnan(signal.iloc[-1]) else 0,
            'macd_signal': (macd - signal).iloc[-1] if not np.isnan((macd - signal).iloc[-1]) else 0
        }
    
    def _calculate_price_efficiency(self, closes: pd.Series) -> float:
        """Calculate price efficiency (how directly price moves)"""
        if len(closes) < 2:
            return 0.5
            
        # Distance traveled vs. displacement
        total_distance = abs(closes.diff()).sum()
        displacement = abs(closes.iloc[-1] - closes.iloc[0])
        
        if total_distance == 0:
            return 1.0
            
        efficiency = displacement / total_distance
        return min(1.0, efficiency)
    
    def _calculate_market_efficiency(self, closes: pd.Series) -> float:
        """Calculate market efficiency using variance ratio"""
        if len(closes) < 20:
            return 0.5
            
        # Simplified variance ratio test
        returns = closes.pct_change().dropna()
        
        if len(returns) < 10:
            return 0.5
            
        # Variance of 1-period vs 2-period returns
        var_1 = returns.var()
        returns_2 = returns.rolling(2).sum().dropna()
        var_2 = returns_2.var()
        
        if var_1 == 0:
            return 0.5
            
        variance_ratio = var_2 / (2 * var_1)
        efficiency = abs(1 - variance_ratio)  # Distance from random walk
        
        return min(1.0, efficiency)
    
    def _calculate_hurst_exponent(self, closes: pd.Series) -> float:
        """Calculate Hurst exponent (simplified R/S analysis)"""
        if len(closes) < 20:
            return 0.5
            
        # Simplified Hurst calculation
        returns = closes.pct_change().dropna()
        
        if len(returns) < 10:
            return 0.5
            
        # Calculate mean return
        mean_return = returns.mean()
        
        # Calculate cumulative deviations
        cum_dev = (returns - mean_return).cumsum()
        
        # Calculate range
        R = cum_dev.max() - cum_dev.min()
        
        # Calculate standard deviation
        S = returns.std()
        
        if S == 0:
            return 0.5
            
        # R/S ratio
        rs_ratio = R / S
        
        # Hurst exponent approximation
        hurst = np.log(rs_ratio) / np.log(len(returns))
        
        return max(0.1, min(0.9, hurst)) if not np.isnan(hurst) else 0.5
    
    def _prepare_clustering_features(self, analysis: Dict[str, Any], 
                                   price_data: pd.DataFrame) -> np.ndarray:
        """Prepare features for clustering analysis"""
        
        # Extract numeric features from analysis
        features_list = []
        
        # Rolling window features
        window_sizes = [10, 20, 50]
        
        for window in window_sizes:
            if len(price_data) >= window:
                # Volatility features
                vol = price_data['close'].pct_change().rolling(window).std()
                features_list.append(vol.dropna())
                
                # Trend features
                ma = price_data['close'].rolling(window).mean()
                trend = (price_data['close'] / ma).dropna()
                features_list.append(trend)
                
                # Volume features (if available)
                if 'volume' in price_data.columns:
                    vol_ma = price_data['volume'].rolling(window).mean()
                    vol_ratio = (price_data['volume'] / vol_ma).dropna()
                    features_list.append(vol_ratio)
        
        # Combine features
        min_length = min(len(f) for f in features_list) if features_list else 0
        
        if min_length < 10:
            return np.array([])
            
        # Align all features to same length
        aligned_features = []
        for feature in features_list:
            aligned_features.append(feature.iloc[-min_length:].values)
        
        return np.column_stack(aligned_features)
    
    def _characterize_cluster(self, features: np.ndarray, labels: np.ndarray, 
                            cluster_id: int) -> Dict[str, Any]:
        """Characterize a specific cluster"""
        
        cluster_mask = labels == cluster_id
        cluster_features = features[cluster_mask]
        
        if len(cluster_features) == 0:
            return self._get_default_characteristics()
        
        # Statistical characterization
        mean_features = cluster_features.mean(axis=0)
        std_features = cluster_features.std(axis=0)
        
        # Determine dominant patterns
        volatility_level = 'high' if mean_features[0] > np.mean(features[:, 0]) else 'low'
        trend_direction = 'bullish' if len(mean_features) > 1 and mean_features[1] > 1 else 'bearish'
        
        return {
            'dominant_pattern': f'{volatility_level}_vol_{trend_direction}',
            'volatility_level': volatility_level,
            'trend_direction': trend_direction,
            'volume_pattern': 'normal',
            'price_action': 'clustering',
            'optimal_models': self._suggest_models_for_cluster(mean_features),
            'cluster_size': len(cluster_features),
            'cluster_stability': 1 / (1 + std_features.mean()) if std_features.mean() > 0 else 0.5
        }
    
    def _suggest_models_for_cluster(self, cluster_features: np.ndarray) -> List[str]:
        """Suggest models based on cluster characteristics"""
        
        # Simple heuristic based on feature means
        if len(cluster_features) > 0:
            if cluster_features[0] > 0.02:  # High volatility
                return ['gradient_boost', 'xgboost', 'neural_net']
            else:  # Low volatility
                return ['logistic', 'svm', 'random_forest']
        
        return ['random_forest', 'ensemble']
    
    def _get_default_characteristics(self) -> Dict[str, Any]:
        """Get default characteristics when clustering fails"""
        return {
            'dominant_pattern': 'normal_market',
            'volatility_level': 'medium',
            'trend_direction': 'sideways',
            'volume_pattern': 'normal',
            'price_action': 'ranging',
            'optimal_models': ['random_forest', 'ensemble'],
            'cluster_size': 0,
            'cluster_stability': 0.5
        }
    
    def _store_regime(self, regime: MarketRegime):
        """Store detected regime in database"""
        
        # End previous regime if it exists
        if self.current_regime:
            self._end_current_regime()
        
        # Store new regime
        conn = sqlite3.connect(self.regime_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO market_regimes 
        (regime_id, regime_name, volatility_level, trend_direction, volume_pattern,
         price_action, characteristics, optimal_models, confidence_score, detected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            regime.regime_id, regime.regime_name, regime.volatility_level,
            regime.trend_direction, regime.volume_pattern, regime.price_action,
            json.dumps(regime.characteristics), json.dumps(regime.optimal_models),
            regime.confidence_score, regime.detected_at
        ))
        
        conn.commit()
        conn.close()
        
        self.current_regime = regime
        self.regime_history.append(regime)
    
    def _end_current_regime(self):
        """End the current regime and calculate duration"""
        if not self.current_regime:
            return
        
        end_time = datetime.now()
        duration = (end_time - self.current_regime.detected_at).total_seconds() / 3600
        
        conn = sqlite3.connect(self.regime_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE market_regimes 
        SET ended_at = ?, duration_hours = ?
        WHERE regime_id = ?
        ''', (end_time, duration, self.current_regime.regime_id))
        
        conn.commit()
        conn.close()
        
        self.current_regime.duration_hours = duration
    
    def get_regime_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get regime history for the specified number of days"""
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = sqlite3.connect(self.regime_db)
        
        regimes_df = pd.read_sql_query('''
        SELECT * FROM market_regimes 
        WHERE detected_at >= ?
        ORDER BY detected_at DESC
        ''', conn, params=[cutoff_date])
        
        conn.close()
        
        return regimes_df.to_dict('records')
    
    def get_regime_summary(self) -> Dict[str, Any]:
        """Get summary of regime detection system"""
        
        conn = sqlite3.connect(self.regime_db)
        
        # Get regime statistics
        regime_stats = pd.read_sql_query('''
        SELECT 
            regime_name,
            COUNT(*) as frequency,
            AVG(duration_hours) as avg_duration,
            AVG(confidence_score) as avg_confidence
        FROM market_regimes 
        GROUP BY regime_name
        ORDER BY frequency DESC
        ''', conn)
        
        # Get recent regimes
        recent_regimes = pd.read_sql_query('''
        SELECT * FROM market_regimes 
        ORDER BY detected_at DESC 
        LIMIT 10
        ''', conn)
        
        conn.close()
        
        summary = {
            'total_regimes_detected': len(recent_regimes),
            'current_regime': asdict(self.current_regime) if self.current_regime else None,
            'regime_frequency': regime_stats.to_dict('records') if not regime_stats.empty else [],
            'recent_regimes': recent_regimes.to_dict('records') if not recent_regimes.empty else [],
            'avg_regime_duration': recent_regimes['duration_hours'].mean() if not recent_regimes.empty and 'duration_hours' in recent_regimes.columns else 0,
            'most_common_regime': regime_stats.iloc[0]['regime_name'] if not regime_stats.empty else 'Unknown'
        }
        
        return summary

# Testing and demonstration
if __name__ == "__main__":
    print("🌍 AI Gold Scalper - Market Regime Detection Test")
    print("=" * 60)
    
    # Initialize regime detector
    detector = MarketRegimeDetector()
    
    # Generate sample market data
    print("📊 Generating sample market data...")
    
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=500, freq='H')
    
    # Simulate different market regimes
    price_data = []
    base_price = 2000
    
    for i, date in enumerate(dates):
        # Create regime changes
        if i < 150:  # Trending up
            trend = 0.001
            vol = 0.01
        elif i < 300:  # High volatility sideways
            trend = 0
            vol = 0.025
        else:  # Trending down
            trend = -0.0008
            vol = 0.015
        
        # Generate OHLC data
        change = np.random.normal(trend, vol)
        base_price *= (1 + change)
        
        # Generate OHLC from close
        high = base_price * (1 + abs(np.random.normal(0, vol/2)))
        low = base_price * (1 - abs(np.random.normal(0, vol/2)))
        open_price = base_price * (1 + np.random.normal(0, vol/4))
        
        price_data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': base_price,
            'volume': abs(np.random.normal(1000, 200))
        })
    
    df = pd.DataFrame(price_data)
    print(f"   Generated {len(df)} data points")
    
    try:
        # Test regime detection
        regime = detector.detect_regime(df)
        
        print(f"\n🎯 Detected Regime:")
        print(f"   Name: {regime.regime_name}")
        print(f"   Volatility: {regime.volatility_level}")
        print(f"   Trend: {regime.trend_direction}")
        print(f"   Price Action: {regime.price_action}")
        print(f"   Confidence: {regime.confidence_score:.2%}")
        print(f"   Optimal Models: {', '.join(regime.optimal_models)}")
        
        # Test with different data segments
        print(f"\n🔄 Testing regime detection on different segments...")
        
        segments = [
            df.iloc[:150],   # Trending segment
            df.iloc[150:300], # Volatile segment  
            df.iloc[300:]     # Declining segment
        ]
        
        for i, segment in enumerate(segments, 1):
            if len(segment) >= 100:  # Ensure sufficient data
                segment_regime = detector.detect_regime(segment)
                print(f"   Segment {i}: {segment_regime.regime_name} (conf: {segment_regime.confidence_score:.2f})")
        
        # Get regime summary
        summary = detector.get_regime_summary()
        print(f"\n📊 Regime Detection Summary:")
        print(f"   Total Regimes Detected: {summary['total_regimes_detected']}")
        print(f"   Current Regime: {summary['current_regime']['regime_name'] if summary['current_regime'] else 'None'}")
        
        print(f"\n✅ Market regime detection test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in regime detection: {e}")
        import traceback
        traceback.print_exc()
