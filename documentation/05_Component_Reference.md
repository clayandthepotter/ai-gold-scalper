# Component Reference - AI Gold Scalper

## 📋 Overview

This document provides detailed reference information for all components in the AI Gold Scalper system. Each component is documented with its purpose, functionality, configuration options, and API endpoints.

## 🎛️ Core System Components

### 1. System Orchestrator Enhanced
**File**: `core/system_orchestrator_enhanced.py`  
**Type**: Management Service  
**Criticality**: Critical  

#### Purpose
The System Orchestrator is the central command and control system that manages all other components. It handles startup, shutdown, health monitoring, and component lifecycle management.

#### Key Features
- **Interactive Setup**: Guided configuration wizard
- **Component Management**: Start/stop/restart individual components
- **Health Monitoring**: Continuous component health checks
- **Deployment Flexibility**: Support for local and VPS deployments
- **Custom Component Selection**: Choose which components to run

#### Configuration
```json
{
  "deployment_type": "development|production",
  "selected_components": ["ai_server", "model_registry", "..."],
  "ai": {
    "api_key": "openai_api_key",
    "signal_fusion": {
      "ml_weight": 0.4,
      "technical_weight": 0.4,
      "gpt4_weight": 0.2
    }
  },
  "server": {
    "host": "0.0.0.0",
    "port": 5000
  }
}
```

#### Commands
```bash
# Interactive setup
python core/system_orchestrator_enhanced.py interactive-setup

# Start all components
python core/system_orchestrator_enhanced.py start

# Check system status
python core/system_orchestrator_enhanced.py status

# Stop all components
python core/system_orchestrator_enhanced.py stop

# Run backtesting
python core/system_orchestrator_enhanced.py backtest
```

#### Component Dependencies
- **Core Components**: ai_server, model_registry, enhanced_trade_logger
- **VPS Components**: Core + regime_detector, data_processor
- **Development Components**: VPS + all additional components

---

### 2. Enhanced AI Server Consolidated
**File**: `core/enhanced_ai_server_consolidated.py`  
**Type**: Service  
**Criticality**: Critical  
**Port**: 5000  

#### Purpose
The AI Server is the heart of the trading system, generating trading signals by combining machine learning models, technical analysis, and GPT-4 insights.

#### Key Features
- **Multi-Source Signal Fusion**: Combines ML, technical, and GPT-4 signals
- **Performance Caching**: Intelligent caching for optimization
- **Model Integration**: Seamless integration with ML models
- **Real-time Processing**: Sub-100ms signal generation
- **Health Monitoring**: Comprehensive health checks

#### API Endpoints

##### Health Check
```http
GET /health
```
**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-07-26T04:15:31Z",
  "server_version": "6.0.0-enhanced",
  "gpt4_enabled": true,
  "models_loaded": ["rf_classifier", "rf_regressor"],
  "performance": {
    "avg_response_time_ms": 45.2,
    "total_requests": 1234,
    "error_rate": 0.5
  }
}
```

##### AI Signal Generation
```http
POST /ai_signal
Content-Type: application/json

{
  "symbol": "XAUUSD",
  "bid": 2034.55,
  "ask": 2034.75,
  "rsi": {"h1": [45.2, 46.1, 47.3]},
  "macd": {"h1": [0.12, 0.15, 0.18]},
  "bollinger": {"upper": 2040.0, "lower": 2030.0}
}
```

**Response**:
```json
{
  "signal": "BUY",
  "confidence": 75,
  "sl": 2030.0,
  "tp": 2045.0,
  "lot_size": 0.1,
  "reasoning": "Strong bullish signals from ML models and technical analysis",
  "timestamp": "2025-07-26T04:15:31Z",
  "components": {
    "ml_signal": {"signal": "BUY", "confidence": 0.8},
    "technical_signal": {"signal": "BUY", "confidence": 0.7},
    "gpt4_signal": {"signal": "BUY", "confidence": 0.75}
  }
}
```

#### Configuration
- **Model Loading**: Automatic loading of trained models
- **Signal Weights**: Configurable weights for different signal sources
- **Caching**: Response caching for performance
- **Logging**: Comprehensive request/response logging

---

### 3. Model Registry
**File**: `scripts/ai/model_registry.py`  
**Type**: Persistent Service  
**Criticality**: Critical  

#### Purpose
Manages the lifecycle of machine learning models including storage, versioning, performance tracking, and model selection.

#### Key Features
- **Model Storage**: Secure storage of trained models
- **Version Control**: Complete model versioning system
- **Performance Tracking**: Real-time model performance monitoring
- **Automatic Selection**: Choose best-performing models
- **Metadata Management**: Comprehensive model metadata

#### Database Schema
```sql
-- Models table
CREATE TABLE models (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    algorithm TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    performance_score REAL NOT NULL,
    is_active BOOLEAN DEFAULT 0
);

-- Performance history
CREATE TABLE model_performance (
    id INTEGER PRIMARY KEY,
    model_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    accuracy REAL NOT NULL,
    precision_score REAL NOT NULL,
    recall_score REAL NOT NULL,
    trades_count INTEGER NOT NULL
);
```

#### API Methods
```python
# Register new model
model_id = registry.register_model(
    model_name="random_forest_v2",
    model_object=trained_model,
    algorithm="RandomForest",
    metadata={"accuracy": 0.85, "features": 42}
)

# Get active model
model, metadata = registry.get_active_model("classifier")

# Update performance
registry.update_model_performance(
    model_id=model_id,
    accuracy=0.87,
    trades_count=150
)

# Compare models
comparison = registry.compare_models([model_id1, model_id2])
```

---

### 4. Enhanced Trade Logger
**File**: `scripts/monitoring/enhanced_trade_logger.py`  
**Type**: Continuous Service  
**Criticality**: Critical  

#### Purpose
Comprehensive trade tracking and analysis system that logs all trading activities and provides detailed analytics.

#### Key Features
- **Trade Execution Logging**: Complete trade lifecycle tracking
- **Performance Analytics**: Real-time performance calculations
- **Risk Analysis**: Risk metrics and drawdown tracking
- **Event Logging**: System events and alerts
- **Database Storage**: SQLite database for trade data

#### Database Schema
```sql
-- Trade executions
CREATE TABLE trade_executions (
    id INTEGER PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    action TEXT NOT NULL,
    volume REAL NOT NULL,
    entry_price REAL NOT NULL,
    exit_price REAL,
    sl_price REAL,
    tp_price REAL,
    profit_loss REAL,
    outcome TEXT,
    signal_source TEXT,
    confidence_score REAL
);

-- Performance metrics
CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY,
    date DATE NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    win_rate REAL NOT NULL,
    total_profit REAL NOT NULL,
    max_drawdown REAL NOT NULL
);
```

#### Usage Examples
```python
# Log trade entry
logger.log_trade_entry({
    "symbol": "XAUUSD",
    "action": "BUY",
    "volume": 0.1,
    "entry_price": 2034.55,
    "sl_price": 2030.0,
    "tp_price": 2045.0,
    "signal_source": "ai_server",
    "confidence_score": 0.75
})

# Log trade exit
logger.log_trade_exit(trade_id, exit_price=2042.30, outcome="win")

# Get performance metrics
metrics = logger.get_performance_metrics(days=30)
```

---

## 🤖 AI & Machine Learning Components

### 5. Ensemble Models System
**File**: `scripts/ai/ensemble_models.py`  
**Type**: On-Demand Service  
**Criticality**: Optional  

#### Purpose
Advanced machine learning system that combines multiple algorithms using ensemble techniques for superior prediction accuracy.

#### Supported Algorithms
- **Random Forest**: Ensemble decision trees
- **Gradient Boosting**: Sequential learning algorithm
- **XGBoost**: Extreme gradient boosting (if available)
- **LightGBM**: Light gradient boosting (if available)
- **CatBoost**: Categorical boosting (if available)
- **Support Vector Machines**: High-dimensional classification
- **Neural Networks**: Multi-layer perceptron

#### Ensemble Methods
- **Voting Classifier**: Majority voting across models
- **Stacking Classifier**: Meta-learning approach
- **Bagging Classifier**: Bootstrap aggregating

#### Configuration
```json
{
  "base_models": ["random_forest", "gradient_boost", "xgboost"],
  "ensemble_methods": ["voting", "stacking", "bagging"],
  "cross_validation_folds": 5,
  "min_model_accuracy": 0.65,
  "ensemble_weights": {
    "random_forest": 0.4,
    "gradient_boost": 0.4,
    "xgboost": 0.2
  }
}
```

#### Usage
```python
# Create ensemble system
ensemble = AdvancedEnsembleSystem()

# Train ensemble models
results = ensemble.create_ensemble_models(
    X_train, y_train, 
    ensemble_type="stacking"
)

# Make predictions
prediction = ensemble.predict_with_ensemble(
    ensemble_id, features
)
```

---

### 6. Market Regime Detector
**File**: `scripts/ai/market_regime_detector.py`  
**Type**: Continuous Service  
**Criticality**: Optional  

#### Purpose
Analyzes market conditions to identify different market regimes (trending, ranging, volatile) and adapts trading strategies accordingly.

#### Detection Methods
- **Rule-based Classification**: Predefined market condition rules
- **Clustering Analysis**: K-means and Gaussian mixture models
- **Statistical Classification**: Statistical properties analysis
- **Multi-method Consensus**: Combines multiple detection methods

#### Market Characteristics Analyzed
- **Volatility Patterns**: High/low volatility periods
- **Trend Analysis**: Trending vs ranging markets
- **Volume Analysis**: Volume patterns and price-volume relationships
- **Price Action**: Breakouts, reversals, consolidations
- **Market Microstructure**: Efficiency and liquidity analysis

#### Usage
```python
# Initialize detector
detector = MarketRegimeDetector()

# Detect current regime
regime = detector.detect_regime(price_data)

# Get regime characteristics
characteristics = detector.get_regime_characteristics(regime_id)

# Historical regime analysis
history = detector.get_regime_history(days=30)
```

---

### 7. Adaptive Learning System
**File**: `scripts/ai/adaptive_learning.py`  
**Type**: Periodic Service  
**Criticality**: Optional  

#### Purpose
Continuously learns from trading results and market conditions to improve model performance and adapt to changing market dynamics.

#### Key Features
- **Continuous Learning**: Updates models based on new trade data
- **Feature Engineering**: Advanced technical indicator generation
- **Performance Monitoring**: Real-time model performance tracking
- **Intelligent Retraining**: Triggered by performance thresholds
- **Feature Selection**: Automatic selection of most predictive features

#### Learning Triggers
- **Scheduled**: Time-based retraining (daily, weekly)
- **Performance-based**: Triggered by declining performance
- **Data-driven**: Minimum trade count requirements
- **Market Change**: Significant market regime changes

#### Configuration
```json
{
  "min_trades_for_update": 50,
  "retraining_frequency_hours": 24,
  "performance_threshold": 0.6,
  "feature_importance_threshold": 0.01,
  "max_features_to_keep": 20
}
```

---

## 📊 Analytics & Monitoring Components

### 8. Performance Dashboard
**File**: `scripts/monitoring/performance_dashboard.py`  
**Type**: Service  
**Criticality**: Optional  
**Port**: 8080  

#### Purpose
Real-time web-based dashboard for monitoring system performance, trading results, and component health.

#### Features
- **Real-time Metrics**: Live performance indicators
- **Interactive Charts**: Plotly-based visualizations
- **System Health**: Component status monitoring
- **Trade Analysis**: Detailed trade performance analysis
- **Risk Monitoring**: Real-time risk metrics

#### Dashboard Sections
1. **System Overview**: Component status and health
2. **Trading Performance**: P&L, win rate, drawdown
3. **Signal Analysis**: Signal accuracy and distribution
4. **Risk Metrics**: Position sizing and risk exposure
5. **Model Performance**: ML model accuracy and predictions

#### API Endpoints
```http
GET /api/system-status          # System health status
GET /api/performance-metrics    # Trading performance data
GET /api/trade-history         # Recent trade history
GET /api/component-health      # Individual component health
```

---

### 9. Risk Parameter Optimizer
**File**: `scripts/analysis/risk_parameter_optimizer.py`  
**Type**: Scheduled Service  
**Criticality**: Optional  

#### Purpose
Analyzes trading performance and optimizes risk parameters such as position sizing, stop-loss levels, and risk exposure limits.

#### Optimization Areas
- **Position Sizing**: Optimal lot size calculations
- **Stop-Loss Optimization**: Dynamic SL level adjustment
- **Risk-Reward Ratios**: Optimal TP/SL ratios
- **Drawdown Management**: Maximum drawdown controls
- **Exposure Limits**: Maximum position exposure

#### Analysis Methods
- **Monte Carlo Simulation**: Risk scenario analysis
- **Historical Backtesting**: Parameter performance testing
- **Statistical Analysis**: Risk-return optimization
- **Machine Learning**: Predictive risk modeling

---

### 10. Backtesting System
**File**: `scripts/backtesting/comprehensive_backtester.py`  
**Type**: On-Demand Service  
**Criticality**: Optional  

#### Purpose
Comprehensive historical testing framework for validating trading strategies and system performance using historical market data.

#### Features
- **Multi-timeframe Testing**: Test across different timeframes
- **Performance Metrics**: Comprehensive performance analysis
- **Risk Analysis**: Drawdown and risk assessment
- **Statistical Validation**: Statistical significance testing
- **Scenario Testing**: Multiple market condition scenarios

#### Key Metrics
- **Return Metrics**: Total return, annualized return, Sharpe ratio
- **Risk Metrics**: Maximum drawdown, volatility, VaR
- **Trade Metrics**: Win rate, profit factor, average trade
- **Statistical Metrics**: Correlation, beta, information ratio

#### Usage
```python
# Initialize backtester
backtester = ComprehensiveBacktester()

# Run backtest
results = backtester.run_backtest(
    strategy="ai_model",
    symbol="XAUUSD",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# Analyze results
analysis = backtester.analyze_results(results)
```

---

## 🔧 Utility Components

### 11. Market Data Processor
**File**: `scripts/data/market_data_processor.py`  
**Type**: Scheduled Service  
**Criticality**: Optional  

#### Purpose
Processes and manages market data feeds, ensuring clean, reliable data for analysis and model training.

#### Features
- **Data Ingestion**: Multiple data source support
- **Data Cleaning**: Outlier detection and correction
- **Feature Engineering**: Technical indicator calculation
- **Data Storage**: Efficient storage and retrieval
- **Data Validation**: Quality checks and validation

---

### 12. Automated Model Trainer
**File**: `scripts/training/automated_model_trainer.py`  
**Type**: Event-Driven Service  
**Criticality**: Optional  

#### Purpose
Automated machine learning model training system that creates, trains, and evaluates models based on available data.

#### Features
- **Automated Training**: Scheduled model training
- **Hyperparameter Optimization**: Automatic parameter tuning
- **Model Evaluation**: Cross-validation and performance testing
- **Model Registration**: Automatic model registry integration
- **Performance Tracking**: Training and validation metrics

---

## 🔄 Integration Components

### 13. Phase 3 Integration
**File**: `scripts/integration/phase3_integration.py`  
**Type**: Integration Layer  
**Criticality**: Optional  

#### Purpose
Integration layer for Phase 3 system components including model registry and adaptive learning.

### 14. Phase 4 Integration
**File**: `scripts/integration/phase4_integration.py`  
**Type**: Integration Layer  
**Criticality**: Optional  

#### Purpose
Advanced integration layer for Phase 4 components including ensemble models and market regime detection.

### 15. Backtesting Integration
**File**: `scripts/integration/backtesting_integration.py`  
**Type**: Integration Layer  
**Criticality**: Optional  

#### Purpose
Integration layer that connects the backtesting system with other components for comprehensive historical analysis.

---

## 🎯 Component Selection Guide

### Core Components (Always Required)
- **System Orchestrator**: System management
- **AI Server**: Signal generation
- **Model Registry**: Model management
- **Trade Logger**: Trade tracking

### VPS Production Components
- Core Components +
- **Market Regime Detector**: Market analysis
- **Data Processor**: Data management

### Development Components
- VPS Components +
- **Performance Dashboard**: Monitoring
- **Ensemble Models**: Advanced ML
- **Adaptive Learning**: Continuous improvement
- **Backtesting System**: Historical validation
- **All other optional components**

## 🔄 Next Steps

For detailed information about specific components:

1. **[AI Server](07_AI_Server.md)** - Deep dive into AI server functionality
2. **[System Orchestrator](08_System_Orchestrator.md)** - Management system details
3. **[Model System](09_Model_System.md)** - ML model management
4. **[Performance Dashboard](14_Performance_Dashboard.md)** - Monitoring interface

---

*This component reference provides the foundation for understanding how each piece of the AI Gold Scalper system works together to create a comprehensive trading solution.*
