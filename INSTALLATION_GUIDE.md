# AI Gold Scalper EA - Installation & Setup Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Installation Steps](#installation-steps)
4. [MetaTrader 5 Configuration](#metatrader-5-configuration)
5. [AI Server Setup](#ai-server-setup)
6. [EA Configuration](#ea-configuration)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [VPS Deployment](#vps-deployment)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11 (64-bit recommended)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Internet**: Stable broadband connection
- **MetaTrader 5**: Latest version

### Recommended for Production
- **VPS**: Windows VPS with 24/7 uptime
- **RAM**: 8GB or higher
- **CPU**: Multi-core processor
- **Internet**: Low-latency connection (<50ms to broker)

## Prerequisites

### Required Software
1. **MetaTrader 5**: Download from your broker or MetaQuotes
2. **Python 3.8+**: For AI server (if running locally)
3. **Git**: For version control and updates

### Required Accounts/APIs
- Valid MetaTrader 5 trading account
- OpenAI API key (for AI analysis)
- Telegram Bot Token (optional, for alerts)

## Installation Steps

### Step 1: Locate MetaTrader 5 Data Directory

1. Open MetaTrader 5
2. Go to **File → Open Data Folder**
3. Navigate to **MQL5 → Experts**
4. Note the full path (typically):
   ```
   C:\Users\{YourUsername}\AppData\Roaming\MetaQuotes\Terminal\{INSTANCE_ID}\MQL5\Experts
   ```

### Step 2: Copy EA Files

1. **Main EA Files**: Copy these files to the `Experts` folder:
   - `AI_Gold_Scalper.mq5` (source code)
   - `AI_Gold_Scalper.ex5` (compiled executable)
   - `EA_Trade_Logger.mq5` (trade logging utility)

2. **Supporting Modules**: Copy these files to the `Experts` folder or create a subfolder:
   - `enhanced_logging.mq5`
   - `ml_integration.mq5`
   - `performance_analytics.mq5`
   - `risk_management_enhanced.mq5`
   - `telegram_alerts_addon.mq5`
   - `trade_journal_addon.mq5`

### Step 3: File Structure Verification

After copying, your Experts folder should contain:
```
MQL5/Experts/
├── AI_Gold_Scalper.mq5
├── AI_Gold_Scalper.ex5
├── EA_Trade_Logger.mq5
├── enhanced_logging.mq5
├── ml_integration.mq5
├── performance_analytics.mq5
├── risk_management_enhanced.mq5
├── telegram_alerts_addon.mq5
└── trade_journal_addon.mq5
```

## MetaTrader 5 Configuration

### Enable WebRequest URLs

1. In MetaTrader 5, go to **Tools → Options → Expert Advisors**
2. Check **"Allow WebRequest for listed URL"**
3. Add these URLs to the list:
   ```
   http://127.0.0.1:5000
   https://api.openai.com
   https://api.telegram.org
   ```
4. Click **OK** to save

### Enable Automated Trading

1. Go to **Tools → Options → Expert Advisors**
2. Check **"Allow automated trading"**
3. Check **"Allow DLL imports"** (if using external libraries)
4. Set **"Max number of bars in chart"** to unlimited or high value
5. Click **OK**

### Chart Setup

1. Open a Gold (XAUUSD) chart
2. Set timeframe to M1 (1-minute) - recommended for scalping
3. Right-click on chart → **Expert Advisors → AI_Gold_Scalper**
4. Configure parameters (see EA Configuration section)

## AI Server Setup

### Option 1: Local AI Server

1. **Install Python Dependencies**:
   ```bash
   cd "G:\My Drive\AI_Gold_Scalper"
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   - Edit `config/config.json`
   - Add your OpenAI API key
   - Configure other settings as needed

3. **Start AI Server**:
   ```bash
   python core/consolidated_ai_server.py
   ```
   
   Server will start on `http://127.0.0.1:5000` by default

### Option 2: Remote AI Server

1. Deploy the AI server to a cloud platform (AWS, Google Cloud, etc.)
2. Update the EA's `AI_Server_URL` parameter to point to your remote server
3. Ensure proper security (HTTPS, authentication) for production use

## EA Configuration

### Essential Parameters

When attaching the EA to a chart, configure these key parameters:

#### Account Settings
- **Account_Type**: Set to LIVE or DEMO
- **Broker_Name**: Your broker's name
- **Account_Number**: Your account number

#### Trading Parameters
- **Lot_Size**: Start with 0.01 for testing
- **Max_Trades**: Maximum concurrent trades (default: 5)
- **Magic_Number**: Unique identifier for EA trades

#### Risk Management
- **Risk_Percent**: Percentage of account to risk per trade (1-3%)
- **Max_Daily_Loss**: Maximum daily loss limit
- **Max_Drawdown**: Maximum portfolio drawdown

#### AI Configuration
- **AI_Server_URL**: `http://127.0.0.1:5000/ai_signal` (or your remote server)
- **AI_Confidence_Threshold**: Minimum confidence for trade execution (0.7)
- **Use_OpenAI**: Enable/disable OpenAI integration

#### Trading Hours
- **Trading_Start_Hour**: Start time (e.g., 8 for 8 AM)
- **Trading_End_Hour**: End time (e.g., 18 for 6 PM)
- **Trade_Monday** through **Trade_Friday**: Enable/disable trading per day

### Advanced Parameters

#### Confluence Indicators
- **Use_RSI_Filter**: Enable RSI confluence
- **Use_MACD_Filter**: Enable MACD confluence
- **Use_BB_Filter**: Enable Bollinger Bands confluence
- **Confluence_Score_Min**: Minimum confluence score

#### Stop Loss & Take Profit
- **Default_SL_Points**: Default stop loss in points
- **Default_TP_Points**: Default take profit in points
- **Use_Trailing_Stop**: Enable trailing stop functionality

## Verification & Testing

### 1. Check EA Loading
1. Attach EA to Gold chart
2. Check **Experts** tab for loading messages
3. Verify no errors in the log

### 2. Test AI Server Connection
1. EA should log successful connection to AI server
2. Check for "AI Server Response" messages in logs
3. Verify JSON parsing is working correctly

### 3. Paper Trading Test
1. Start with demo account
2. Set small lot sizes (0.01)
3. Monitor for 24-48 hours
4. Verify trade execution and management

### 4. Performance Monitoring
1. Check the dashboard display on chart
2. Monitor win rate and profit metrics
3. Review trade journal logs
4. Verify risk management is working

## Troubleshooting

### Common Issues

#### "WebRequest to [URL] failed"
**Solution**: Add the URL to MetaTrader's WebRequest whitelist

#### "AI server not responding"
**Solution**: 
1. Check if AI server is running
2. Verify server URL in EA parameters
3. Check firewall settings

#### "No trades being executed"
**Solution**:
1. Check AI confidence threshold
2. Verify trading hours settings
3. Confirm automated trading is enabled
4. Check account balance and margin

#### "High CPU usage"
**Solution**:
1. Reduce update frequency in EA settings
2. Optimize indicator calculations
3. Consider running on VPS

### Log Files Location
- **EA Logs**: MetaTrader Logs folder
- **AI Server Logs**: `logs/` directory in project folder
- **Trade Journal**: Exported to Files folder in MetaTrader

## VPS Deployment

### Recommended VPS Specifications
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB SSD
- **Location**: Near your broker's servers
- **OS**: Windows Server 2019/2022

### VPS Setup Steps
1. **Install MetaTrader 5** on VPS
2. **Copy EA files** to VPS MetaTrader installation
3. **Deploy AI server** on VPS or use cloud service
4. **Configure networking** (ports, firewall)
5. **Set up monitoring** and alerting
6. **Test connectivity** and latency

### VPS Maintenance
- Regular Windows updates
- MetaTrader 5 updates
- EA version updates
- Performance monitoring
- Backup configurations

## Security Considerations

### API Key Protection
- Store API keys securely
- Use environment variables when possible
- Rotate keys regularly
- Monitor API usage

### Network Security
- Use HTTPS for remote AI server
- Implement authentication
- Use VPN for sensitive operations
- Monitor network traffic

### Trading Security
- Start with small position sizes
- Set appropriate risk limits
- Monitor trades regularly
- Have emergency stop procedures

## Support & Updates

### Getting Help
1. Check this documentation first
2. Review log files for errors
3. Test on demo account
4. Contact support with detailed error descriptions

### Updates
- Check for EA updates regularly
- Update AI server dependencies
- Keep MetaTrader 5 updated
- Backup configurations before updates

---

## Quick Start Checklist

- [ ] MetaTrader 5 installed and configured
- [ ] EA files copied to Experts folder
- [ ] WebRequest URLs added to whitelist
- [ ] AI server running and accessible
- [ ] EA attached to Gold chart with proper parameters
- [ ] Demo testing completed successfully
- [ ] Risk management parameters set appropriately
- [ ] Monitoring and alerting configured

**Remember**: Always test thoroughly on a demo account before using real money. Trading involves significant risk of loss.
