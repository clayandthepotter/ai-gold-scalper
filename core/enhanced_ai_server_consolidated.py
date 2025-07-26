#!/usr/bin/env python3
"""
AI Gold Scalper - Production Server

Version: 5.0.0
Features:
- Production Performance Monitoring with P95/P99 metrics
- Dev Tunnel Integration for secure model updates
- Multi-Model ML Integration (RF, NN, GB)
- Advanced Technical Analysis with time-series
- Intelligent Caching and Connection Pooling
- Signal Fusion Engine for multi-source signals
- Risk Management System
- Market Context Engine
- Comprehensive Error Handling and Logging
"""

import os
import json
import logging
import numpy as np
import pandas as pd
import asyncio
import aiohttp
import time
import hashlib
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
import openai
from typing import Dict, List, Tuple, Optional, Any, Union
import joblib
import torch
import torch.nn as nn
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

# Configure advanced logging with function/line tracking
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('consolidated_ai_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Production performance monitoring with advanced metrics"""
    def __init__(self):
        self.request_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.error_count = 0
        self.start_time = datetime.now()
        self.model_updates = 0
        self.last_model_update = None
        self.signal_accuracy_tracking = []
        self.lock = threading.Lock()
        
    def log_request(self, duration: float, error: bool = False, cached: bool = False):
        with self.lock:
            self.request_times.append(duration)
            self.total_requests += 1
            
            if error:
                self.error_count += 1
            if cached:
                self.cache_hits += 1
            else:
                self.cache_misses += 1
            
            # Keep only last 1000 requests for memory efficiency
            if len(self.request_times) > 1000:
                self.request_times.pop(0)
    
    def log_model_update(self, model_name: str, version: str):
        with self.lock:
            self.model_updates += 1
            self.last_model_update = datetime.now()
            logger.info(f"Model update logged: {model_name} v{version}")
    
    def log_signal_accuracy(self, predicted: str, actual: str = None):
        """Track signal accuracy for performance monitoring"""
        if actual:
            self.signal_accuracy_tracking.append({
                'predicted': predicted,
                'actual': actual,
                'timestamp': datetime.now(),
                'correct': predicted == actual
            })
            # Keep only last 100 signals
            if len(self.signal_accuracy_tracking) > 100:
                self.signal_accuracy_tracking.pop(0)
    
    def get_stats(self) -> Dict:
        with self.lock:
            if not self.request_times:
                return {"status": "no_data", "server_version": "5.0.0-consolidated"}
            
            uptime = (datetime.now() - self.start_time).total_seconds()
            
            # Calculate accuracy if we have tracking data
            accuracy_rate = 0.0
            if self.signal_accuracy_tracking:
                correct_predictions = sum(1 for s in self.signal_accuracy_tracking if s.get('correct', False))
                accuracy_rate = correct_predictions / len(self.signal_accuracy_tracking) * 100
            
            return {
                "server_version": "5.0.0-consolidated",
                "uptime_hours": round(uptime / 3600, 2),
                "avg_response_time_ms": round(np.mean(self.request_times) * 1000, 2),
                "median_response_time_ms": round(np.median(self.request_times) * 1000, 2),
                "p95_response_time_ms": round(np.percentile(self.request_times, 95) * 1000, 2),
                "p99_response_time_ms": round(np.percentile(self.request_times, 99) * 1000, 2),
                "cache_hit_rate": round(self.cache_hits / max(self.cache_hits + self.cache_misses, 1) * 100, 2),
                "total_requests": self.total_requests,
                "error_rate": round(self.error_count / max(self.total_requests, 1) * 100, 2),
                "requests_per_hour": round(self.total_requests / max(uptime / 3600, 0.001), 1),
                "model_updates": self.model_updates,
                "last_model_update": self.last_model_update.isoformat() if self.last_model_update else None,
                "signal_accuracy_rate": round(accuracy_rate, 2),
                "signals_tracked": len(self.signal_accuracy_tracking)
            }

class ModelInferenceEngine:
    """Multi-model inference engine with performance tracking"""
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.model_versions = {}
        self.model_performance = {}
        self.feature_list = None
        self.lock = threading.Lock()
        
    def load_model(self, model_name: str, model_path: str, scaler_path: str = None, version: str = "1.0") -> bool:
        """Load model and optional scaler for inference"""
        try:
            with self.lock:
                if os.path.exists(model_path):
                    model = joblib.load(model_path)
                    self.models[model_name] = model
                    self.model_versions[model_name] = version
                    
                    # Load scaler if provided
                    if scaler_path and os.path.exists(scaler_path):
                        scaler = joblib.load(scaler_path)
                        self.scalers[model_name] = scaler
                        logger.info(f"Loaded scaler for {model_name}")
                    
                    self.model_performance[model_name] = {
                        'loaded_at': datetime.now().isoformat(),
                        'predictions': 0,
                        'avg_inference_time': 0.0,
                        'version': version
                    }
                    
                    logger.info(f"Model {model_name} v{version} loaded successfully")
                    return True
                else:
                    logger.warning(f"Model file not found: {model_path}")
                    return False
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    def predict(self, model_name: str, features: np.ndarray) -> Optional[Any]:
        """Fast model inference with performance tracking"""
        start_time = time.time()
        try:
            with self.lock:
                if model_name not in self.models:
                    logger.warning(f"Model {model_name} not loaded")
                    return None
                
                model = self.models[model_name]
                
                # Apply scaling if available
                if model_name in self.scalers:
                    features_scaled = self.scalers[model_name].transform([features])
                    prediction = model.predict(features_scaled)[0]
                else:
                    prediction = model.predict([features])[0]
                
                # Update performance metrics
                inference_time = time.time() - start_time
                perf = self.model_performance[model_name]
                perf['predictions'] += 1
                perf['avg_inference_time'] = (
                    (perf['avg_inference_time'] * (perf['predictions'] - 1) + inference_time) / 
                    perf['predictions']
                )
                
                return prediction
                
        except Exception as e:
            logger.error(f"Error in model inference for {model_name}: {e}")
            return None
    
    def predict_proba(self, model_name: str, features: np.ndarray) -> Optional[np.ndarray]:
        """Get prediction probabilities if supported by model"""
        try:
            with self.lock:
                if model_name not in self.models:
                    return None
                
                model = self.models[model_name]
                if not hasattr(model, 'predict_proba'):
                    return None
                
                # Apply scaling if available
                if model_name in self.scalers:
                    features_scaled = self.scalers[model_name].transform([features])
                    probabilities = model.predict_proba(features_scaled)[0]
                else:
                    probabilities = model.predict_proba([features])[0]
                
                return probabilities
                
        except Exception as e:
            logger.error(f"Error getting probabilities from {model_name}: {e}")
            return None
    
    def get_model_info(self) -> Dict:
        """Get information about loaded models"""
        with self.lock:
            return {
                'loaded_models': list(self.models.keys()),
                'versions': self.model_versions.copy(),
                'performance': self.model_performance.copy(),
                'scalers_loaded': list(self.scalers.keys())
            }

class DevTunnelClient:
    """Enhanced client for receiving model updates via dev tunnel"""
    def __init__(self, tunnel_config: Dict):
        self.tunnel_config = tunnel_config
        self.tunnel_url = tunnel_config.get('url', 'http://localhost:8001')
        self.auth_key = tunnel_config.get('auth_key', '')
        self.model_path = tunnel_config.get('model_path', './models/')
        self.check_interval = tunnel_config.get('check_interval', 300)  # 5 minutes
        self.last_check = None
        
    async def check_for_updates(self) -> Optional[Dict]:
        """Check for new models from local training environment"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.auth_key}'} if self.auth_key else {}
                timeout = aiohttp.ClientTimeout(total=10)
                
                async with session.get(
                    f"{self.tunnel_url}/models/status", 
                    headers=headers, 
                    timeout=timeout
                ) as response:
                    if response.status == 200:
                        self.last_check = datetime.now()
                        return await response.json()
                    else:
                        logger.warning(f"Model update check failed: {response.status}")
        except Exception as e:
            logger.error(f"Error checking for model updates: {e}")
        return None
    
    async def download_model(self, model_info: Dict) -> Optional[str]:
        """Download new model from local training environment"""
        try:
            model_name = model_info['name']
            model_version = model_info['version']
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.auth_key}'} if self.auth_key else {}
                url = f"{self.tunnel_url}/models/{model_name}/download"
                timeout = aiohttp.ClientTimeout(total=60)  # Longer timeout for downloads
                
                async with session.get(url, headers=headers, timeout=timeout) as response:
                    if response.status == 200:
                        model_data = await response.read()
                        
                        # Save model locally
                        os.makedirs(self.model_path, exist_ok=True)
                        model_file = os.path.join(self.model_path, f"{model_name}_v{model_version}.pkl")
                        
                        with open(model_file, 'wb') as f:
                            f.write(model_data)
                        
                        logger.info(f"Downloaded model {model_name} v{model_version}")
                        return model_file
                    else:
                        logger.error(f"Model download failed: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
        return None

class TechnicalAnalysisEngine:
    """Advanced technical analysis with time-series capabilities"""
    
    @staticmethod
    def extract_series_data(indicator_data: Dict, key: str, default_value: float = 50) -> List[float]:
        """Extract time series data from indicator"""
        if isinstance(indicator_data.get(key), list):
            return indicator_data[key]
        elif isinstance(indicator_data.get(key + '_series'), list):
            return indicator_data[key + '_series']
        else:
            return [indicator_data.get(key, default_value)]
    
    @staticmethod
    def detect_crossover(series1: List[float], series2: List[float]) -> str:
        """Detect crossover between two series"""
        if len(series1) < 2 or len(series2) < 2:
            return "none"
        
        if series1[-2] <= series2[-2] and series1[-1] > series2[-1]:
            return "bullish"
        elif series1[-2] >= series2[-2] and series1[-1] < series2[-1]:
            return "bearish"
        
        return "none"
    
    @staticmethod
    def calculate_trend_strength(series: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and strength from a series"""
        if len(series) < 3:
            return "neutral", 0
        
        slope = np.polyfit(range(len(series)), series, 1)[0] if len(series) > 1 else 0
        
        if slope > 0.01:
            trend = "bullish"
        elif slope < -0.01:
            trend = "bearish"
        else:
            trend = "neutral"
        
        strength = min(abs(slope) * 100, 100)
        return trend, strength
    
    @staticmethod
    def calculate_technical_indicators(data: List[Dict]) -> Dict:
        """Calculate comprehensive technical indicators from OHLCV data"""
        try:
            if not data:
                return {}
            
            df = pd.DataFrame(data)
            
            # Ensure required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    logger.warning(f"Missing required column: {col}")
                    return {}
            
            # Basic calculations
            df['returns'] = df['close'].pct_change()
            df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Moving averages
            periods = [5, 10, 20, 50, 200]
            for period in periods:
                df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
                df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['macd'] = exp1 - exp2
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['atr'] = true_range.rolling(window=14).mean()
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Stochastic
            low_min = df['low'].rolling(window=14).min()
            high_max = df['high'].rolling(window=14).max()
            df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            # Return latest indicators
            latest = df.iloc[-1]
            return {
                'rsi': latest.get('rsi', 50),
                'macd': latest.get('macd', 0),
                'macd_signal': latest.get('macd_signal', 0),
                'macd_histogram': latest.get('macd_histogram', 0),
                'bb_position': latest.get('bb_position', 0.5),
                'atr': latest.get('atr', 1),
                'stoch_k': latest.get('stoch_k', 50),
                'stoch_d': latest.get('stoch_d', 50),
                'sma_20': latest.get('sma_20', latest['close']),
                'sma_50': latest.get('sma_50', latest['close']),
                'ema_20': latest.get('ema_20', latest['close']),
                'current_price': latest['close']
            }
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}

class SignalFusionEngine:
    """Advanced signal fusion combining ML, technical analysis, and GPT-4"""
    def __init__(self):
        self.ml_weight = 0.4
        self.technical_weight = 0.4
        self.gpt4_weight = 0.2
        self.confidence_threshold = 0.6
        
    def fuse_signals(self, ml_signal: Dict = None, technical_signal: Dict = None, gpt4_signal: Dict = None) -> Dict:
        """Combine multiple signals with confidence weighting"""
        try:
            signals = []
            total_weight = 0
            
            # Process ML signal
            if ml_signal:
                signals.append({
                    'signal': ml_signal.get('signal', 'HOLD'),
                    'confidence': ml_signal.get('confidence', 0.5),
                    'weight': self.ml_weight,
                    'source': 'ML'
                })
                total_weight += self.ml_weight
            
            # Process technical signal
            if technical_signal:
                signals.append({
                    'signal': technical_signal.get('signal', 'HOLD'),
                    'confidence': technical_signal.get('confidence', 0.5) / 100,  # Convert from percentage
                    'weight': self.technical_weight,
                    'source': 'Technical'
                })
                total_weight += self.technical_weight
            
            # Process GPT-4 signal
            if gpt4_signal:
                signals.append({
                    'signal': gpt4_signal.get('signal', 'HOLD'),
                    'confidence': gpt4_signal.get('confidence', 0.5),
                    'weight': self.gpt4_weight,
                    'source': 'GPT-4'
                })
                total_weight += self.gpt4_weight
            
            if not signals:
                return self._default_signal("No signals available")
            
            # Normalize weights
            for signal in signals:
                signal['weight'] = signal['weight'] / total_weight
            
            # Calculate weighted signal scores
            buy_score = 0
            sell_score = 0
            hold_score = 0
            
            for signal in signals:
                weighted_confidence = signal['confidence'] * signal['weight']
                
                if signal['signal'] == 'BUY':
                    buy_score += weighted_confidence
                elif signal['signal'] == 'SELL':
                    sell_score += weighted_confidence
                else:
                    hold_score += weighted_confidence
            
            # Determine final signal
            max_score = max(buy_score, sell_score, hold_score)
            
            if max_score < self.confidence_threshold:
                final_signal = "HOLD"
                final_confidence = hold_score
            elif buy_score == max_score:
                final_signal = "BUY"
                final_confidence = buy_score
            elif sell_score == max_score:
                final_signal = "SELL"
                final_confidence = sell_score
            else:
                final_signal = "HOLD"
                final_confidence = hold_score
            
            # Calculate position sizing based on confidence
            lot_size = self._calculate_lot_size(final_confidence)
            
            # Calculate risk parameters
            risk_params = self._calculate_risk_parameters(
                technical_signal if technical_signal else {},
                final_confidence
            )
            
            return {
                "signal": final_signal,
                "confidence": round(final_confidence * 100, 1),
                "lot_size": lot_size,
                "sl": risk_params['sl'],
                "tp": risk_params['tp'],
                "reasoning": self._generate_reasoning(signals, final_signal),
                "risk_level": self._assess_risk_level(final_confidence),
                "signal_sources": [s['source'] for s in signals],
                "fusion_method": "confidence_weighted_averaging"
            }
            
        except Exception as e:
            logger.error(f"Error in signal fusion: {e}")
            return self._default_signal(f"Fusion error: {str(e)}")
    
    def _calculate_lot_size(self, confidence: float) -> float:
        """Calculate position size based on confidence"""
        base_lot_size = 0.01
        if confidence > 0.8:
            return base_lot_size * 2
        elif confidence > 0.7:
            return base_lot_size * 1.5
        else:
            return base_lot_size
    
    def _calculate_risk_parameters(self, technical_signal: Dict, confidence: float) -> Dict:
        """Calculate stop loss and take profit based on technical analysis and confidence"""
        base_sl = technical_signal.get('sl', 100.0)
        base_tp = technical_signal.get('tp', 200.0)
        
        # Adjust risk based on confidence
        if confidence > 0.8:
            # Higher confidence, tighter stops, larger targets
            sl = base_sl * 0.8
            tp = base_tp * 1.5
        elif confidence > 0.6:
            # Medium confidence, standard risk
            sl = base_sl
            tp = base_tp
        else:
            # Lower confidence, wider stops, smaller targets
            sl = base_sl * 1.2
            tp = base_tp * 0.8
        
        return {'sl': round(sl, 1), 'tp': round(tp, 1)}
    
    def _generate_reasoning(self, signals: List[Dict], final_signal: str) -> str:
        """Generate human-readable reasoning for the signal"""
        reasons = []
        for signal in signals:
            source = signal['source']
            signal_type = signal['signal']
            confidence = signal['confidence']
            reasons.append(f"{source}: {signal_type} ({confidence:.2f} confidence)")
        
        return f"Final: {final_signal} | " + " | ".join(reasons)
    
    def _assess_risk_level(self, confidence: float) -> str:
        """Assess risk level based on confidence"""
        if confidence > 0.8:
            return "LOW"
        elif confidence > 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _default_signal(self, reason: str) -> Dict:
        """Return default safe signal"""
        return {
            "signal": "HOLD",
            "confidence": 30,
            "sl": 100.0,
            "tp": 200.0,
            "lot_size": 0.01,
            "reasoning": reason,
            "risk_level": "HIGH",
            "signal_sources": [],
            "fusion_method": "default"
        }

# Initialize components
perf_monitor = PerformanceMonitor()
model_engine = ModelInferenceEngine()
technical_engine = TechnicalAnalysisEngine()
signal_fusion = SignalFusionEngine()

# Initialize Flask app with optimizations
app = Flask(__name__)
CORS(app)

# Configure caching
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 60
})

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=4)

# Global configuration
CONFIG = {
    'openai_api_key': None,
    'use_gpt4': False,
    'connection_pool': None,
    'last_config_update': None,
    'server_version': '5.0.0-consolidated',
    'dev_tunnel': {
        'enabled': False,
        'config': {}
    }
}

# Dev tunnel client (initialized later if configured)
dev_tunnel_client = None

async def get_connection_pool():
    """Get or create HTTP connection pool for external requests"""
    if CONFIG['connection_pool'] is None:
        CONFIG['connection_pool'] = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(
                limit=50,
                ttl_dns_cache=300,
                enable_cleanup_closed=True
            ),
            timeout=aiohttp.ClientTimeout(total=10)
        )
    return CONFIG['connection_pool']

def load_config() -> bool:
    """Load configuration with intelligent caching"""
    try:
        # Check cache (5 minute cache)
        if (CONFIG['last_config_update'] and 
            (datetime.now() - CONFIG['last_config_update']).seconds < 300):
            return True
        
        # Try multiple config paths
        config_paths = [
            'config/settings.json',
            'aiGoldScalper/config/settings.json',
            os.path.join(os.path.dirname(__file__), 'config', 'settings.json')
        ]
        
        settings = None
        for config_path in config_paths:
            try:
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        settings = json.load(f)
                    logger.info(f"Config loaded from: {config_path}")
                    break
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
                continue
        
        if not settings:
            logger.warning("No config file found, using defaults")
            return False
        
        # Configure OpenAI
        api_key = settings.get('openai_api_key', '')
        if api_key and api_key != 'YOUR_OPENAI_API_KEY_HERE':
            CONFIG['openai_api_key'] = api_key
            openai.api_key = api_key
            CONFIG['use_gpt4'] = True
            logger.info("OpenAI API key configured")
        
        # Configure dev tunnel
        dev_tunnel_config = settings.get('dev_tunnel', {})
        if dev_tunnel_config.get('enabled', False):
            CONFIG['dev_tunnel'] = dev_tunnel_config
            global dev_tunnel_client
            dev_tunnel_client = DevTunnelClient(dev_tunnel_config)
            logger.info("Dev tunnel client configured")
        
        CONFIG['last_config_update'] = datetime.now()
        return True
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False

def initialize_models():
    """Initialize ML models from the trained models directory"""
    models_dir = "models/trained"
    
    try:
        # Load feature list
        feature_path = os.path.join(models_dir, "feature_list.pkl")
        if os.path.exists(feature_path):
            model_engine.feature_list = joblib.load(feature_path)
            logger.info(f"Loaded {len(model_engine.feature_list)} features")
        
        # Load Random Forest Classifier
        rf_model_path = os.path.join(models_dir, "rf_classifier.pkl")
        rf_scaler_path = os.path.join(models_dir, "rf_classifier_scaler.pkl")
        if os.path.exists(rf_model_path):
            model_engine.load_model("rf_classifier", rf_model_path, rf_scaler_path, "1.0")
        
        # Load Random Forest Regressor
        rf_reg_path = os.path.join(models_dir, "rf_regressor.pkl")
        rf_reg_scaler_path = os.path.join(models_dir, "rf_regressor_scaler.pkl")
        if os.path.exists(rf_reg_path):
            model_engine.load_model("rf_regressor", rf_reg_path, rf_reg_scaler_path, "1.0")
        
        logger.info("Model initialization complete")
        
    except Exception as e:
        logger.error(f"Error initializing models: {e}")

# Initialize on startup
load_config()
initialize_models()

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        stats = perf_monitor.get_stats()
        model_info = model_engine.get_model_info()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "server_version": CONFIG['server_version'],
            "gpt4_enabled": CONFIG['use_gpt4'],
            "dev_tunnel_enabled": CONFIG['dev_tunnel'].get('enabled', False),
            "models_loaded": model_info['loaded_models'],
            "performance": stats,
            "last_config_update": CONFIG['last_config_update'].isoformat() if CONFIG['last_config_update'] else None
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.route('/ai_signal', methods=['POST'])
def get_ai_signal():
    """Main endpoint for consolidated AI trading signals"""
    start_time = time.time()
    cached = False
    error = False
    
    try:
        # Get market data
        market_data = request.get_json()
        if not market_data:
            error = True
            return jsonify({"error": "No market data provided"}), 400
        
        # Handle test requests
        if market_data.get('test', False):
            logger.info("Test request received")
            response = {
                "signal": "HOLD",
                "confidence": 95,
                "sl": 100.0,
                "tp": 200.0,
                "lot_size": 0.01,
                "reasoning": "Test response - Consolidated AI server is working correctly",
                "timestamp": datetime.now().isoformat(),
                "test_mode": True,
                "server_version": CONFIG['server_version']
            }
            perf_monitor.log_request(time.time() - start_time, error=False, cached=False)
            return jsonify(response)
        
        # Check cache for similar requests
        cache_key = hashlib.md5(str(sorted(market_data.items())).encode()).hexdigest()
        cached_result = cache.get(cache_key)
        
        if cached_result:
            cached = True
            logger.info("Serving cached result")
            perf_monitor.log_request(time.time() - start_time, error=False, cached=True)
            return jsonify(cached_result)
        
        logger.info(f"Processing signal request for {market_data.get('symbol', 'Unknown')}")
        
        # Prepare signals from different sources
        ml_signal = None
        technical_signal = None
        gpt4_signal = None
        
        # 1. Technical Analysis Signal
        try:
            technical_signal = calculate_technical_signal(market_data)
            logger.info("Technical analysis completed")
        except Exception as e:
            logger.error(f"Technical analysis error: {e}")
        
        # 2. ML Model Signal (if models are loaded)
        try:
            if model_engine.models:
                ml_signal = calculate_ml_signal(market_data)
                logger.info("ML prediction completed")
        except Exception as e:
            logger.error(f"ML prediction error: {e}")
        
        # 3. GPT-4 Signal (if configured)
        try:
            if CONFIG['use_gpt4']:
                gpt4_signal = calculate_gpt4_signal(market_data)
                logger.info("GPT-4 analysis completed")
        except Exception as e:
            logger.error(f"GPT-4 analysis error: {e}")
        
        # 4. Fuse all signals
        final_signal = signal_fusion.fuse_signals(ml_signal, technical_signal, gpt4_signal)
        final_signal['timestamp'] = datetime.now().isoformat()
        final_signal['server_version'] = CONFIG['server_version']
        
        # Cache the result
        cache.set(cache_key, final_signal, timeout=30)  # 30 second cache
        
        # Log performance
        perf_monitor.log_request(time.time() - start_time, error=False, cached=False)
        perf_monitor.log_signal_accuracy(final_signal['signal'])
        
        return jsonify(final_signal)
        
    except Exception as e:
        error = True
        logger.error(f"Signal processing error: {e}")
        perf_monitor.log_request(time.time() - start_time, error=True, cached=cached)
        return jsonify({
            "error": "Signal processing failed",
            "details": str(e),
            "timestamp": datetime.now().isoformat(),
            "server_version": CONFIG['server_version']
        }), 500

def calculate_technical_signal(market_data: Dict) -> Dict:
    """Enhanced technical analysis combining multiple implementations"""
    try:
        # Use the enhanced technical analysis from the production server
        bid = market_data.get('bid', 0)
        
        # Extract time series data
        rsi_data = market_data.get('rsi', {})
        rsi_h1_series = technical_engine.extract_series_data(rsi_data, 'h1', 50)
        
        macd_data = market_data.get('macd', {})
        macd_series = technical_engine.extract_series_data(macd_data, 'h1', 0)
        
        # Calculate current values
        rsi_current = rsi_h1_series[-1] if rsi_h1_series else 50
        macd_current = macd_series[-1] if macd_series else 0
        
        # Bollinger Bands
        bb = market_data.get('bollinger', {})
        bb_upper = bb.get('upper', bid + 5)
        bb_lower = bb.get('lower', bid - 5)
        
        # Initialize scoring
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # RSI Analysis
        if rsi_current < 30:
            buy_score += 25
            reasons.append(f"RSI oversold ({rsi_current:.1f})")
        elif rsi_current > 70:
            sell_score += 25
            reasons.append(f"RSI overbought ({rsi_current:.1f})")
        
        # MACD Analysis
        if macd_current > 0:
            buy_score += 10
            reasons.append("MACD bullish")
        else:
            sell_score += 10
            reasons.append("MACD bearish")
        
        # Bollinger Bands Analysis
        if bid > bb_upper:
            sell_score += 15
            reasons.append("Price above upper BB")
        elif bid < bb_lower:
            buy_score += 15
            reasons.append("Price below lower BB")
        
        # Determine signal
        if buy_score > sell_score and buy_score > 30:
            signal = "BUY"
            confidence = min(95, max(50, buy_score))
        elif sell_score > buy_score and sell_score > 30:
            signal = "SELL"
            confidence = min(95, max(50, sell_score))
        else:
            signal = "HOLD"
            confidence = 40
        
        # Calculate risk parameters
        atr = market_data.get('advanced_indicators', {}).get('atr_h1', 5)
        if signal == "BUY":
            sl = atr * 1.5
            tp = atr * 3.0
        elif signal == "SELL":
            sl = atr * 1.5
            tp = atr * 3.0
        else:
            sl = 100.0
            tp = 200.0
        
        return {
            "signal": signal,
            "confidence": confidence,
            "sl": round(sl, 1),
            "tp": round(tp, 1),
            "reasoning": " | ".join(reasons) if reasons else "No clear signals",
            "source": "technical_analysis"
        }
        
    except Exception as e:
        logger.error(f"Technical analysis error: {e}")
        return {
            "signal": "HOLD",
            "confidence": 30,
            "sl": 100.0,
            "tp": 200.0,
            "reasoning": f"Technical analysis error: {str(e)}",
            "source": "technical_analysis"
        }

def calculate_ml_signal(market_data: Dict) -> Optional[Dict]:
    """Calculate ML-based signal using loaded models"""
    try:
        if not model_engine.feature_list:
            return None
        
        # Prepare features (simplified feature extraction)
        features = []
        
        # Basic price features
        bid = market_data.get('bid', 0)
        features.append(bid)
        
        # Technical indicators
        rsi = market_data.get('rsi', {}).get('h1', 50)
        features.append(rsi)
        
        macd = market_data.get('macd', {}).get('h1', 0)
        features.append(macd)
        
        # Pad or trim features to match expected input size
        expected_features = len(model_engine.feature_list)
        while len(features) < expected_features:
            features.append(0.0)
        features = features[:expected_features]
        
        # Get predictions from available models
        predictions = {}
        
        if 'rf_classifier' in model_engine.models:
            prediction = model_engine.predict('rf_classifier', np.array(features))
            probabilities = model_engine.predict_proba('rf_classifier', np.array(features))
            
            if prediction is not None:
                signal_map = {0: "SELL", 1: "HOLD", 2: "BUY"}  # Adjust based on your model
                predictions['rf_classifier'] = {
                    'signal': signal_map.get(prediction, "HOLD"),
                    'confidence': np.max(probabilities) if probabilities is not None else 0.6
                }
        
        # Combine ML predictions if multiple models
        if predictions:
            # Simple majority voting for now
            signals = [p['signal'] for p in predictions.values()]
            confidences = [p['confidence'] for p in predictions.values()]
            
            from collections import Counter
            signal_counts = Counter(signals)
            most_common_signal = signal_counts.most_common(1)[0][0]
            avg_confidence = np.mean(confidences)
            
            return {
                "signal": most_common_signal,
                "confidence": avg_confidence,
                "reasoning": f"ML models prediction: {dict(signal_counts)}",
                "source": "ml_models",
                "models_used": list(predictions.keys())
            }
        
        return None
        
    except Exception as e:
        logger.error(f"ML signal calculation error: {e}")
        return None

async def calculate_gpt4_signal(market_data: Dict) -> Optional[Dict]:
    """Calculate GPT-4 based market analysis signal"""
    try:
        if not CONFIG['use_gpt4']:
            return None
        
        # Prepare market context for GPT-4
        context = f"""
        Analyze XAUUSD (Gold) market data:
        - Current Price: {market_data.get('bid', 'N/A')}
        - RSI H1: {market_data.get('rsi', {}).get('h1', 'N/A')}
        - MACD H1: {market_data.get('macd', {}).get('h1', 'N/A')}
        - Session: {market_data.get('session', 'Unknown')}
        - Minutes to News: {market_data.get('minutes_to_news', 'N/A')}
        
        Provide a trading signal (BUY/SELL/HOLD) with confidence (0-1) and brief reasoning.
        Format: SIGNAL|CONFIDENCE|REASONING
        """
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert forex trader analyzing XAUUSD."},
                {"role": "user", "content": context}
            ],
            max_tokens=150,
            temperature=0.1
        )
        
        result = response.choices[0].message.content.strip()
        parts = result.split('|')
        
        if len(parts) >= 3:
            signal = parts[0].strip().upper()
            confidence = float(parts[1].strip())
            reasoning = parts[2].strip()
            
            return {
                "signal": signal,
                "confidence": confidence,
                "reasoning": reasoning,
                "source": "gpt4_analysis"
            }
        
        return None
        
    except Exception as e:
        logger.error(f"GPT-4 analysis error: {e}")
        return None

@app.route('/models/status', methods=['GET'])
def get_models_status():
    """Get status of loaded models"""
    try:
        model_info = model_engine.get_model_info()
        return jsonify({
            "status": "success",
            "models": model_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Model status error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/performance', methods=['GET'])
def get_performance_stats():
    """Get detailed performance statistics"""
    try:
        stats = perf_monitor.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Performance stats error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Consolidated AI Server v5.0.0")
    logger.info(f"Models loaded: {list(model_engine.models.keys())}")
    logger.info(f"GPT-4 enabled: {CONFIG['use_gpt4']}")
    logger.info(f"Dev tunnel enabled: {CONFIG['dev_tunnel'].get('enabled', False)}")
    
    # Use Waitress WSGI server for production
    try:
        from waitress import serve
        logger.info("Starting with Waitress WSGI server (Production Mode)")
        serve(app, host='0.0.0.0', port=5000, threads=4)
    except ImportError:
        logger.warning("Waitress not available, falling back to Flask dev server")
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
