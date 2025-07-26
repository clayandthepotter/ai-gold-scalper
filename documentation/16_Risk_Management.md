# Risk Management Guide - AI Gold Scalper

## 🛡️ Overview

Risk management is the cornerstone of successful automated trading. This guide covers essential risk controls, position sizing, and protective measures to preserve capital while maximizing returns.

## 🎯 Core Risk Management Principles

### 1. Capital Preservation First
- **Never risk more than you can afford to lose**
- **Preserve capital during unfavorable market conditions**
- **Focus on consistent returns over time**
- **Avoid emotional decision-making**

### 2. Position Sizing Rules
```
Conservative: 0.5-1.0% risk per trade
Balanced: 1.0-2.0% risk per trade  
Aggressive: 2.0-3.0% risk per trade
NEVER exceed: 5% risk per trade
```

### 3. Diversification Strategy
- **Multiple timeframes**: M1, M5, M15 analysis
- **Multiple indicators**: RSI, MACD, Bollinger Bands
- **Multiple AI models**: ML + Technical + GPT-4
- **Time diversification**: Spread trades across sessions

## ⚙️ System Risk Controls

### 1. Account-Level Limits

#### Daily Risk Limits
```json
{
  "max_daily_loss": 100.0,        // Maximum daily loss in account currency
  "max_daily_trades": 20,         // Maximum trades per day
  "max_consecutive_losses": 5,    // Stop after N consecutive losses
  "daily_drawdown_limit": 5.0     // Daily drawdown percentage limit
}
```

#### Portfolio Risk Limits
```json
{
  "max_portfolio_exposure": 10.0,  // Maximum total exposure percentage
  "max_correlated_positions": 3,   // Maximum correlated positions
  "account_equity_stop": 20.0,     // Stop trading at 20% account loss
  "margin_usage_limit": 80.0       // Maximum margin utilization
}
```

### 2. Position-Level Controls

#### Stop Loss Management
```python
# Automatic stop loss calculation
def calculate_stop_loss(entry_price, risk_amount, position_size):
    atr = get_average_true_range(14)  # 14-period ATR
    
    # Dynamic stop loss based on volatility
    if atr > 0.5:  # High volatility
        stop_distance = atr * 1.5
    else:  # Normal volatility
        stop_distance = atr * 2.0
    
    return entry_price - stop_distance  # For long positions
```

#### Take Profit Targets
```python
# Risk/Reward ratio optimization
def calculate_take_profit(entry_price, stop_loss, risk_reward_ratio=2.0):
    risk_amount = abs(entry_price - stop_loss)
    take_profit = entry_price + (risk_amount * risk_reward_ratio)
    return take_profit
```

### 3. Time-Based Risk Controls

#### Trading Hours Management
```json
{
  "allowed_sessions": {
    "asian": {"start": "00:00", "end": "09:00", "risk_multiplier": 0.8},
    "london": {"start": "07:00", "end": "16:00", "risk_multiplier": 1.0},
    "new_york": {"start": "13:00", "end": "22:00", "risk_multiplier": 1.2}
  },
  "avoid_news_events": true,
  "high_impact_news_buffer": 30  // Minutes before/after news
}
```

## 📊 Risk Monitoring & Alerts

### 1. Real-Time Risk Metrics

#### Key Risk Indicators (KRIs)
- **Current Drawdown**: Live account equity decline
- **Value at Risk (VaR)**: Potential 24-hour loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Sortino Ratio**: Downside risk measurement
- **Maximum Adverse Excursion**: Worst unrealized loss

#### Risk Dashboard Alerts
```json
{
  "risk_alerts": {
    "drawdown_warning": 5.0,      // Alert at 5% drawdown
    "drawdown_critical": 10.0,    // Critical at 10% drawdown
    "var_exceeded": true,         // Alert when VaR exceeded
    "correlation_spike": 0.8,     // Alert when correlation > 80%
    "margin_warning": 70.0        // Alert at 70% margin usage
  }
}
```

### 2. Automated Risk Responses

#### Circuit Breakers
```python
def check_circuit_breakers():
    """Automated system shutdown triggers"""
    
    # Daily loss limit exceeded
    if daily_loss > MAX_DAILY_LOSS:
        shutdown_trading("Daily loss limit exceeded")
    
    # Consecutive losses limit
    if consecutive_losses >= MAX_CONSECUTIVE_LOSSES:
        reduce_position_size(0.5)  # Reduce by 50%
    
    # Drawdown limit exceeded
    if current_drawdown > MAX_DRAWDOWN:
        enter_recovery_mode()
    
    # System health degraded
    if system_health < MINIMUM_HEALTH_SCORE:
        pause_new_trades()
```

## 🎯 Position Sizing Strategies

### 1. Fixed Fractional Method
```python
def fixed_fractional_sizing(account_balance, risk_percent, stop_loss_points):
    """Calculate position size based on fixed risk percentage"""
    
    risk_amount = account_balance * (risk_percent / 100)
    point_value = get_point_value()  # Value per point for Gold
    
    position_size = risk_amount / (stop_loss_points * point_value)
    return min(position_size, MAX_POSITION_SIZE)
```

### 2. Kelly Criterion (Advanced)
```python
def kelly_position_sizing(win_rate, avg_win, avg_loss):
    """Optimal position sizing using Kelly Criterion"""
    
    # Kelly percentage = (bp - q) / b
    # where b = avg_win/avg_loss, p = win_rate, q = 1-win_rate
    
    b = avg_win / avg_loss
    p = win_rate
    q = 1 - win_rate
    
    kelly_percent = (b * p - q) / b
    
    # Use fractional Kelly to reduce risk
    return min(kelly_percent * 0.25, 0.02)  # Max 2% risk
```

### 3. Volatility-Adjusted Sizing
```python
def volatility_adjusted_sizing(base_size, current_volatility, avg_volatility):
    """Adjust position size based on market volatility"""
    
    volatility_ratio = avg_volatility / current_volatility
    adjusted_size = base_size * volatility_ratio
    
    # Limit adjustment range
    return max(0.5 * base_size, min(2.0 * base_size, adjusted_size))
```

## 🚨 Crisis Management Protocols

### 1. Market Crisis Response

#### Black Swan Event Protocol
```python
def handle_black_swan_event():
    """Emergency response to extreme market events"""
    
    # Immediate actions
    pause_all_trading()
    close_losing_positions()
    reduce_position_sizes(0.2)  # Reduce to 20% of normal
    
    # Monitor for recovery
    enter_monitoring_mode()
    
    # Gradual re-entry
    if market_stability_restored():
        gradual_position_increase()
```

#### System Failure Protocol
```python
def handle_system_failure():
    """Response to technical system failures"""
    
    # Immediate protective actions
    enable_manual_mode()
    send_emergency_alerts()
    
    # Failsafe mechanisms
    activate_backup_systems()
    enable_position_monitoring()
    
    # Recovery procedures
    run_system_diagnostics()
    verify_data_integrity()
    restart_with_reduced_risk()
```

### 2. Drawdown Recovery Strategies

#### Stepped Recovery Approach
```python
def drawdown_recovery_strategy(current_drawdown):
    """Systematic approach to recovering from drawdowns"""
    
    if current_drawdown < 5.0:
        # Normal operations
        return 1.0  # 100% normal position size
    
    elif current_drawdown < 10.0:
        # Cautious mode
        return 0.7  # 70% position size
        
    elif current_drawdown < 15.0:
        # Conservative mode
        return 0.5  # 50% position size
        
    else:
        # Recovery mode
        return 0.2  # 20% position size
```

## 📈 Performance vs Risk Optimization

### 1. Risk-Adjusted Metrics

#### Sharpe Ratio Optimization
```python
def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate risk-adjusted returns"""
    
    excess_returns = returns - risk_free_rate
    return excess_returns.mean() / returns.std()

# Target: Sharpe Ratio > 1.5
```

#### Sortino Ratio (Downside Risk)
```python
def calculate_sortino_ratio(returns, target_return=0):
    """Focus on downside risk only"""
    
    downside_returns = returns[returns < target_return]
    downside_deviation = downside_returns.std()
    
    return (returns.mean() - target_return) / downside_deviation

# Target: Sortino Ratio > 2.0
```

### 2. Risk Budget Allocation

#### Component Risk Budgets
```json
{
  "risk_allocation": {
    "ml_models": 40,        // 40% of risk budget
    "technical_analysis": 35, // 35% of risk budget
    "gpt4_signals": 25      // 25% of risk budget
  },
  "rebalancing_frequency": "weekly",
  "minimum_allocation": 10  // Minimum 10% per component
}
```

## 🔧 Configuration Examples

### 1. Conservative Setup
```json
{
  "risk_profile": "conservative",
  "max_risk_per_trade": 0.5,
  "max_daily_loss": 50.0,
  "max_drawdown": 8.0,
  "position_sizing": "fixed_fractional",
  "stop_loss_multiplier": 2.0,
  "take_profit_ratio": 3.0,
  "max_positions": 2
}
```

### 2. Balanced Setup  
```json
{
  "risk_profile": "balanced",
  "max_risk_per_trade": 1.5,
  "max_daily_loss": 100.0,
  "max_drawdown": 12.0,
  "position_sizing": "volatility_adjusted",
  "stop_loss_multiplier": 1.8,
  "take_profit_ratio": 2.5,
  "max_positions": 3
}
```

### 3. Aggressive Setup
```json
{
  "risk_profile": "aggressive",
  "max_risk_per_trade": 2.5,
  "max_daily_loss": 200.0,
  "max_drawdown": 18.0,
  "position_sizing": "kelly_criterion",
  "stop_loss_multiplier": 1.5,
  "take_profit_ratio": 2.0,
  "max_positions": 5
}
```

## 🎯 Best Practices

### 1. Daily Risk Management Routine

#### Morning Checklist
- [ ] Review overnight positions
- [ ] Check account equity vs. yesterday
- [ ] Verify risk limits are active
- [ ] Review market volatility conditions
- [ ] Update position sizes if needed

#### Evening Review
- [ ] Calculate daily risk metrics
- [ ] Review trade performance vs. risk taken
- [ ] Update risk parameters if needed
- [ ] Plan tomorrow's risk allocation
- [ ] Backup risk settings

### 2. Weekly Risk Assessment

#### Performance Review
- Analyze risk-adjusted returns
- Review drawdown periods
- Assess position sizing effectiveness
- Evaluate stop loss performance
- Optimize risk parameters

#### System Health Check
- Verify all risk controls functioning
- Test emergency procedures
- Update risk thresholds
- Review correlation analysis
- Backup risk management settings

## ⚠️ Common Risk Management Mistakes

### 1. Avoid These Pitfalls
- **Over-leveraging**: Using too much leverage
- **Position size creep**: Gradually increasing risk
- **Ignoring correlations**: Multiple correlated positions
- **Revenge trading**: Increasing size after losses
- **Neglecting volatility**: Not adjusting for market conditions

### 2. Warning Signs
- Win rate declining consistently
- Average loss exceeding average win
- Drawdowns lasting longer than usual
- Increased emotional decision-making
- Ignoring risk management rules

## 🚨 Emergency Contacts & Procedures

### Immediate Actions for Major Losses
1. **Stop all automated trading**
2. **Review open positions**
3. **Check system integrity**
4. **Implement damage control**
5. **Document the incident**

### Recovery Protocol
1. **Analyze what went wrong**
2. **Adjust risk parameters**
3. **Test on demo account**
4. **Gradual return to live trading**
5. **Monitor closely**

---

## 🎯 Quick Reference

### Essential Risk Metrics
- **Max Risk per Trade**: 1-2% of account
- **Daily Loss Limit**: 2-5% of account  
- **Maximum Drawdown**: 10-15% of account
- **Risk/Reward Ratio**: Minimum 1:2
- **Position Correlation**: Maximum 70%

### Emergency Commands
```bash
# Stop all trading immediately
python core/system_orchestrator_enhanced.py emergency-stop

# Enable manual mode only
python core/system_orchestrator_enhanced.py manual-mode

# Reduce all position sizes
python core/system_orchestrator_enhanced.py reduce-risk 50
```

**Remember**: Risk management is not about avoiding risk—it's about taking calculated risks that preserve capital while allowing for profitable opportunities. Good risk management makes the difference between long-term success and account blow-ups.

*Next: [Configuration Guide](21_Configuration_Guide.md) for system customization.*
