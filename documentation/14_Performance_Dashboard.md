# Performance Dashboard Guide - AI Gold Scalper

## 📊 Overview

The AI Gold Scalper Performance Dashboard provides real-time monitoring and analytics for your trading system. Access it at `http://localhost:8080` when the system is running.

## 🎯 Dashboard Components

### 1. System Health Panel

**Location**: Top of dashboard  
**Purpose**: Monitor overall system status

| Indicator | Status | Description |
|-----------|--------|-------------|
| 🟢 **Healthy** | All systems operational | System running normally |
| 🟡 **Warning** | Minor issues detected | Check logs for details |
| 🔴 **Error** | Critical issues | System needs attention |

### 2. Trading Performance Metrics

#### Real-Time Statistics
- **Total Trades**: Number of executed trades
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / Gross loss ratio
- **Current Drawdown**: Maximum equity decline
- **Daily P&L**: Today's profit/loss

#### Key Performance Indicators (KPIs)
```
Target Metrics:
- Win Rate: >60%
- Profit Factor: >1.3
- Max Drawdown: <15%
- Sharpe Ratio: >1.0
- Recovery Factor: >2.0
```

### 3. AI Signal Analysis

#### Signal Quality Metrics
- **Signal Confidence**: Average confidence of executed trades
- **Signal Distribution**: Buy vs Sell signal frequency
- **Confluence Score**: Technical indicator agreement
- **GPT-4 Integration**: AI analysis contribution

#### Signal Sources Breakdown
- **ML Models**: Machine learning prediction accuracy
- **Technical Analysis**: Indicator-based signals
- **GPT-4 Analysis**: AI market sentiment

### 4. Risk Management Dashboard

#### Position Monitoring
- **Current Exposure**: Active position sizes
- **Risk per Trade**: Percentage risk per position
- **Account Equity**: Real-time account balance
- **Margin Usage**: Used vs available margin

#### Risk Alerts
- 🚨 **High Drawdown**: >10% equity decline
- ⚠️ **Position Size**: Exceeding risk limits
- 📊 **Correlation**: High position correlation

## 🔧 Dashboard Configuration

### Accessing Dashboard Settings

1. **Navigate to Settings Panel**
   ```
   http://localhost:8080/settings
   ```

2. **Configure Display Options**
   - Update frequency (1-60 seconds)
   - Chart timeframes
   - Metric thresholds
   - Alert preferences

### Customizing Views

#### Chart Configuration
```javascript
// Example: Customize P&L chart
{
  "timeframe": "1H",
  "indicators": ["EMA20", "RSI", "MACD"],
  "overlays": ["Support/Resistance"]
}
```

#### Metric Thresholds
```json
{
  "win_rate_threshold": 60,
  "drawdown_alert": 10,
  "profit_factor_min": 1.3,
  "confidence_threshold": 0.7
}
```

## 📈 Performance Analysis

### 1. Equity Curve Analysis

**Purpose**: Track account growth over time

Key Features:
- Real-time equity updates
- Drawdown visualization
- Recovery periods
- Trend analysis

**Reading the Curve**:
- Steady upward trend = Good performance
- High volatility = Review risk settings
- Extended drawdown = System adjustment needed

### 2. Trade Distribution Analysis

#### Win/Loss Analysis
- Trade outcome distribution
- Average win vs average loss
- Consecutive wins/losses
- Time-based performance

#### Signal Performance by Type
```
Buy Signals:
- Total: 150 trades
- Win Rate: 65%
- Avg Profit: $12.50

Sell Signals:
- Total: 145 trades  
- Win Rate: 58%
- Avg Profit: $10.80
```

### 3. Market Condition Performance

#### Trending Markets
- Performance during strong trends
- Breakout trade success rate
- Trend following effectiveness

#### Ranging Markets
- Scalping performance
- Mean reversion success
- Support/resistance trading

## 🚨 Alert System

### Setting Up Alerts

1. **Performance Alerts**
   - Drawdown exceeds threshold
   - Win rate drops below target
   - Unusual trade frequency

2. **Technical Alerts**
   - System component failures
   - API connection issues
   - Data feed interruptions

3. **Risk Alerts**
   - Position size violations
   - Margin call warnings
   - Correlation limit breaches

### Alert Configuration
```json
{
  "alerts": {
    "drawdown_limit": 10.0,
    "win_rate_minimum": 55.0,
    "daily_loss_limit": 100.0,
    "system_downtime": 300
  },
  "notification_channels": ["dashboard", "email", "telegram"]
}
```

## 📊 Key Dashboard URLs

| Function | URL | Description |
|----------|-----|-------------|
| **Main Dashboard** | `http://localhost:8080` | Primary monitoring interface |
| **Performance** | `http://localhost:8080/performance` | Detailed performance metrics |
| **System Status** | `http://localhost:8080/api/system-status` | Component health check |
| **Trade Log** | `http://localhost:8080/trades` | Recent trade history |
| **Settings** | `http://localhost:8080/settings` | Dashboard configuration |

## 🔍 Troubleshooting Dashboard Issues

### Common Problems

#### Dashboard Not Loading
```bash
# Check if dashboard service is running
python core/system_orchestrator_enhanced.py status

# Restart dashboard
python core/system_orchestrator_enhanced.py restart-dashboard
```

#### Missing Data
- Verify AI server connection
- Check MetaTrader 5 integration
- Review data feed status

#### Slow Performance
- Reduce update frequency
- Clear browser cache
- Check system resources

### Performance Optimization

#### Browser Settings
- Use Chrome or Firefox for best performance
- Enable hardware acceleration
- Clear cache regularly

#### System Resources
- Monitor CPU/RAM usage
- Close unnecessary applications
- Consider dedicated monitoring system

## 📱 Mobile Access

### Responsive Design
The dashboard automatically adapts to mobile devices:
- Touch-friendly interface
- Simplified charts
- Essential metrics only
- Quick alert access

### Mobile Optimization Tips
1. Use landscape mode for charts
2. Enable push notifications
3. Bookmark key dashboard pages
4. Use mobile data cautiously

## 🎯 Best Practices

### Daily Monitoring Routine
1. **Morning Check** (5 minutes)
   - System health status
   - Overnight performance
   - Market condition assessment

2. **Midday Review** (10 minutes)
   - Trade execution quality
   - Risk metrics review
   - Adjust settings if needed

3. **Evening Analysis** (15 minutes)
   - Daily performance summary
   - Signal accuracy review
   - Plan for next session

### Performance Optimization
- Monitor win rate trends
- Adjust risk parameters based on drawdown
- Review signal sources effectiveness
- Optimize for current market conditions

## 🔄 Integration with Trading

### MetaTrader 5 Integration
- Real-time position updates
- Trade execution confirmation
- Account balance synchronization
- Margin level monitoring

### Data Synchronization
- 1-second update frequency
- Real-time price feeds
- Historical data backfill
- Multi-timeframe analysis

## 📈 Advanced Features

### Custom Metrics
Create custom performance indicators:
```python
# Example: Custom risk-adjusted return
def calculate_risk_adjusted_return(equity_curve, max_drawdown):
    return (equity_curve[-1] / equity_curve[0] - 1) / max_drawdown
```

### Export Functionality
- CSV export of performance data
- PDF report generation
- Email performance summaries
- API access for external tools

---

## 🎯 Quick Reference

### Essential Metrics to Monitor
1. **Win Rate** (Target: >60%)
2. **Profit Factor** (Target: >1.3)
3. **Max Drawdown** (Limit: <15%)
4. **Daily P&L** (Track consistency)
5. **Signal Confidence** (Monitor quality)

### Warning Signs
- 🚨 Win rate dropping below 50%
- 🚨 Drawdown exceeding 15%
- 🚨 System components showing errors
- 🚨 Unusual trade frequency patterns

**Remember**: The dashboard is your primary tool for monitoring system health and trading performance. Regular monitoring prevents small issues from becoming major problems.

*Next: [Risk Management Guide](16_Risk_Management.md) for safe trading practices.*
