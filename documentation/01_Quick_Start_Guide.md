# Quick Start Guide - AI Gold Scalper

## 📋 Overview

This guide will get you up and running with the AI Gold Scalper system in 15 minutes. Perfect for users who want to start trading immediately with minimal setup.

## 🎯 Prerequisites

- **Python 3.8+** installed on your system
- **MetaTrader 5** (for live trading) or demo account
- **Minimum 4GB RAM** (8GB recommended for full features)
- **Internet connection** for market data and GPT-4 features

## 🚀 15-Minute Setup

### Step 1: System Initialization (5 minutes)

1. **Navigate to the AI Gold Scalper directory**
   ```bash
   cd "G:\My Drive\AI_Gold_Scalper"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the interactive setup**
   ```bash
   python core/system_orchestrator_enhanced.py interactive-setup
   ```

### Step 2: Configuration Wizard (5 minutes)

The interactive setup will guide you through:

1. **Deployment Type Selection**
   - Choose "Development" for local testing
   - Choose "Production" for VPS deployment

2. **OpenAI API Key (Optional)**
   - Enter your OpenAI API key for GPT-4 features
   - Skip if you want to use only technical analysis

3. **AI Signal Weights**
   - Default: ML Models (40%), Technical Analysis (40%), GPT-4 (20%)
   - Adjust based on your preferences

4. **Component Selection**
   - **Beginners**: Choose "Full Development Suite" 
   - **Advanced**: Choose "Custom selection" for specific components

### Step 3: System Launch (5 minutes)

1. **Start the system**
   ```bash
   python core/system_orchestrator_enhanced.py start
   ```

2. **Verify system health**
   - Open browser to `http://localhost:5000/health`
   - Should return `{"status": "healthy"}`

3. **Access the dashboard**
   - Open browser to `http://localhost:8080`
   - View real-time system performance

## 🎯 First Trading Session

### Option A: Demo Trading (Recommended)

1. **Connect MT5 Demo Account**
   - Install MT5 with demo account
   - Attach the AI Gold Scalper EA
   - Enable automated trading

2. **Monitor Performance**
   - Watch dashboard at `http://localhost:8080`
   - Observe trade signals and execution
   - Review system logs

### Option B: Backtesting First

1. **Run backtesting**
   ```bash
   python core/system_orchestrator_enhanced.py backtest
   ```

2. **Review results**
   - Check backtesting reports in `/logs/backtesting/`
   - Analyze performance metrics
   - Adjust configuration if needed

## 📊 Key URLs & Endpoints

| Service | URL | Purpose |
|---------|-----|---------|
| **AI Server** | `http://localhost:5000` | Core AI trading signals |
| **Health Check** | `http://localhost:5000/health` | System status |
| **Dashboard** | `http://localhost:8080` | Performance monitoring |
| **System Status** | `http://localhost:8080/api/system-status` | Component status |

## 🔧 Basic Commands

```bash
# Start the system
python core/system_orchestrator_enhanced.py start

# Check system status
python core/system_orchestrator_enhanced.py status

# Stop the system
python core/system_orchestrator_enhanced.py stop

# Restart the system
python core/system_orchestrator_enhanced.py restart

# Run backtesting
python core/system_orchestrator_enhanced.py backtest
```

## 💡 Default Configuration

The system starts with these sensible defaults:

- **AI Server**: Port 5000
- **Dashboard**: Port 8080
- **Signal Fusion**: 40% ML, 40% Technical, 20% GPT-4
- **Risk Management**: 0.5% risk per trade
- **Components**: Core components (AI server, model registry, trade logger)

## ⚠️ Important First Steps

1. **Test with Demo Account First**
   - Never start with live trading
   - Understand system behavior
   - Verify signal quality

2. **Monitor Initial Performance**
   - Watch first 10-20 trades closely
   - Review signal accuracy
   - Adjust risk settings if needed

3. **Understand the Dashboard**
   - Learn key performance metrics
   - Monitor system health indicators
   - Set up alerts for issues

## 🔄 Next Steps

After your quick start:

1. **Read [System Overview](02_System_Overview.md)** - Understand what you're running
2. **Study [Configuration Guide](21_Configuration_Guide.md)** - Customize your setup
3. **Explore [Performance Dashboard](14_Performance_Dashboard.md)** - Monitor effectively
4. **Learn [Risk Management](16_Risk_Management.md)** - Trade safely

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| **System won't start** | Check Python version, install requirements |
| **Health check fails** | Restart system, check logs in `/logs/` |
| **No dashboard** | Verify port 8080 is available |
| **No trading signals** | Check MT5 connection, API endpoints |
| **Poor performance** | Review configuration, increase resources |

## 📈 Success Indicators

You'll know your setup is working when:

- ✅ Health check returns "healthy"
- ✅ Dashboard loads and shows data
- ✅ System status shows components running
- ✅ Trade signals appear in MT5
- ✅ Logs show normal activity

## 🎯 Quick Configuration Tips

- **Conservative Trading**: Reduce risk per trade to 0.1-0.2%
- **Aggressive Trading**: Increase ML weight to 60%
- **Research Mode**: Enable all components for maximum analysis
- **Production Mode**: Use only core components for stability

---

**🚀 Congratulations! You now have the AI Gold Scalper system running. Happy trading!**

*Next: [System Overview](02_System_Overview.md) to understand what you've just deployed.*
