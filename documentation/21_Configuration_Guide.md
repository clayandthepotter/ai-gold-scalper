# Configuration Guide - AI Gold Scalper

## 🔧 Overview

This guide covers how to customize and configure your AI Gold Scalper system after installation. Whether you want to adjust risk parameters, optimize AI signals, or customize the trading behavior, this guide provides detailed configuration options.

## 📁 Configuration File Locations

### Main Configuration Files
```
AI_Gold_Scalper/
├── config/
│   ├── config.json                 # Main system configuration
│   ├── development_template.json   # Development settings template
│   └── production_template.json    # Production settings template
├── EA_CONFIG_REFERENCE.md          # EA parameter quick reference
└── INSTALLATION_GUIDE.md           # Installation and initial setup
```

### MetaTrader 5 EA Configuration
- **EA Files**: Located in `EA/` directory
- **Parameters**: Configured when attaching EA to chart
- **Settings**: Stored in MetaTrader terminal

## 🎯 Core System Configuration

### 1. Main Configuration File (config/config.json)

#### Basic Structure
```json
{
  "deployment_type": "development",
  "debug_mode": true,
  "logging_level": "INFO",
  
  "server": {
    "ai_server_port": 5000,
    "dashboard_port": 8080,
    "host": "127.0.0.1"
  },
  
  "ai": {
    "api_key": "your_openai_api_key_here",
    "model": "gpt-4",
    "signal_fusion": {
      "ml_weight": 0.4,
      "technical_weight": 0.4,
      "gpt4_weight": 0.2
    }
  },
  
  "trading": {
    "risk_per_trade": 0.01,
    "max_positions": 3,
    "default_timeframe": "M1"
  },
  
  "components": {
    "ai_server": true,
    "dashboard": true,
    "model_registry": true,
    "trade_logger": true,
    "backtesting": false
  }
}
```

### 2. Deployment Type Configurations

#### Development Configuration
```json
{
  "deployment_type": "development",
  "debug_mode": true,
  "logging_level": "DEBUG",
  "server": {
    "ai_server_port": 5000,
    "dashboard_port": 8080,
    "auto_reload": true
  },
  "components": {
    "all_components": true,
    "research_tools": true,
    "backtesting": true
  }
}
```

#### Production Configuration
```json
{
  "deployment_type": "production",
  "debug_mode": false,
  "logging_level": "INFO",
  "server": {
    "ai_server_port": 5000,
    "dashboard_port": 8080,
    "workers": 4
  },
  "components": {
    "ai_server": true,
    "dashboard": true,
    "model_registry": true,
    "trade_logger": true,
    "research_tools": false
  }
}
```

## 🤖 AI Signal Configuration

### 1. Signal Fusion Weights

#### Balanced Approach (Default)
```json
{
  "ai": {
    "signal_fusion": {
      "ml_weight": 0.4,        // Machine learning models
      "technical_weight": 0.4,  // Technical indicators
      "gpt4_weight": 0.2       // GPT-4 analysis
    }
  }
}
```

#### Conservative Approach
```json
{
  "ai": {
    "signal_fusion": {
      "ml_weight": 0.3,
      "technical_weight": 0.5,  // Higher weight on proven indicators
      "gpt4_weight": 0.2
    }
  }
}
```

#### Aggressive AI Approach
```json
{
  "ai": {
    "signal_fusion": {
      "ml_weight": 0.6,        // Higher ML weight
      "technical_weight": 0.2,
      "gpt4_weight": 0.2
    }
  }
}
```

### 2. ML Model Configuration

#### Model Selection
```json
{
  "ml_models": {
    "primary_model": "lstm_ensemble",
    "secondary_model": "xgboost_regressor",
    "confidence_threshold": 0.7,
    "models_enabled": {
      "lstm": true,
      "xgboost": true,
      "random_forest": true,
      "svm": false
    }
  }
}
```

#### Model Parameters
```json
{
  "model_parameters": {
    "lstm": {
      "sequence_length": 60,
      "features": ["price", "volume", "rsi", "macd"],
      "batch_size": 32,
      "epochs": 100
    },
    "xgboost": {
      "n_estimators": 100,
      "max_depth": 6,
      "learning_rate": 0.1,
      "subsample": 0.8
    }
  }
}
```

### 3. Technical Analysis Configuration

#### Indicator Settings
```json
{
  "technical_analysis": {
    "indicators": {
      "rsi": {
        "period": 14,
        "overbought": 70,
        "oversold": 30,
        "weight": 0.3
      },
      "macd": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "weight": 0.3
      },
      "bollinger_bands": {
        "period": 20,
        "std_dev": 2.0,
        "weight": 0.2
      },
      "ema": {
        "periods": [9, 21, 50],
        "weight": 0.2
      }
    }
  }
}
```

#### Confluence Scoring
```json
{
  "confluence": {
    "minimum_score": 60,      // Minimum confluence percentage
    "required_indicators": 3, // Minimum indicators agreeing
    "weights": {
      "trend": 0.4,
      "momentum": 0.3,
      "volatility": 0.3
    }
  }
}
```

## 💰 Trading Configuration

### 1. Risk Management Settings

#### Account Risk Limits
```json
{
  "risk_management": {
    "max_risk_per_trade": 0.02,      // 2% per trade
    "max_daily_loss": 0.05,          // 5% daily limit
    "max_drawdown": 0.15,            // 15% maximum drawdown
    "max_positions": 3,              // Maximum concurrent positions
    "position_correlation_limit": 0.7 // Maximum correlation between positions
  }
}
```

#### Position Sizing
```json
{
  "position_sizing": {
    "method": "fixed_fractional",    // Options: fixed_fractional, kelly, volatility_adjusted
    "base_risk": 0.01,              // Base risk percentage
    "volatility_adjustment": true,   // Adjust for market volatility
    "max_position_size": 1.0,       // Maximum position size (lots)
    "min_position_size": 0.01       // Minimum position size (lots)
  }
}
```

### 2. Trading Hours Configuration

#### Session Management
```json
{
  "trading_hours": {
    "timezone": "GMT",
    "sessions": {
      "asian": {
        "enabled": true,
        "start": "00:00",
        "end": "09:00",
        "risk_multiplier": 0.8
      },
      "london": {
        "enabled": true,
        "start": "07:00",
        "end": "16:00",
        "risk_multiplier": 1.0
      },
      "new_york": {
        "enabled": true,
        "start": "13:00",
        "end": "22:00",
        "risk_multiplier": 1.2
      }
    },
    "avoid_news": true,
    "news_buffer_minutes": 30
  }
}
```

#### Day-of-Week Settings
```json
{
  "trading_days": {
    "monday": {"enabled": true, "risk_multiplier": 0.9},
    "tuesday": {"enabled": true, "risk_multiplier": 1.0},
    "wednesday": {"enabled": true, "risk_multiplier": 1.0},
    "thursday": {"enabled": true, "risk_multiplier": 1.0},
    "friday": {"enabled": true, "risk_multiplier": 0.8},
    "saturday": {"enabled": false},
    "sunday": {"enabled": false}
  }
}
```

## 📊 Dashboard Configuration

### 1. Display Settings
```json
{
  "dashboard": {
    "update_frequency": 1,           // Seconds between updates
    "chart_timeframes": ["M1", "M5", "M15"],
    "performance_metrics": {
      "show_equity_curve": true,
      "show_drawdown": true,
      "show_trade_distribution": true,
      "show_signal_analysis": true
    },
    "alerts": {
      "enabled": true,
      "sound_alerts": false,
      "browser_notifications": true
    }
  }
}
```

### 2. Alert Configuration
```json
{
  "alerts": {
    "performance": {
      "drawdown_warning": 0.05,      // 5% drawdown warning
      "drawdown_critical": 0.10,     // 10% drawdown critical
      "win_rate_threshold": 0.55,    // Alert if win rate < 55%
      "daily_loss_limit": 0.03       // Alert at 3% daily loss
    },
    "system": {
      "component_failure": true,
      "api_connection_issues": true,
      "data_feed_interruption": true
    },
    "notification_channels": {
      "dashboard": true,
      "telegram": false,
      "email": false
    }
  }
}
```

## 🔌 Component Configuration

### 1. AI Server Settings
```json
{
  "ai_server": {
    "port": 5000,
    "host": "127.0.0.1",
    "workers": 1,
    "timeout": 30,
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60
    },
    "caching": {
      "enabled": true,
      "ttl": 300
    }
  }
}
```

### 2. Model Registry Configuration
```json
{
  "model_registry": {
    "auto_update": true,
    "update_frequency": "daily",
    "model_validation": {
      "enabled": true,
      "validation_split": 0.2,
      "min_accuracy": 0.6
    },
    "model_storage": {
      "path": "models/",
      "compression": true,
      "backup_count": 5
    }
  }
}
```

### 3. Logging Configuration
```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_rotation": {
      "enabled": true,
      "max_size_mb": 10,
      "backup_count": 5
    },
    "loggers": {
      "ai_server": "INFO",
      "dashboard": "INFO",
      "trading": "DEBUG",
      "risk_management": "DEBUG"
    }
  }
}
```

## 🎯 MetaTrader 5 EA Configuration

### 1. Essential EA Parameters

#### Account Settings
```
Account_Type = DEMO               // Start with demo
Broker_Name = "Your Broker"       // Your broker name
Magic_Number = 12345              // Unique identifier
```

#### Trading Parameters
```
Lot_Size = 0.01                   // Position size
Max_Trades = 3                    // Maximum concurrent trades
Risk_Percent = 1.0                // Risk per trade (%)
```

#### AI Configuration
```
AI_Server_URL = "http://127.0.0.1:5000/ai_signal"
AI_Confidence_Threshold = 0.70    // Minimum confidence
AI_Request_Timeout = 10           // Server timeout (seconds)
Use_OpenAI = true                 // Enable GPT-4 integration
```

### 2. Risk Management Parameters
```
Max_Daily_Loss = 100.0            // Daily loss limit
Max_Drawdown = 15.0               // Maximum drawdown (%)
Use_Trailing_Stop = true          // Enable trailing stops
Breakeven_Points = 10             // Move to breakeven points
```

### 3. Technical Indicator Settings
```
Use_RSI_Filter = true             // Enable RSI confluence
Use_MACD_Filter = true            // Enable MACD confluence
Use_BB_Filter = true              // Enable Bollinger Bands
Confluence_Score_Min = 60         // Minimum confluence score
RSI_Period = 14                   // RSI calculation period
MACD_Fast = 12                    // MACD fast EMA
MACD_Slow = 26                    // MACD slow EMA
BB_Period = 20                    // Bollinger Bands period
```

## 🔧 Configuration Management

### 1. Using Configuration Templates

#### Copy and Customize
```bash
# Copy development template
cp config/development_template.json config/config.json

# Copy production template
cp config/production_template.json config/config.json
```

#### Environment-Specific Configs
```bash
# Development
export CONFIG_FILE=config/development.json

# Production
export CONFIG_FILE=config/production.json

# Start with specific config
python core/system_orchestrator_enhanced.py start --config=$CONFIG_FILE
```

### 2. Configuration Validation

#### Validate Configuration
```bash
# Validate current configuration
python core/system_orchestrator_enhanced.py validate-config

# Validate specific config file
python core/system_orchestrator_enhanced.py validate-config --config=config/production.json
```

#### Common Validation Errors
- Invalid JSON syntax
- Missing required fields
- Invalid parameter ranges
- Conflicting settings

### 3. Dynamic Configuration Updates

#### Runtime Configuration Changes
```python
# Example: Update risk parameters during runtime
import requests

config_update = {
    "risk_management": {
        "max_risk_per_trade": 0.015  # Change from 2% to 1.5%
    }
}

response = requests.post(
    "http://localhost:5000/api/config/update",
    json=config_update
)
```

## 📝 Configuration Best Practices

### 1. Development vs Production

#### Development Settings
- Enable debug mode
- Verbose logging
- All components enabled
- Lower risk limits
- Shorter update intervals

#### Production Settings
- Disable debug mode
- INFO level logging
- Core components only
- Appropriate risk limits
- Optimized update intervals

### 2. Performance Optimization

#### High-Performance Settings
```json
{
  "performance": {
    "use_caching": true,
    "parallel_processing": true,
    "optimize_memory": true,
    "reduce_logging": true
  }
}
```

#### Resource-Constrained Settings
```json
{
  "resource_optimization": {
    "limit_history": 1000,
    "reduce_indicators": true,
    "simple_dashboard": true,
    "minimal_logging": true
  }
}
```

### 3. Security Considerations

#### API Key Management
```json
{
  "security": {
    "api_keys": {
      "use_environment_variables": true,
      "rotate_keys_regularly": true,
      "restrict_api_access": true
    }
  }
}
```

#### Network Security
```json
{
  "network": {
    "bind_to_localhost": true,
    "use_https": true,
    "rate_limiting": true,
    "access_control": true
  }
}
```

## 🚨 Troubleshooting Configuration Issues

### Common Problems

#### 1. Configuration Not Loading
```bash
# Check file permissions
ls -la config/config.json

# Validate JSON syntax
python -m json.tool config/config.json
```

#### 2. Invalid Parameters
```bash
# Check logs for validation errors
tail -f logs/system.log

# Use configuration validator
python core/system_orchestrator_enhanced.py validate-config
```

#### 3. Component Conflicts
- Check port conflicts
- Verify resource requirements
- Review dependency requirements

### Recovery Procedures

#### Reset to Default Configuration
```bash
# Backup current config
cp config/config.json config/config.backup.json

# Reset to default
python core/system_orchestrator_enhanced.py reset-config
```

#### Incremental Configuration Testing
```bash
# Test minimal configuration first
python core/system_orchestrator_enhanced.py start --minimal

# Gradually add components
python core/system_orchestrator_enhanced.py add-component dashboard
```

---

## 🎯 Quick Reference

### Essential Configuration Commands
```bash
# Interactive configuration
python core/system_orchestrator_enhanced.py interactive-setup

# Validate configuration
python core/system_orchestrator_enhanced.py validate-config

# Start with specific config
python core/system_orchestrator_enhanced.py start --config=custom.json

# Reset configuration
python core/system_orchestrator_enhanced.py reset-config
```

### Key Configuration Files
- `config/config.json` - Main system configuration
- `EA_CONFIG_REFERENCE.md` - EA parameter reference
- `INSTALLATION_GUIDE.md` - Initial setup guidance

### Configuration Priority Order
1. Command line arguments
2. Environment variables
3. Configuration file
4. Default values

**Remember**: Always test configuration changes on a demo account before applying to live trading. Backup your working configuration before making significant changes.

*Next: [System Architecture](04_System_Architecture.md) to understand the system structure.*
