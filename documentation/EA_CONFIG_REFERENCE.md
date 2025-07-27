# AI Gold Scalper EA - Configuration Quick Reference

## Essential Parameters for First-Time Setup

### 🔧 Account Settings
| Parameter | Recommended Value | Description |
|-----------|------------------|-------------|
| **Account_Type** | `DEMO` | Start with DEMO for testing |
| **Broker_Name** | `Your Broker` | Your broker's name for logging |
| **Magic_Number** | `12345` | Unique EA identifier |

### 💰 Trading Parameters
| Parameter | Demo Value | Live Value | Description |
|-----------|------------|------------|-------------|
| **Lot_Size** | `0.01` | `0.01-0.1` | Position size per trade |
| **Max_Trades** | `3` | `3-5` | Maximum concurrent trades |
| **Risk_Percent** | `1.0` | `1.0-2.0` | Risk per trade (% of account) |

### 🤖 AI Configuration
| Parameter | Value | Description |
|-----------|--------|-------------|
| **AI_Server_URL** | `http://127.0.0.1:5000/ai_signal` | Local AI server endpoint |
| **AI_Confidence_Threshold** | `0.70` | Minimum confidence for trades |
| **AI_Request_Timeout** | `10` | Server timeout in seconds |
| **Use_OpenAI** | `true` | Enable OpenAI integration |

### ⚠️ Risk Management
| Parameter | Conservative | Aggressive | Description |
|-----------|-------------|------------|-------------|
| **Max_Daily_Loss** | `50` | `100` | Daily loss limit (currency) |
| **Max_Drawdown** | `10.0` | `20.0` | Max drawdown percentage |
| **Use_Trailing_Stop** | `true` | `true` | Enable trailing stops |
| **Breakeven_Points** | `10` | `5` | Points to move to breakeven |

### ⏰ Trading Hours (GMT+0)
| Parameter | Asian Session | London Session | NY Session |
|-----------|--------------|----------------|------------|
| **Trading_Start_Hour** | `0` | `7` | `13` |
| **Trading_End_Hour** | `9` | `16` | `22` |

### 📈 Technical Indicators
| Parameter | Recommended | Description |
|-----------|-------------|-------------|
| **Use_RSI_Filter** | `true` | Enable RSI confluence |
| **Use_MACD_Filter** | `true` | Enable MACD confluence |
| **Use_BB_Filter** | `true` | Enable Bollinger Bands |
| **Confluence_Score_Min** | `60` | Minimum confluence score |

## Quick Setup Checklist

### ✅ Pre-Installation
- [ ] MetaTrader 5 installed and updated
- [ ] Valid trading account (demo for testing)
- [ ] Python 3.8+ installed
- [ ] OpenAI API key obtained

### ✅ Installation
- [ ] EA files copied to MetaTrader Experts folder
- [ ] WebRequest URLs added to MT5 whitelist
- [ ] Automated trading enabled in MT5
- [ ] AI server dependencies installed (`pip install -r requirements.txt`)

### ✅ Configuration
- [ ] OpenAI API key added to `config/config.json`
- [ ] AI server started (`python core/consolidated_ai_server.py`)
- [ ] EA attached to Gold (XAUUSD) M1 chart
- [ ] Parameters configured according to risk tolerance
- [ ] Dashboard enabled for monitoring

### ✅ Testing
- [ ] Demo account testing for 24-48 hours
- [ ] Trade execution verified
- [ ] Risk management functioning
- [ ] Performance metrics tracking
- [ ] No error messages in logs

## Common Parameter Combinations

### 🟢 Conservative Setup (Low Risk, Stable Returns)
```
Lot_Size = 0.01
Risk_Percent = 1.0
Max_Trades = 2
AI_Confidence_Threshold = 0.75
Max_Daily_Loss = 30
Confluence_Score_Min = 70
```

### 🟡 Balanced Setup (Medium Risk, Good Returns)
```
Lot_Size = 0.05
Risk_Percent = 1.5
Max_Trades = 3
AI_Confidence_Threshold = 0.70
Max_Daily_Loss = 50
Confluence_Score_Min = 60
```

### 🔴 Aggressive Setup (Higher Risk, Higher Returns)
```
Lot_Size = 0.10
Risk_Percent = 2.0
Max_Trades = 5
AI_Confidence_Threshold = 0.65
Max_Daily_Loss = 100
Confluence_Score_Min = 50
```

## URL Whitelist (Copy & Paste Ready)

Add these URLs to MetaTrader 5 → Tools → Options → Expert Advisors → WebRequest:

```
http://127.0.0.1:5000
https://api.openai.com
https://api.telegram.org
```

## Critical Settings Verification

### ⚠️ Must Check Before Going Live
1. **Account Type**: Set to LIVE only after thorough demo testing
2. **Lot Size**: Start small, scale gradually
3. **Risk Percent**: Never exceed 3% per trade
4. **Max Daily Loss**: Set appropriate stop-loss for your account
5. **AI Server**: Ensure it's running and accessible
6. **Trading Hours**: Align with your preferred market sessions

## Performance Monitoring

### 📊 Key Metrics to Watch
- **Win Rate**: Target >60%
- **Profit Factor**: Target >1.2
- **Max Drawdown**: Keep <20%
- **Daily P&L**: Track consistency
- **Trades per Day**: Monitor frequency

### 🚨 Warning Signs
- Win rate dropping below 50%
- Consecutive losses >5
- Drawdown exceeding risk limits
- AI server connection errors
- Unusual trade behavior

## Emergency Procedures

### 🛑 If Things Go Wrong
1. **Immediate**: Disable automated trading in MT5
2. **Close Positions**: Manually close all open trades if necessary
3. **Check Logs**: Review EA and AI server logs
4. **Verify Settings**: Double-check all parameters
5. **Demo Test**: Return to demo account for troubleshooting

---

**💡 Pro Tip**: Always keep a trading journal and regularly backup your EA settings. Success in automated trading comes from continuous monitoring and gradual optimization, not from "set and forget" approaches.
