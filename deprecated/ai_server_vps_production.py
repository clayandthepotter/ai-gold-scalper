#!/usr/bin/env python3
"""
AI Gold Scalper - VPS Production Server (Lightweight)
Optimized for production trading with inference-only capabilities
Designed to work with dev tunnels for model updates from powerful local hardware

Version: 4.0.0-vps-production
Features:
- Lightweight inference engine for real-time trading
- GPT-4 integration for advanced signal analysis
- Advanced technical analysis with optimized performance
- Dev tunnel integration for seamless model updates
- Comprehensive monitoring and error handling
- Risk management integration
- Production-ready with minimal resource usage
"""

import os
import json
import logging
import numpy as np
import asyncio
import aiohttp
import time
import hashlib
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
import openai
from typing import Dict, List, Tuple, Optional, Any
import joblib
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
import pickle
import threading

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('vps_ai_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Production performance monitoring"""
    def __init__(self):
        self.request_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.error_count = 0
        self.start_time = datetime.now()
        self.model_updates = 0
        self.last_model_update = None
        
    def log_request(self, duration, error=False):
        self.request_times.append(duration)
        self.total_requests += 1
        if error:
            self.error_count += 1
        
        # Keep only last 1000 requests for performance
        if len(self.request_times) > 1000:
            self.request_times.pop(0)
    
    def log_model_update(self):
        self.model_updates += 1
        self.last_model_update = datetime.now()
    
    def get_stats(self):
        if not self.request_times:
            return {"status": "no_data"}
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "uptime_hours": round(uptime / 3600, 2),
            "avg_response_time_ms": round(np.mean(self.request_times) * 1000, 2),
            "median_response_time_ms": round(np.median(self.request_times) * 1000, 2),
            "p95_response_time_ms": round(np.percentile(self.request_times, 95) * 1000, 2),
            "cache_hit_rate": round(self.cache_hits / max(self.cache_hits + self.cache_misses, 1) * 100, 2),
            "total_requests": self.total_requests,
            "error_rate": round(self.error_count / max(self.total_requests, 1) * 100, 2),
            "requests_per_hour": round(self.total_requests / max(uptime / 3600, 0.001), 1),
            "model_updates": self.model_updates,
            "last_model_update": self.last_model_update.isoformat() if self.last_model_update else None
        }

class ModelInferenceEngine:
    """Lightweight model inference for production trading"""
    def __init__(self):
        self.models = {}
        self.model_versions = {}
        self.model_performance = {}
        self.lock = threading.Lock()
        
    def load_model(self, model_name, model_path, version="1.0"):
        """Load model for inference"""
        try:
            with self.lock:
                if os.path.exists(model_path):
                    model = joblib.load(model_path)
                    self.models[model_name] = model
                    self.model_versions[model_name] = version
                    self.model_performance[model_name] = {
                        'loaded_at': datetime.now().isoformat(),
                        'predictions': 0,
                        'avg_inference_time': 0.0
                    }
                    logger.info(f"Model {model_name} v{version} loaded successfully")
                    return True
                else:
                    logger.warning(f"Model file not found: {model_path}")
                    return False
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            return False
    
    def predict(self, model_name, features):
        """Fast model inference"""
        start_time = time.time()
        try:
            with self.lock:
                if model_name not in self.models:
                    return None
                
                model = self.models[model_name]
                prediction = model.predict([features])[0] if hasattr(model, 'predict') else None
                
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
            logger.error(f"Error in model inference: {e}")
            return None
    
    def get_model_info(self):
        """Get information about loaded models"""
        with self.lock:
            return {
                'loaded_models': list(self.models.keys()),
                'versions': self.model_versions.copy(),
                'performance': self.model_performance.copy()
            }

class DevTunnelClient:
    """Client for receiving model updates via dev tunnel"""
    def __init__(self, tunnel_config):
        self.tunnel_config = tunnel_config
        self.tunnel_url = tunnel_config.get('url', 'http://localhost:8001')
        self.auth_key = tunnel_config.get('auth_key', '')
        self.model_path = tunnel_config.get('model_path', './models/')
        
    async def check_for_updates(self):
        """Check for new models from local training environment"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.auth_key}'} if self.auth_key else {}
                async with session.get(f"{self.tunnel_url}/models/status", headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            logger.error(f"Error checking for model updates: {e}")
        return None
    
    async def download_model(self, model_info):
        """Download new model from local training environment"""
        try:
            model_name = model_info['name']
            model_version = model_info['version']
            
            async with aiohttp.ClientSession() as session:
                headers = {'Authorization': f'Bearer {self.auth_key}'} if self.auth_key else {}
                url = f"{self.tunnel_url}/models/{model_name}/download"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        model_data = await response.read()
                        
                        # Save model locally
                        os.makedirs(self.model_path, exist_ok=True)
                        model_file = os.path.join(self.model_path, f"{model_name}_v{model_version}.pkl")
                        
                        with open(model_file, 'wb') as f:
                            f.write(model_data)
                        
                        logger.info(f"Downloaded model {model_name} v{model_version}")
                        return model_file
        except Exception as e:
            logger.error(f"Error downloading model: {e}")
        return None

# Initialize Flask app with optimizations
app = Flask(__name__)
CORS(app)

# Import and register workspace blueprint
from workspace_server_integration import workspace_bp
app.register_blueprint(workspace_bp)

# Configure caching for production
cache = Cache(app, config={
    'CACHE_TYPE': 'simple',
    'CACHE_DEFAULT_TIMEOUT': 45  # Shorter cache for live trading
})

# Thread pool for parallel processing
executor = ThreadPoolExecutor(max_workers=2)  # Lightweight for VPS

# Global configuration
CONFIG = {
    'openai_api_key': None,
    'use_gpt4': False,
    'signal_weights': {
        'technical': 0.7,  # Higher weight for reliable technical analysis
        'gpt4': 0.25,
        'ml': 0.05  # Lower weight until models are validated
    },
    'cache_enabled': True,
    'connection_pool': None,
    'last_config_update': None,
    'server_version': '4.0.0-vps-production',
    'dev_tunnel': {
        'enabled': False,
        'url': 'http://localhost:8001',
        'auth_key': '',
        'check_interval': 300  # Check every 5 minutes
    }
}

# Global instances
perf_monitor = PerformanceMonitor()
model_engine = ModelInferenceEngine()
tunnel_client = None

def load_config():
    """Load configuration optimized for VPS production"""
    try:
        config_paths = [
            './config/settings.json',
            './settings.json',
            '../config/settings.json'
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
            
        # Set OpenAI API key
        api_key = settings.get('openai_api_key', '')
        if api_key and api_key != 'YOUR_OPENAI_API_KEY_HERE':
            CONFIG['openai_api_key'] = api_key
            openai.api_key = api_key
            CONFIG['use_gpt4'] = True
            logger.info("OpenAI API key configured")
        else:
            logger.warning("No valid OpenAI API key found")
        
        # Load dev tunnel configuration
        dev_tunnel_config = settings.get('dev_tunnel', {})
        CONFIG['dev_tunnel'].update(dev_tunnel_config)
        
        if CONFIG['dev_tunnel']['enabled']:
            global tunnel_client
            tunnel_client = DevTunnelClient(CONFIG['dev_tunnel'])
            logger.info("Dev tunnel client configured")
        
        # Update signal weights
        CONFIG['signal_weights'].update(settings.get('signal_weights', {}))
        
        CONFIG['last_config_update'] = datetime.now()
        return True
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False

def extract_series_data(indicator_data: Dict, key: str, default_value: float = 50) -> np.ndarray:
    """Optimized data extraction"""
    if isinstance(indicator_data.get(key), list):
        return np.array(indicator_data[key])
    elif isinstance(indicator_data.get(key + '_series'), list):
        return np.array(indicator_data[key + '_series'])
    else:
        return np.array([indicator_data.get(key, default_value)])

@lru_cache(maxsize=256)
def calculate_technical_score_cached(cache_key: str, rsi_h1: float, macd_h1: float, 
                                   ma_fast: float, ma_slow: float, session: str) -> Dict:
    """Optimized technical analysis with aggressive caching"""
    try:
        buy_score = 0
        sell_score = 0
        reasons = []
        
        # RSI Analysis (optimized)
        if rsi_h1 < 30:
            buy_score += 30
            reasons.append(f"RSI oversold ({rsi_h1:.1f})")
        elif rsi_h1 > 70:
            sell_score += 30
            reasons.append(f"RSI overbought ({rsi_h1:.1f})")
        
        # MACD Analysis (optimized)
        if macd_h1 > 0:
            buy_score += 15
            reasons.append("MACD positive")
        else:
            sell_score += 15
            reasons.append("MACD negative")
        
        # Moving Average Analysis (optimized)
        if ma_fast > ma_slow:
            separation = (ma_fast - ma_slow) / ma_slow * 100
            if separation > 0.5:
                buy_score += 25
                reasons.append("Strong bullish MA alignment")
            else:
                buy_score += 15
                reasons.append("Bullish MA alignment")
        else:
            separation = (ma_slow - ma_fast) / ma_slow * 100
            if separation > 0.5:
                sell_score += 25
                reasons.append("Strong bearish MA alignment")
            else:
                sell_score += 15
                reasons.append("Bearish MA alignment")
        
        # Session boost (optimized)
        if session in ['London', 'NY'] and (buy_score > sell_score or sell_score > buy_score):
            reasons.append(f"Active {session} session")
        
        # Determine signal
        if buy_score > sell_score and buy_score >= 40:
            signal = "BUY"
            confidence = min(95, 50 + buy_score)
        elif sell_score > buy_score and sell_score >= 40:
            signal = "SELL"
            confidence = min(95, 50 + sell_score)
        else:
            signal = "HOLD"
            confidence = 40
        
        # Calculate SL/TP (simplified for production)
        atr = 5.0  # Default ATR for gold
        sl = round(atr * 1.5, 1)
        tp = round(atr * 3.0, 1)
        
        return {
            "signal": signal,
            "confidence": confidence,
            "sl": sl,
            "tp": tp,
            "reasoning": "; ".join(reasons[:4]),  # Top 4 reasons
            "buy_score": buy_score,
            "sell_score": sell_score,
            "risk_level": "LOW" if confidence > 75 else "MEDIUM" if confidence > 50 else "HIGH"
        }
        
    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        return {
            "signal": "HOLD",
            "confidence": 0,
            "sl": 100,
            "tp": 200,
            "reasoning": "Technical analysis error",
            "error": str(e)
        }

async def get_gpt4_signal_async(market_data: Dict) -> Optional[Dict]:
    """Optimized GPT-4 analysis for production"""
    if not CONFIG['use_gpt4']:
        return None
        
    try:
        bid = market_data.get('bid', 0)
        rsi_h1 = market_data.get('rsi', {}).get('h1', 50)
        macd_h1 = market_data.get('macd', {}).get('h1', 0)
        session = market_data.get('session', 'Unknown')
        
        # Simplified prompt for faster response
        prompt = f"""Gold XAUUSD Analysis:
Price: ${bid:.2f}, RSI: {rsi_h1:.1f}, MACD: {macd_h1:.5f}, Session: {session}

Provide quick trading signal with 2:1 RR requirement.
JSON only: {{"signal": "BUY/SELL/HOLD", "confidence": 0-100, "reasoning": "brief"}}"""
        
        # Faster timeout for production
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Expert gold trader. Quick 2:1 RR signals only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.1
            ),
            timeout=5.0  # Faster timeout for production
        )
        
        content = response.choices[0].message.content
        if '{' in content and '}' in content:
            json_str = content[content.find('{'):content.rfind('}')+1]
            return json.loads(json_str)
            
    except Exception as e:
        logger.error(f"GPT-4 error: {e}")
        return None

def get_ml_signal(market_data: Dict) -> Optional[Dict]:
    """Get ML model prediction if available"""
    try:
        if not model_engine.models:
            return None
        
        # Extract features (simplified for production)
        features = [
            market_data.get('bid', 2000),
            market_data.get('rsi', {}).get('h1', 50),
            market_data.get('macd', {}).get('h1', 0),
            market_data.get('moving_average', {}).get('fast', 2000),
            market_data.get('moving_average', {}).get('slow', 2000)
        ]
        
        # Use first available model
        model_name = list(model_engine.models.keys())[0]
        prediction = model_engine.predict(model_name, features)
        
        if prediction is not None:
            # Convert prediction to signal format
            if prediction > 0.6:
                signal = "BUY"
                confidence = min(85, int(prediction * 100))
            elif prediction < 0.4:
                signal = "SELL"
                confidence = min(85, int((1 - prediction) * 100))
            else:
                signal = "HOLD"
                confidence = 40
            
            return {
                "signal": signal,
                "confidence": confidence,
                "reasoning": f"ML model prediction: {prediction:.3f}",
                "model": model_name
            }
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
    
    return None

def combine_signals_weighted(signals: List[Tuple[str, Dict, float]]) -> Dict:
    """Optimized signal combination for production"""
    if not signals:
        return {"signal": "HOLD", "confidence": 0, "reasoning": "No signals available"}
    
    signal_weights = {"BUY": 0, "SELL": 0, "HOLD": 0}
    total_confidence = 0
    reasons = []
    
    for source, signal_data, weight in signals:
        if signal_data and isinstance(signal_data, dict):
            signal = signal_data.get('signal', 'HOLD')
            confidence = signal_data.get('confidence', 0) / 100.0
            
            signal_weights[signal] += weight * confidence
            total_confidence += weight * confidence
            
            if signal_data.get('reasoning'):
                reasons.append(f"{source}: {signal_data['reasoning'][:50]}")
    
    # Determine final signal
    max_weight = max(signal_weights.values())
    if max_weight == 0:
        return {"signal": "HOLD", "confidence": 0, "reasoning": "No valid signals"}
    
    final_signal = next(s for s, w in signal_weights.items() if w == max_weight)
    final_confidence = min(95, int((max_weight / sum(signal_weights.values())) * 100))
    
    # Get SL/TP from technical analysis (most reliable)
    tech_signal = next((s[1] for s in signals if s[0] == 'technical'), {})
    
    return {
        "signal": final_signal,
        "confidence": final_confidence,
        "reasoning": " | ".join(reasons[:2]),  # Keep it short for production
        "sl": tech_signal.get('sl', 100),
        "tp": tech_signal.get('tp', 200),
        "risk_level": tech_signal.get('risk_level', 'MEDIUM')
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Production health check"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": CONFIG['server_version'],
        "components": {
            "gpt4": CONFIG['use_gpt4'],
            "ml_models": len(model_engine.models),
            "technical_analysis": True,
            "caching": CONFIG['cache_enabled'],
            "dev_tunnel": CONFIG['dev_tunnel']['enabled']
        },
        "performance": perf_monitor.get_stats(),
        "models": model_engine.get_model_info()
    })

@app.route('/ai_signal', methods=['POST'])
async def get_ai_signal():
    """Main signal endpoint optimized for production"""
    start_time = time.time()
    
    try:
        market_data = request.get_json()
        if not market_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Handle test requests
        if market_data.get('test', False):
            return jsonify({
                "signal": "HOLD",
                "confidence": 95,
                "reasoning": "VPS server test successful",
                "test_mode": True,
                "timestamp": datetime.now().isoformat()
            })
        
        # Generate cache key for production efficiency
        cache_key_data = {
            'bid': round(market_data.get('bid', 0), 1),
            'rsi_h1': round(market_data.get('rsi', {}).get('h1', 50), 1),
            'macd_h1': round(market_data.get('macd', {}).get('h1', 0), 4),
            'session': market_data.get('session', 'unknown'),
            'timestamp': int(time.time() / 30)  # 30-second cache buckets
        }
        cache_key = hashlib.md5(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()
        
        # Check cache first
        if CONFIG['cache_enabled']:
            cached_result = cache.get(f"signal_{cache_key}")
            if cached_result:
                perf_monitor.cache_hits += 1
                perf_monitor.log_request(time.time() - start_time)
                return jsonify(cached_result)
            else:
                perf_monitor.cache_misses += 1
        
        # Extract weights from settings
        settings = market_data.get('settings', {})
        weights = settings.get('weights', CONFIG['signal_weights'])
        
        # Collect signals with production optimizations
        signals = []
        
        # 1. Technical Analysis (always available, highest priority)
        rsi_h1 = market_data.get('rsi', {}).get('h1', 50)
        macd_h1 = market_data.get('macd', {}).get('h1', 0)
        ma_data = market_data.get('moving_average', {})
        ma_fast = ma_data.get('fast', 0)
        ma_slow = ma_data.get('slow', 0)
        session = market_data.get('session', 'Unknown')
        
        tech_cache_key = f"{rsi_h1}_{macd_h1}_{ma_fast}_{ma_slow}_{session}"
        tech_signal = calculate_technical_score_cached(
            tech_cache_key, rsi_h1, macd_h1, ma_fast, ma_slow, session
        )
        if tech_signal:
            signals.append(('technical', tech_signal, weights.get('technical', 0.7)))
        
        # 2. GPT-4 Analysis (async, with timeout)
        if CONFIG['use_gpt4'] and weights.get('gpt4', 0) > 0:
            try:
                gpt_signal = await asyncio.wait_for(
                    get_gpt4_signal_async(market_data), 
                    timeout=6.0  # Slightly longer timeout
                )
                if gpt_signal:
                    signals.append(('gpt4', gpt_signal, weights.get('gpt4', 0.25)))
            except asyncio.TimeoutError:
                logger.warning("GPT-4 timed out")
        
        # 3. ML Models (if available)
        if weights.get('ml', 0) > 0:
            ml_signal = get_ml_signal(market_data)
            if ml_signal:
                signals.append(('ml', ml_signal, weights.get('ml', 0.05)))
        
        # Combine signals
        final_signal = combine_signals_weighted(signals)
        
        # Add metadata
        final_signal.update({
            'timestamp': datetime.now().isoformat(),
            'symbol': market_data.get('symbol', 'XAUUSD'),
            'lot_size': 0.01,
            'processing_time': round(time.time() - start_time, 3),
            'server_version': CONFIG['server_version']
        })
        
        # Cache result for production efficiency
        if CONFIG['cache_enabled']:
            cache.set(f"signal_{cache_key}", final_signal, timeout=30)
        
        # Log performance
        perf_monitor.log_request(time.time() - start_time)
        logger.info(f"Signal: {final_signal['signal']} ({final_signal['confidence']}%) in {final_signal['processing_time']}s")
        
        return jsonify(final_signal)
        
    except Exception as e:
        logger.error(f"Signal processing error: {e}")
        perf_monitor.log_request(time.time() - start_time, error=True)
        return jsonify({
            "error": str(e),
            "signal": "HOLD",
            "confidence": 0,
            "reasoning": "Processing error",
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/models/update', methods=['POST'])
def update_model():
    """Endpoint for dev tunnel model updates"""
    try:
        model_info = request.get_json()
        if not model_info:
            return jsonify({"error": "No model info provided"}), 400
        
        model_name = model_info.get('name')
        model_version = model_info.get('version')
        model_data = model_info.get('data')  # Base64 encoded model
        
        if not all([model_name, model_version, model_data]):
            return jsonify({"error": "Missing required fields"}), 400
        
        # Decode and save model
        import base64
        model_bytes = base64.b64decode(model_data)
        
        os.makedirs('./models', exist_ok=True)
        model_path = f"./models/{model_name}_v{model_version}.pkl"
        
        with open(model_path, 'wb') as f:
            f.write(model_bytes)
        
        # Load model into inference engine
        success = model_engine.load_model(model_name, model_path, model_version)
        
        if success:
            perf_monitor.log_model_update()
            logger.info(f"Model {model_name} v{model_version} updated successfully")
            return jsonify({
                "status": "success",
                "message": f"Model {model_name} v{model_version} updated",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({"error": "Failed to load model"}), 500
            
    except Exception as e:
        logger.error(f"Model update error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Production status endpoint"""
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": CONFIG['server_version'],
        "environment": "vps-production",
        "components": {
            "gpt4": CONFIG['use_gpt4'],
            "ml_models": list(model_engine.models.keys()),
            "technical_analysis": True,
            "caching": CONFIG['cache_enabled'],
            "dev_tunnel": CONFIG['dev_tunnel']['enabled']
        },
        "performance": perf_monitor.get_stats(),
        "models": model_engine.get_model_info()
    })

async def model_update_checker():
    """Background task to check for model updates via dev tunnel"""
    if not CONFIG['dev_tunnel']['enabled'] or not tunnel_client:
        return
    
    while True:
        try:
            await asyncio.sleep(CONFIG['dev_tunnel']['check_interval'])
            
            updates = await tunnel_client.check_for_updates()
            if updates and updates.get('new_models'):
                logger.info(f"Found {len(updates['new_models'])} model updates")
                
                for model_info in updates['new_models']:
                    model_file = await tunnel_client.download_model(model_info)
                    if model_file:
                        success = model_engine.load_model(
                            model_info['name'], 
                            model_file, 
                            model_info['version']
                        )
                        if success:
                            perf_monitor.log_model_update()
                            logger.info(f"Auto-updated model: {model_info['name']}")
        except Exception as e:
            logger.error(f"Model update checker error: {e}")

def initialize():
    """Initialize the VPS production server"""
    logger.info("Initializing AI Gold Scalper VPS Production Server v4.0.0")
    
    # Load configuration
    load_config()
    
    # Load any existing models
    models_dir = './models'
    if os.path.exists(models_dir):
        for filename in os.listdir(models_dir):
            if filename.endswith('.pkl'):
                model_name = filename.split('_v')[0] if '_v' in filename else filename.split('.')[0]
                model_path = os.path.join(models_dir, filename)
                model_engine.load_model(model_name, model_path)
    
    # Start background model update checker if dev tunnel is enabled
    if CONFIG['dev_tunnel']['enabled']:
        import threading
        update_thread = threading.Thread(target=lambda: asyncio.run(model_update_checker()))
        update_thread.daemon = True
        update_thread.start()
        logger.info("Model update checker started")
    
    logger.info("VPS Production Server initialization complete")
    logger.info(f"GPT-4 enabled: {CONFIG['use_gpt4']}")
    logger.info(f"ML models loaded: {len(model_engine.models)}")
    logger.info(f"Dev tunnel enabled: {CONFIG['dev_tunnel']['enabled']}")
    logger.info(f"Caching enabled: {CONFIG['cache_enabled']}")

if __name__ == '__main__':
    # Initialize
    initialize()
    
    # Get host and port
    host = os.environ.get('AI_SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('AI_SERVER_PORT', 5000))
    
    # Run with production server
    logger.info(f"Starting VPS production server on {host}:{port}")
    
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=4)
    except ImportError:
        logger.warning("Waitress not available, using Flask development server")
        app.run(host=host, port=port, debug=False, threaded=True)
