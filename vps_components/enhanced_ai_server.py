#!/usr/bin/env python3
"""
Enhanced AI Server for XAUUSD Trading
Integrates newly trained ML models with existing technical analysis
"""
from flask import Flask, request, jsonify
import pandas as pd
import numpy as np
import joblib
import torch
import torch.nn as nn
from datetime import datetime, timedelta
import os
import sys
import logging
import json
import warnings
warnings.filterwarnings('ignore')

# Add paths for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class EnhancedAIServer:
    def __init__(self, config_path=None):
        self.config_path = config_path or r"G:\My Drive\AI_Gold_Scalper\config\settings.json"
        self.models = {}
        self.scalers = {}
        self.feature_list = None
        self.config = {}
        
        # Load configuration
        self.load_config()
        
        # Load trained models
        self.load_trained_models()
        
        # Initialize Flask app
        app = Flask(__name__)
        CORS(app)
        
        logger.info("Enhanced AI Server initialized successfully")
    
    def load_config(self):
        """Load server configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found at {self.config_path}")
                self.config = self.get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config = self.get_default_config()
    
    def get_default_config(self):
        """Return default configuration"""
            "model_weights": {
                "neural_network": 0.4,
                "rf_classifier": 0.3,
                "technical_analysis": 0.3
            },
            "risk_management": {
                "max_risk_per_trade": 0.005,
                "max_daily_drawdown": 0.02,
                "min_confidence_threshold": 0.6
            },
            "trading_sessions": {
                "london": {"start": 8, "end": 17},
                "newyork": {"start": 13, "end": 22}
            }
        }
    
    def load_trained_models(self):
        """Load trained ML models"""
        models_dir = r"G:\My Drive\AI_Gold_Scalper\models\trained"
        
        try:
            # Load feature list
            feature_path = os.path.join(models_dir, "feature_list.pkl")
            if os.path.exists(feature_path):
                self.feature_list = joblib.load(feature_path)
                logger.info(f"Loaded {len(self.feature_list)} features")
            
            # Load Random Forest Classifier
            rf_classifier_path = os.path.join(models_dir, "rf_classifier.pkl")
            rf_classifier_scaler_path = os.path.join(models_dir, "rf_classifier_scaler.pkl")
            
            if os.path.exists(rf_classifier_path) and os.path.exists(rf_classifier_scaler_path):
                self.models['rf_classifier'] = joblib.load(rf_classifier_path)
                self.scalers['rf_classifier'] = joblib.load(rf_classifier_scaler_path)
                logger.info("Loaded Random Forest Classifier")
            
            # Load Random Forest Regressor
            rf_regressor_path = os.path.join(models_dir, "rf_regressor.pkl")
            rf_regressor_scaler_path = os.path.join(models_dir, "rf_regressor_scaler.pkl")
            
            if os.path.exists(rf_regressor_path) and os.path.exists(rf_regressor_scaler_path):
                self.models['rf_regressor'] = joblib.load(rf_regressor_path)
                self.scalers['rf_regressor'] = joblib.load(rf_regressor_scaler_path)
                logger.info("Loaded Random Forest Regressor")
            
            # Load Neural Network
            nn_path = os.path.join(models_dir, "neural_network.pkl")
            nn_scaler_path = os.path.join(models_dir, "neural_network_scaler.pkl")
            
            if os.path.exists(nn_path) and os.path.exists(nn_scaler_path):
                # Note: For neural network, we need to recreate the architecture
                # This is a simplified version - in production, save architecture separately
                self.scalers['neural_network'] = joblib.load(nn_scaler_path)
                logger.info("Loaded Neural Network scaler (model architecture needs recreation)")
            
            logger.info(f"Successfully loaded {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
    
    def calculate_technical_indicators(self, data):
        """Calculate technical indicators from OHLCV data"""
        try:
            df = pd.DataFrame(data)
            
            # Ensure we have required columns
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in required_cols:
                if col not in df.columns:
                    logger.warning(f"Missing required column: {col}")
                    return {}
            
            # Calculate basic indicators
            df['Returns'] = df['close'].pct_change()
            df['LogReturns'] = np.log(df['close'] / df['close'].shift(1))
            
            # Moving averages
            for period in [5, 10, 20, 50]:
                df[f'SMA_{period}'] = df['close'].rolling(window=period).mean()
                df[f'EMA_{period}'] = df['close'].ewm(span=period).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI_14'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = df['close'].ewm(span=12).mean()
            exp2 = df['close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            df['ATR_14'] = true_range.rolling(window=14).mean()
            
            # Bollinger Bands
            df['BB_Middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
            df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
            df['BB_Position'] = (df['close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
            
            # Return latest values
            latest_row = df.iloc[-1]
            indicators = {
                'rsi': latest_row.get('RSI_14', 50),
                'macd': latest_row.get('MACD', 0),
                'macd_signal': latest_row.get('MACD_Signal', 0),
                'macd_histogram': latest_row.get('MACD_Histogram', 0),
                'bb_position': latest_row.get('BB_Position', 0.5),
                'atr': latest_row.get('ATR_14', 1),
                'sma_20': latest_row.get('SMA_20', latest_row['close']),
                'ema_20': latest_row.get('EMA_20', latest_row['close']),
                'current_price': latest_row['close']
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators: {e}")
            return {}
    
    def prepare_ml_features(self, data, indicators):
        """Prepare features for ML model prediction"""
        try:
            if not self.feature_list:
                logger.warning("Feature list not loaded, cannot prepare ML features")
                return None
            
            # Create a simplified feature vector
            # In production, this should match the exact feature engineering from training
            current_time = datetime.now()
            
            features = {
                # Price indicators
                'RSI_14': indicators.get('rsi', 50),
                'MACD': indicators.get('macd', 0),
                'MACD_Signal': indicators.get('macd_signal', 0),
                'MACD_Histogram': indicators.get('macd_histogram', 0),
                'ATR_14': indicators.get('atr', 1),
                'BB_Position': indicators.get('bb_position', 0.5),
                
                # Time features
                'Hour': current_time.hour,
                'DayOfWeek': current_time.weekday(),
                'IsLondonSession': 1 if 8 <= current_time.hour < 17 else 0,
                'IsNYSession': 1 if 13 <= current_time.hour < 22 else 0,
                'IsOverlapSession': 1 if 13 <= current_time.hour < 17 else 0,
            }
            
            # Fill missing features with default values
            feature_vector = []
            for feature_name in self.feature_list:
                if feature_name in features:
                    feature_vector.append(features[feature_name])
                else:
                    # Default values for missing features
                    default_value = 0
                    if 'Volume' in feature_name:
                        default_value = 1000
                    elif 'Price' in feature_name or 'SMA' in feature_name or 'EMA' in feature_name:
                        default_value = indicators.get('current_price', 2500)
                    elif 'RSI' in feature_name:
                        default_value = 50
                    elif 'BB_Position' in feature_name:
                        default_value = 0.5
                    
                    feature_vector.append(default_value)
            
            return np.array(feature_vector).reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error preparing ML features: {e}")
            return None
    
    def get_ml_predictions(self, features):
        """Get predictions from trained ML models"""
        predictions = {}
        
        try:
            if features is None:
                return predictions
            
            # Random Forest Classifier
            if 'rf_classifier' in self.models and 'rf_classifier' in self.scalers:
                try:
                    features_scaled = self.scalers['rf_classifier'].transform(features)
                    pred_proba = self.models['rf_classifier'].predict_proba(features_scaled)[0]
                    pred_class = self.models['rf_classifier'].predict(features_scaled)[0]
                    
                    # Map predictions back to original labels
                    class_mapping = {0: -1, 1: 0, 2: 1}  # Assuming this mapping
                    if len(pred_proba) == 3:
                        predictions['rf_classifier'] = {
                            'signal': class_mapping.get(pred_class, 0),
                            'confidence': np.max(pred_proba),
                            'probabilities': {
                                'sell': pred_proba[0],
                                'hold': pred_proba[1], 
                                'buy': pred_proba[2]
                            }
                        }
                    else:
                        # Binary classification case
                        predictions['rf_classifier'] = {
                            'signal': 1 if pred_class == 1 else -1,
                            'confidence': np.max(pred_proba),
                            'probabilities': pred_proba.tolist()
                        }
                        
                except Exception as e:
                    logger.error(f"Error with RF classifier prediction: {e}")
            
            # Random Forest Regressor
            if 'rf_regressor' in self.models and 'rf_regressor' in self.scalers:
                try:
                    features_scaled = self.scalers['rf_regressor'].transform(features)
                    pred_return = self.models['rf_regressor'].predict(features_scaled)[0]
                    
                    predictions['rf_regressor'] = {
                        'predicted_return_bps': pred_return,
                        'signal': 1 if pred_return > 0.5 else (-1 if pred_return < -0.5 else 0),
                        'confidence': min(abs(pred_return) / 5.0, 1.0)  # Scale confidence
                    }
                    
                except Exception as e:
                    logger.error(f"Error with RF regressor prediction: {e}")
            
        except Exception as e:
            logger.error(f"Error getting ML predictions: {e}")
        
        return predictions
    
    def get_technical_signal(self, indicators):
        """Generate signal based on technical analysis"""
        try:
            rsi = indicators.get('rsi', 50)
            macd_histogram = indicators.get('macd_histogram', 0)
            bb_position = indicators.get('bb_position', 0.5)
            
            # Simple technical signal logic
            signal_score = 0
            
            # RSI signals
            if rsi > 70:
                signal_score -= 1  # Overbought
            elif rsi < 30:
                signal_score += 1  # Oversold
            
            # MACD signals
            if macd_histogram > 0:
                signal_score += 1
            elif macd_histogram < 0:
                signal_score -= 1
            
            # Bollinger Band signals
            if bb_position > 0.8:
                signal_score -= 1  # Near upper band
            elif bb_position < 0.2:
                signal_score += 1  # Near lower band
            
            # Determine final signal
            if signal_score >= 2:
                signal = 1  # Buy
            elif signal_score <= -2:
                signal = -1  # Sell
            else:
                signal = 0  # Hold
            
            confidence = min(abs(signal_score) / 3.0, 1.0)
            
            return {
                'signal': signal,
                'confidence': confidence,
                'score': signal_score,
                'components': {
                    'rsi': rsi,
                    'macd_histogram': macd_histogram,
                    'bb_position': bb_position
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating technical signal: {e}")
            return {'signal': 0, 'confidence': 0, 'score': 0}
    
    def combine_signals(self, ml_predictions, technical_signal):
        """Combine ML and technical analysis signals"""
        try:
            weights = self.config.get('model_weights', {})
            
            # Extract individual signals
            signals = []
            confidences = []
            
            # Neural Network
            if 'neural_network' in ml_predictions:
                nn_signal = ml_predictions['neural_network']['signal']
                nn_confidence = ml_predictions['neural_network']['confidence']
                signals.append(nn_signal * weights.get('neural_network', 0.4))
                confidences.append(nn_confidence)
            
            # Random Forest Classifier
            if 'rf_classifier' in ml_predictions:
                rf_signal = ml_predictions['rf_classifier']['signal']
                rf_confidence = ml_predictions['rf_classifier']['confidence']
                signals.append(rf_signal * weights.get('rf_classifier', 0.3))
                confidences.append(rf_confidence)
            
            # Technical Analysis
            tech_signal = technical_signal['signal']
            tech_confidence = technical_signal['confidence']
            signals.append(tech_signal * weights.get('technical_analysis', 0.3))
            confidences.append(tech_confidence)
            
            # Combine signals
            combined_signal = np.sum(signals)
            avg_confidence = np.mean(confidences)
            
            # Determine final signal
            if combined_signal > 0.3:
                final_signal = "BUY"
            elif combined_signal < -0.3:
                final_signal = "SELL"
            else:
                final_signal = "HOLD"
            
            return {
                'signal': final_signal,
                'confidence': avg_confidence,
                'raw_score': combined_signal,
                'individual_signals': {
                    'ml_predictions': ml_predictions,
                    'technical_analysis': technical_signal
                }
            }
            
        except Exception as e:
            logger.error(f"Error combining signals: {e}")
            return {'signal': 'HOLD', 'confidence': 0}

# Initialize the AI server
ai_server = EnhancedAIServer()

@app.route('/analyze', methods=['POST'])
def analyze_market():
    """Main analysis endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Calculate technical indicators
        indicators = ai_server.calculate_technical_indicators(data)
        
        # Prepare ML features
        ml_features = ai_server.prepare_ml_features(data, indicators)
        
        # Get ML predictions
        ml_predictions = ai_server.get_ml_predictions(ml_features)
        
        # Get technical analysis signal
        technical_signal = ai_server.get_technical_signal(indicators)
        
        # Combine all signals
        final_analysis = ai_server.combine_signals(ml_predictions, technical_signal)
        
        # Add additional context
        response = {
            'timestamp': datetime.now().isoformat(),
            'signal': final_analysis['signal'],
            'confidence': final_analysis['confidence'],
            'analysis': final_analysis,
            'indicators': indicators,
            'status': 'success'
        }
        
        logger.info(f"Analysis complete: {final_analysis['signal']} ({final_analysis['confidence']:.2f})")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in analyze_market: {e}")
        return jsonify({'error': str(e), 'status': 'error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'models_loaded': len(ai_server.models),
        'features_count': len(ai_server.feature_list) if ai_server.feature_list else 0
    })

@app.route('/models/status', methods=['GET'])
def model_status():
    """Get model status"""
    return jsonify({
        'models_loaded': list(ai_server.models.keys()),
        'scalers_loaded': list(ai_server.scalers.keys()),
        'feature_count': len(ai_server.feature_list) if ai_server.feature_list else 0,
        'config': ai_server.config
    })

if __name__ == '__main__':
    logger.info("Starting Enhanced AI Server...")
    logger.info(f"Models loaded: {list(ai_server.models.keys())}")
    logger.info(f"Server ready at http://127.0.0.1:5000")
    
    app.run(host='127.0.0.1', port=5000, debug=False)
