# AI Gold Scalper EA Files

**✅ COMPILATION STATUS: SUCCESSFUL** - EA compiled without errors on 2025-07-27

**🏆 OPTIMIZED FOR XAUUSD (GOLD/USD) TRADING**

This directory contains all the necessary files for the AI Gold Scalper Expert Advisor (EA) for MetaTrader 5, specifically optimized for gold trading with auto-detection and parameter adjustment.

## Files Included

### Main EA Files
- **AI_Gold_Scalper.mq5** - Main EA source code
- **AI_Gold_Scalper.ex5** - Compiled EA executable (ready to use)
- **EA_Trade_Logger.mq5** - Trade logging utility

### Supporting Modules (server directory)
- **enhanced_logging.mq5** - Advanced logging functionality
- **ml_integration.mq5** - Machine learning integration and feature engineering
- **performance_analytics.mq5** - Performance tracking and advanced metrics
- **risk_management_enhanced.mq5** - Enhanced risk management and position sizing
- **telegram_alerts_addon.mq5** - Telegram notification system
- **trade_journal_addon.mq5** - Trade journaling functionality
- **adaptive_learning_engine.mq5** - Continuous strategy optimization
- **postmortem_analysis.mq5** - Trade failure analysis and improvement

## Quick Installation

### Option 1: Automated Deployment (Recommended)
1. Go back to the main project directory: `cd "G:\My Drive\AI_Gold_Scalper"`
2. Run the deployment script: `.\deploy_ea.ps1 -AutoDetect`
3. Follow the on-screen instructions

### Option 2: Manual Installation
1. Open MetaTrader 5
2. Go to **File → Open Data Folder**
3. Navigate to **MQL5 → Experts**
4. Copy all files from this EA directory to the Experts folder
5. Restart MetaTrader 5 or refresh the Navigator panel

## MetaTrader 5 Configuration

After copying the files, you must configure MetaTrader 5:

1. **Enable WebRequest URLs**:
   - Go to **Tools → Options → Expert Advisors**
   - Check "Allow WebRequest for listed URL"
   - Add these URLs:
     - `http://127.0.0.1:5000`
     - `https://api.openai.com`
     - `https://api.telegram.org`

2. **Enable Automated Trading**:
   - Check "Allow automated trading"
   - Check "Allow DLL imports" (if needed)

## Starting the EA

1. **Start the AI Server**:
   ```bash
   cd "G:\My Drive\AI_Gold_Scalper"
   python core/enhanced_ai_server_consolidated.py
   ```

2. **Attach EA to Chart**:
   - Open a Gold (XAUUSD) chart in MetaTrader 5
   - Set timeframe to M1 (1-minute)
   - Drag AI_Gold_Scalper from Navigator to the chart
   - Configure parameters as needed
   - Click OK to start

## Important Notes

- **Always test on demo account first**
- **Configure risk management parameters carefully**
- **Monitor the EA performance regularly**
- **Keep the AI server running for the EA to function**

## For Detailed Instructions

See the main `INSTALLATION_GUIDE.md` in the project root directory for comprehensive setup instructions, configuration options, and troubleshooting information.

## Support

If you encounter issues:
1. Check the MetaTrader 5 Experts log
2. Verify AI server is running and accessible
3. Ensure WebRequest URLs are properly configured
4. Review the detailed installation guide
