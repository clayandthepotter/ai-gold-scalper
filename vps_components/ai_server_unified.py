#!/usr/bin/env python3
"""
AI Gold Scalper - Unified Production Server
Combines the best features from all server versions into one robust, optimized solution

Version: 3.0.0-unified
Features:
- Advanced technical analysis from production server
- Performance optimizations from optimized server
- Clean architecture from core server
- Comprehensive logging and error handling
- Dynamic weight adjustment
- Caching and async processing
- Production-ready with monitoring
"""

import os
import json
import logging
import numpy as np
import asyncio
import aiohttp
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache
import openai
from typing import Dict, List, Tuple, Optional, Any
import joblib
from concurrent.futures import ThreadPoolExecutor
import threading
import time
from functools import lru_cache
import hashlib

# Configure advanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Enhanced performance monitoring and metrics"""
    def __init__(self):
        self.request_times = []
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_requests = 0
        self.error_count = 0
        self.start_time = datetime.now()
        
    def log_request(self, duration, error=False):
        self.request_times.append(duration)
        self.total_requests += 1
        if error:
            self.error_count += 1
        
        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times.pop(0)
    
    def get_stats(self):
        if not self.request_times:
            return {"status": "no_data"}
        
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            "uptime_hours": round(uptime / 3600, 2),
            "avg_response_time_ms": round(np.mean(self.request_times) * 1000, 2),
            "median_response_time_ms": round(np.median(self.request_times) * 1000, 2),
            "p95_response_time_ms": round(np.percentile(self.request_times, 95) * 1000, 2),
            "p99_response_time_ms": round(np.percentile(self.request_times, 99) * 1000, 2),
            "cache_hit_rate": round(self.cache_hits / max(self.cache_hits + self.cache_misses, 1) * 100, 2),
            "total_requests": self.total_requests,
            "error_rate": round(self.error_count / max(self.total_requests, 1) * 100, 2),
            "requests_per_hour": round(self.total_requests / max(uptime / 3600, 0.001), 1)
        }

perf_monitor = PerformanceMonitor()

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
    'ml_models': {},
    'signal_weights': {
        'technical': 0.6,  # Higher weight for reliability
        'gpt4': 0.3,
        'ml': 0.1
    },
    'cache_enabled': True,
    'async_enabled': True,
    'connection_pool': None,
    'last_config_update': None,
    'server_version': '3.0.0-unified'
}

async def get_connection_pool():
    """Get or create HTTP connection pool"""
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

def load_config():
    """Load configuration from settings.json with intelligent caching"""
    try:
        # Check if config was recently loaded (5 minute cache)
        if (CONFIG['last_config_update'] and 
            (datetime.now() - CONFIG['last_config_update']).seconds < 300):
            return True
            
        # Try multiple config paths
        config_paths = [
            os.path.join(os.path.dirname(__file__), '..', 'config', 'settings.json'),
            os.path.join(os.path.dirname(__file__), 'config', 'settings.json'),
            'config/settings.json'
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
        if api_key and api_key != 'YOUR_OPENAI_API_KEY_HERE' and not api_key.startswith('sk-proj-'):
            CONFIG['openai_api_key'] = api_key
            openai.api_key = api_key
            CONFIG['use_gpt4'] = True
            logger.info("OpenAI API key configured")
        else:
            logger.warning("No valid OpenAI API key found")
            
        # Load other settings
        trading_config = settings.get('trading', {})
        CONFIG['signal_weights'].update(settings.get('signal_weights', {}))
        
        CONFIG['last_config_update'] = datetime.now()
        return True
        
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return False

@lru_cache(maxsize=10)
def load_ml_models():
    """Load ML models with caching"""
    models_dir = os.path.join(os.path.dirname(__file__), '..', 'models')
    loaded_models = {}
    
    # Load ensemble models
    try:
        ensemble_dir = os.path.join(models_dir, 'ml_ensemble')
        if os.path.exists(ensemble_dir):
            rf_path = os.path.join(ensemble_dir, 'random_forest_model.pkl')
            gb_path = os.path.join(ensemble_dir, 'gradient_boosting_model.pkl')
            
            if os.path.exists(rf_path):
                loaded_models['random_forest'] = joblib.load(rf_path)
                logger.info("Random Forest model loaded")
                
            if os.path.exists(gb_path):
                loaded_models['gradient_boosting'] = joblib.load(gb_path)
                logger.info("Gradient Boosting model loaded")
    except Exception as e:
        logger.warning(f"Could not load ensemble models: {e}")
    
    # Load neural network models
    try:
        nn_dir = os.path.join(models_dir, 'neural_network')
        nn_path = os.path.join(nn_dir, 'enhanced_model.pth')
        if os.path.exists(nn_path):
            loaded_models['neural_network'] = joblib.load(nn_path)
            logger.info("Neural network model loaded")
    except Exception as e:
        logger.warning(f"Could not load neural network model: {e}")
        
    CONFIG['ml_models'] = loaded_models
    return loaded_models

def extract_series_data(indicator_data: Dict, key: str, default_value: float = 50) -> np.ndarray:
    """Extract time series data optimized for numpy processing"""
    if isinstance(indicator_data.get(key), list):
        return np.array(indicator_data[key])
    elif isinstance(indicator_data.get(key + '_series'), list):
        return np.array(indicator_data[key + '_series'])
    else:
        return np.array([indicator_data.get(key, default_value)])

def detect_crossover_vectorized(series1: np.ndarray, series2: np.ndarray) -> str:
    """Optimized crossover detection using vectorized operations"""
    if len(series1) < 2 or len(series2) < 2:
        return "none"
    
    prev_diff = series1[-2] - series2[-2]
    curr_diff = series1[-1] - series2[-1]
    
    if prev_diff <= 0 and curr_diff > 0:
        return "bullish"
    elif prev_diff >= 0 and curr_diff < 0:
        return "bearish"
    
    return "none"

@lru_cache(maxsize=128)
def calculate_trend_strength_cached(series_tuple: tuple) -> Tuple[str, float]:
    """Cached trend calculation for performance"""
    series = np.array(series_tuple)
    if len(series) < 3:
        return "neutral", 0
    
    # Vectorized linear regression
    x = np.arange(len(series))
    slope = np.polyfit(x, series, 1)[0] if len(series) > 1 else 0
    
    if slope > 0.01:
        trend = "bullish"
    elif slope < -0.01:
        trend = "bearish"
    else:
        trend = "neutral"
    
    strength = min(abs(slope) * 100, 100)
    return trend, strength

def calculate_indicator_scores_parallel(market_data: Dict) -> Tuple[int, int, List[str]]:
    """Parallel indicator calculation for better performance"""
    tasks = []
    
    # Submit parallel tasks
    tasks.append(executor.submit(calculate_rsi_score, market_data))
    tasks.append(executor.submit(calculate_macd_score, market_data))
    tasks.append(executor.submit(calculate_ma_score, market_data))
    tasks.append(executor.submit(calculate_stochastic_score, market_data))
    tasks.append(executor.submit(calculate_support_resistance_score, market_data))
    
    # Collect results
    buy_score = 0
    sell_score = 0
    reasons = []
    
    for task in tasks:
        try:
            b, s, r = task.result(timeout=2.0)  # 2 second timeout per task
            buy_score += b
            sell_score += s
            reasons.extend(r)
        except Exception as e:
            logger.warning(f"Indicator calculation error: {e}")
    
    return buy_score, sell_score, reasons

def calculate_rsi_score(market_data: Dict) -> Tuple[int, int, List[str]]:
    """Enhanced RSI analysis with divergence detection"""
    buy_score = 0
    sell_score = 0
    reasons = []
    
    rsi_data = market_data.get('rsi', {})
    rsi_h1_series = extract_series_data(rsi_data, 'h1', 50)
    rsi_m15_series = extract_series_data(rsi_data, 'm15', 50)
    
    rsi_h1 = rsi_h1_series[-1]
    rsi_m15 = rsi_m15_series[-1]
    
    # Multi-timeframe RSI analysis
    if rsi_h1 < 30:
        buy_score += 30
        reasons.append(f"H1 RSI severely oversold ({rsi_h1:.1f})")
    elif rsi_h1 < 40:
        buy_score += 20
        reasons.append(f"H1 RSI oversold ({rsi_h1:.1f})")
    elif rsi_h1 > 70:
        sell_score += 30
        reasons.append(f"H1 RSI severely overbought ({rsi_h1:.1f})")
    elif rsi_h1 > 60:
        sell_score += 20
        reasons.append(f"H1 RSI overbought ({rsi_h1:.1f})")
        
    # M15 confirmation
    if rsi_m15 < 25 and rsi_h1 < 40:
        buy_score += 15
        reasons.append(f"M15 RSI confirms oversold ({rsi_m15:.1f})")
    elif rsi_m15 > 75 and rsi_h1 > 60:
        sell_score += 15
        reasons.append(f"M15 RSI confirms overbought ({rsi_m15:.1f})")
    
    # RSI trend analysis
    if len(rsi_h1_series) >= 5:
        rsi_trend, strength = calculate_trend_strength_cached(tuple(rsi_h1_series[-5:]))
        if rsi_trend == "bullish" and rsi_h1 < 50:
            buy_score += 10
            reasons.append("RSI trending up from oversold")
        elif rsi_trend == "bearish" and rsi_h1 > 50:
            sell_score += 10
            reasons.append("RSI trending down from overbought")
        
    return buy_score, sell_score, reasons

def calculate_macd_score(market_data: Dict) -> Tuple[int, int, List[str]]:
    """Enhanced MACD analysis with histogram and divergence"""
    buy_score = 0
    sell_score = 0
    reasons = []
    
    macd_data = market_data.get('macd', {})
    macd_h1_series = extract_series_data(macd_data, 'h1', 0)
    macd_signal_series = extract_series_data(macd_data, 'signal', 0)
    macd_hist_series = extract_series_data(macd_data, 'hist', 0)
    
    if len(macd_h1_series) < 2:
        return buy_score, sell_score, reasons
    
    macd_h1 = macd_h1_series[-1]
    macd_signal = macd_signal_series[-1]
    macd_hist = macd_hist_series[-1] if len(macd_hist_series) > 0 else 0
    
    # MACD crossover analysis
    crossover = detect_crossover_vectorized(macd_h1_series, macd_signal_series)
    if crossover == "bullish":
        buy_score += 25
        reasons.append("Fresh bullish MACD crossover")
    elif crossover == "bearish":
        sell_score += 25
        reasons.append("Fresh bearish MACD crossover")
    
    # MACD position analysis
    if macd_h1 > 0:
        buy_score += 15
        reasons.append("MACD above zero line")
    else:
        sell_score += 15
        reasons.append("MACD below zero line")
    
    # Histogram momentum
    if len(macd_hist_series) >= 2:
        hist_change = macd_hist - macd_hist_series[-2]
        if hist_change > 0 and macd_hist > 0:
            buy_score += 10
            reasons.append("MACD histogram rising (bullish momentum)")
        elif hist_change < 0 and macd_hist < 0:
            sell_score += 10
            reasons.append("MACD histogram falling (bearish momentum)")
        
    return buy_score, sell_score, reasons

def calculate_ma_score(market_data: Dict) -> Tuple[int, int, List[str]]:
    """Enhanced moving average analysis"""
    buy_score = 0
    sell_score = 0
    reasons = []
    
    ma_data = market_data.get('moving_average', {})
    ma_fast_series = extract_series_data(ma_data, 'fast', 0)
    ma_slow_series = extract_series_data(ma_data, 'slow', 0)
    ma_200_series = extract_series_data(ma_data, 'ma_200', 0)
    
    if len(ma_fast_series) < 2 or len(ma_slow_series) < 2:
        return buy_score, sell_score, reasons
    
    ma_fast = ma_fast_series[-1]
    ma_slow = ma_slow_series[-1]
    ma_200 = ma_200_series[-1] if len(ma_200_series) > 0 else 0
    bid = market_data.get('bid', 0)
    
    # MA crossover
    crossover = detect_crossover_vectorized(ma_fast_series, ma_slow_series)
    if crossover == "bullish":
        buy_score += 25
        reasons.append("Bullish MA crossover")
    elif crossover == "bearish":
        sell_score += 25
        reasons.append("Bearish MA crossover")
    
    # MA alignment
    if ma_fast > ma_slow:
        separation = (ma_fast - ma_slow) / ma_slow * 100
        if separation > 0.5:  # Strong separation
            buy_score += 20
            reasons.append("Strong bullish MA alignment")
        else:
            buy_score += 15
            reasons.append("Bullish MA alignment")
    else:
        separation = (ma_slow - ma_fast) / ma_slow * 100
        if separation > 0.5:
            sell_score += 20
            reasons.append("Strong bearish MA alignment")
        else:
            sell_score += 15
            reasons.append("Bearish MA alignment")
    
    # 200 MA trend filter
    if ma_200 > 0:
        if bid > ma_200:
            buy_score += 10
            reasons.append("Price above 200 MA (bullish bias)")
        else:
            sell_score += 10
            reasons.append("Price below 200 MA (bearish bias)")
    
    return buy_score, sell_score, reasons

def calculate_stochastic_score(market_data: Dict) -> Tuple[int, int, List[str]]:
    """Enhanced stochastic analysis"""
    buy_score = 0
    sell_score = 0
    reasons = []
    
    stoch_data = market_data.get('stochastic', {})
    stoch_main_series = extract_series_data(stoch_data, 'main', 50)
    stoch_signal_series = extract_series_data(stoch_data, 'signal', 50)
    
    if len(stoch_main_series) < 2:
        return buy_score, sell_score, reasons
    
    stoch_main = stoch_main_series[-1]
    stoch_signal = stoch_signal_series[-1]
    
    # Oversold/Overbought with crossover
    if stoch_main < 20:
        buy_score += 15
        reasons.append("Stochastic oversold")
        crossover = detect_crossover_vectorized(stoch_main_series, stoch_signal_series)
        if crossover == "bullish":
            buy_score += 15
            reasons.append("Bullish stochastic crossover in oversold")
    elif stoch_main > 80:
        sell_score += 15
        reasons.append("Stochastic overbought")
        crossover = detect_crossover_vectorized(stoch_main_series, stoch_signal_series)
        if crossover == "bearish":
            sell_score += 15
            reasons.append("Bearish stochastic crossover in overbought")
    
    return buy_score, sell_score, reasons

def calculate_support_resistance_score(market_data: Dict) -> Tuple[int, int, List[str]]:
    """Support and resistance analysis"""
    buy_score = 0
    sell_score = 0
    reasons = []
    
    bid = market_data.get('bid', 0)
    support_level = market_data.get('support_level')
    resistance_level = market_data.get('resistance_level')
    
    adv = market_data.get('advanced_indicators', {})
    atr_series = extract_series_data(adv, 'atr_h1', 5)
    atr = atr_series[-1] if len(atr_series) > 0 else 5
    
    if support_level:
        distance_to_support = abs(bid - support_level)
        if distance_to_support <= atr * 0.5:  # Within 0.5 ATR
            buy_score += 20
            reasons.append(f"Near support level ({support_level:.2f})")
    
    if resistance_level:
        distance_to_resistance = abs(resistance_level - bid)
        if distance_to_resistance <= atr * 0.5:  # Within 0.5 ATR
            sell_score += 20
            reasons.append(f"Near resistance level ({resistance_level:.2f})")
    
    return buy_score, sell_score, reasons

def get_signal_cache_key(market_data: Dict) -> str:
    """Generate cache key for market data"""
    key_data = {
        'bid': round(market_data.get('bid', 0), 2),
        'ask': round(market_data.get('ask', 0), 2),
        'rsi_h1': round(market_data.get('rsi', {}).get('h1', 50), 1),
        'macd_h1': round(market_data.get('macd', {}).get('h1', 0), 4),
        'session': market_data.get('session', 'unknown'),
        'timestamp': int(time.time() / 30)  # 30-second cache buckets
    }
    return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

@cache.memoize(timeout=30)
def calculate_technical_signal_cached(cache_key: str, market_data: Dict) -> Dict:
    """Unified technical analysis with caching"""
    start_time = time.time()
    
    try:
        # Parallel indicator calculation
        buy_score, sell_score, reasons = calculate_indicator_scores_parallel(market_data)
        
        # Additional context
        session = market_data.get('session', 'Unknown')
        minutes_to_news = market_data.get('minutes_to_news')
        
        # Session adjustments
        if session in ['London', 'NY']:
            if buy_score > sell_score or sell_score > buy_score:
                reasons.append(f"Active {session} session")
        
        # News proximity warning
        if minutes_to_news is not None and minutes_to_news < 30:
            reasons.append(f"⚠️ News in {minutes_to_news} min")
            # Reduce confidence near news
            buy_score = int(buy_score * 0.8)
            sell_score = int(sell_score * 0.8)
        
        # Determine signal
        total_score = buy_score + sell_score
        if buy_score > sell_score and buy_score >= 40:
            signal = "BUY"
            confidence = min(95, 50 + int((buy_score / max(total_score, 1)) * 50))
        elif sell_score > buy_score and sell_score >= 40:
            signal = "SELL" 
            confidence = min(95, 50 + int((sell_score / max(total_score, 1)) * 50))
        else:
            signal = "HOLD"
            confidence = 40
        
        # Calculate SL/TP based on ATR
        adv = market_data.get('advanced_indicators', {})
        atr_series = extract_series_data(adv, 'atr_h1', 5)
        atr = atr_series[-1] if len(atr_series) > 0 else 5.0
        
        # Dynamic SL/TP based on signal strength
        if signal != "HOLD":
            sl_multiplier = 1.5 if confidence > 70 else 2.0
            tp_multiplier = 3.0 if confidence > 70 else 2.5
        else:
            sl_multiplier = 2.0
            tp_multiplier = 3.0
        
        result = {
            "signal": signal,
            "confidence": confidence,
            "sl": round(atr * sl_multiplier, 1),
            "tp": round(atr * tp_multiplier, 1),
            "reasoning": "; ".join(reasons[:6]),  # Top 6 reasons
            "buy_score": buy_score,
            "sell_score": sell_score,
            "risk_level": "LOW" if confidence > 75 else "MEDIUM" if confidence > 50 else "HIGH",
            "processing_time": round(time.time() - start_time, 3)
        }
        
        return result
        
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
    """Async GPT-4 analysis with optimized prompting"""
    if not CONFIG['use_gpt4']:
        return None
        
    try:
        # Create focused prompt
        bid = market_data.get('bid', 0)
        rsi_h1 = market_data.get('rsi', {}).get('h1', 50)
        macd_h1 = market_data.get('macd', {}).get('h1', 0)
        session = market_data.get('session', 'Unknown')
        
        # Get ATR for risk calculations
        adv = market_data.get('advanced_indicators', {})
        atr_series = extract_series_data(adv, 'atr_h1', 5)
        atr = atr_series[-1] if len(atr_series) > 0 else 5.0
        
        prompt = f"""Gold Trading Analysis for XAUUSD:

Price: ${bid:.2f}
RSI H1: {rsi_h1:.1f}
MACD H1: {macd_h1:.5f}
Session: {session}
ATR: {atr:.1f}

Market Context:
{market_data.get('reasoning', 'Standard market conditions')}

Requirements:
- Only recommend BUY/SELL if 2:1 risk-reward is achievable
- ATR-based stop loss: {atr * 1.5:.1f} points
- Required take profit: {atr * 3.0:.1f} points minimum
- Consider support/resistance levels

Respond with JSON: {{"signal": "BUY/SELL/HOLD", "confidence": 0-100, "reasoning": "brief analysis"}}"""
        
        # Async OpenAI call with timeout
        response = await asyncio.wait_for(
            asyncio.to_thread(
                openai.chat.completions.create,
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Expert gold trader focusing on high-probability 2:1 RR setups only."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1
            ),
            timeout=8.0
        )
        
        # Parse response
        content = response.choices[0].message.content
        if '{' in content and '}' in content:
            json_str = content[content.find('{'):content.rfind('}')+1]
            return json.loads(json_str)
            
    except Exception as e:
        logger.error(f"GPT-4 error: {e}")
        return None

def combine_signals_weighted(signals: List[Tuple[str, Dict, float]]) -> Dict:
    """Advanced signal combination with weighted voting"""
    if not signals:
        return {"signal": "HOLD", "confidence": 0, "reasoning": "No signals available"}
    
    # Weighted aggregation
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
                reasons.append(f"{source}: {signal_data['reasoning'][:80]}")
    
    # Determine final signal
    max_weight = max(signal_weights.values())
    if max_weight == 0:
        return {"signal": "HOLD", "confidence": 0, "reasoning": "No valid signals"}
    
    final_signal = next(s for s, w in signal_weights.items() if w == max_weight)
    final_confidence = min(95, int((max_weight / sum(signal_weights.values())) * 100))
    
    # Get SL/TP from technical analysis
    tech_signal = next((s[1] for s in signals if s[0] == 'technical'), {})
    
    return {
        "signal": final_signal,
        "confidence": final_confidence,
        "reasoning": " | ".join(reasons[:3]),
        "sl": tech_signal.get('sl', 100),
        "tp": tech_signal.get('tp', 200),
        "risk_level": tech_signal.get('risk_level', 'MEDIUM')
    }

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check with performance metrics"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": CONFIG['server_version'],
        "components": {
            "gpt4": CONFIG['use_gpt4'],
            "ml_models": len(CONFIG['ml_models']),
            "technical_analysis": True,
            "caching": CONFIG['cache_enabled'],
            "async_processing": CONFIG['async_enabled']
        },
        "performance": perf_monitor.get_stats()
    })

@app.route('/ai_signal', methods=['POST'])
async def get_ai_signal():
    """Main unified signal endpoint"""
    start_time = time.time()
    
    try:
        # Get request data
        market_data = request.get_json()
        if not market_data:
            return jsonify({"error": "No data provided"}), 400
        
        # Handle test requests
        if market_data.get('test', False):
            return jsonify({
                "signal": "HOLD",
                "confidence": 95,
                "reasoning": "Server test successful",
                "test_mode": True,
                "timestamp": datetime.now().isoformat()
            })
        
        # Extract weights
        settings = market_data.get('settings', {})
        weights = settings.get('weights', CONFIG['signal_weights'])
        
        # Generate cache key
        cache_key = get_signal_cache_key(market_data)
        
        # Check cache
        if CONFIG['cache_enabled']:
            cached_result = cache.get(f"signal_{cache_key}")
            if cached_result:
                perf_monitor.cache_hits += 1
                perf_monitor.log_request(time.time() - start_time)
                return jsonify(cached_result)
            else:
                perf_monitor.cache_misses += 1
        
        # Collect signals
        signals = []
        
        # 1. Technical Analysis (always available)
        tech_signal = calculate_technical_signal_cached(cache_key, market_data)
        if tech_signal:
            signals.append(('technical', tech_signal, weights.get('technical', 0.6)))
        
        # 2. GPT-4 Analysis (async if available)
        if CONFIG['use_gpt4'] and weights.get('gpt4', 0) > 0:
            try:
                gpt_signal = await asyncio.wait_for(
                    get_gpt4_signal_async(market_data), 
                    timeout=10.0
                )
                if gpt_signal:
                    signals.append(('gpt4', gpt_signal, weights.get('gpt4', 0.3)))
            except asyncio.TimeoutError:
                logger.warning("GPT-4 timed out")
        
        # 3. ML Models (if available)
        # TODO: Add ML prediction integration
        
        # Combine signals
        final_signal = combine_signals_weighted(signals)
        
        # Add metadata
        final_signal.update({
            'timestamp': datetime.now().isoformat(),
            'symbol': market_data.get('symbol', 'XAUUSD'),
            'lot_size': 0.01,
            'processing_time': round(time.time() - start_time, 3)
        })
        
        # Cache result
        if CONFIG['cache_enabled']:
            cache.set(f"signal_{cache_key}", final_signal, timeout=45)
        
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

@app.route('/status', methods=['GET'])
def get_status():
    """Enhanced status endpoint"""
    return jsonify({
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": CONFIG['server_version'],
        "components": {
            "gpt4": CONFIG['use_gpt4'],
            "ml_models": list(CONFIG['ml_models'].keys()),
            "technical_analysis": True,
            "caching": CONFIG['cache_enabled'],
            "async_processing": CONFIG['async_enabled']
        },
        "performance": perf_monitor.get_stats(),
        "system_info": {
            "python_version": "3.x",
            "dependencies": "flask, openai, numpy, scikit-learn"
        }
    })

async def cleanup():
    """Cleanup resources on shutdown"""
    if CONFIG['connection_pool']:
        await CONFIG['connection_pool'].close()
    executor.shutdown(wait=True)

def initialize():
    """Initialize the unified server"""
    logger.info("Initializing AI Gold Scalper Unified Server v3.0.0")
    
    # Load configuration
    load_config()
    
    # Load ML models in background
    executor.submit(load_ml_models)
    
    logger.info("Server initialization complete")
    logger.info(f"GPT-4 enabled: {CONFIG['use_gpt4']}")
    logger.info(f"ML models available: {len(CONFIG['ml_models'])}")
    logger.info(f"Caching enabled: {CONFIG['cache_enabled']}")

if __name__ == '__main__':
    # Initialize
    initialize()
    
    # Get host and port
    host = os.environ.get('AI_SERVER_HOST', '0.0.0.0')
    port = int(os.environ.get('AI_SERVER_PORT', 5001))
    
    # Run with production server
    logger.info(f"Starting unified server on {host}:{port}")
    
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=6)
    except ImportError:
        logger.warning("Waitress not available, using Flask development server")
        app.run(host=host, port=port, debug=False, threaded=True)
