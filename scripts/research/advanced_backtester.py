#!/usr/bin/env python3
"""
AI Gold Scalper - Advanced Backtesting Engine
Comprehensive backtesting framework for strategy evaluation and optimization.

Features:
- Multi-strategy backtesting
- Advanced performance metrics
- Risk-adjusted returns
- Transaction cost modeling
- Monte Carlo analysis
- Strategy optimization
- Portfolio backtesting
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import warnings
warnings.filterwarnings('ignore')

# Analysis imports
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns

# Import our strategy generator
from strategy_generator import StrategyGenerator

class AdvancedBacktester:
    """Advanced backtesting engine with comprehensive analytics"""
    
    def __init__(self, initial_capital: float = 10000, commission: float = 0.001):
        self.initial_capital = initial_capital
        self.commission = commission  # 0.1% per trade
        self.spread = 0.0005  # 0.05% spread
        
        # Results storage
        self.backtest_results = {}
        self.portfolio_results = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("Advanced Backtester initialized")
    
    def run_single_strategy_backtest(self, df: pd.DataFrame, signals: pd.Series, 
                                   strategy_name: str, **kwargs) -> Dict[str, Any]:
        """Run backtest for a single strategy"""
        try:
            # Initialize tracking variables
            capital = self.initial_capital
            position = 0  # 0 = no position, 1 = long, -1 = short
            entry_price = 0
            trades = []
            equity_curve = []
            
            # Risk management parameters
            stop_loss_pct = kwargs.get('stop_loss', 0.02)  # 2% stop loss
            take_profit_pct = kwargs.get('take_profit', 0.04)  # 4% take profit
            max_position_size = kwargs.get('max_position_size', 1.0)  # 100% of capital
            
            for i, (timestamp, signal) in enumerate(signals.items()):
                if i >= len(df.index):
                    break
                    
                current_price = df.loc[timestamp, 'close']
                
                # Apply spread (bid-ask spread simulation)
                buy_price = current_price * (1 + self.spread)
                sell_price = current_price * (1 - self.spread)
                
                # Check for stop loss or take profit if in position
                if position != 0:
                    if position == 1:  # Long position
                        # Stop loss check
                        if current_price <= entry_price * (1 - stop_loss_pct):
                            # Exit with stop loss
                            trade_return = (sell_price - entry_price) / entry_price
                            capital *= (1 + trade_return - self.commission)
                            
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': timestamp,
                                'entry_price': entry_price,
                                'exit_price': sell_price,
                                'position': position,
                                'return': trade_return,
                                'exit_reason': 'stop_loss'
                            })
                            position = 0
                        
                        # Take profit check
                        elif current_price >= entry_price * (1 + take_profit_pct):
                            # Exit with take profit
                            trade_return = (sell_price - entry_price) / entry_price
                            capital *= (1 + trade_return - self.commission)
                            
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': timestamp,
                                'entry_price': entry_price,
                                'exit_price': sell_price,
                                'position': position,
                                'return': trade_return,
                                'exit_reason': 'take_profit'
                            })
                            position = 0
                    
                    elif position == -1:  # Short position
                        # Stop loss check (price going up)
                        if current_price >= entry_price * (1 + stop_loss_pct):
                            # Exit with stop loss
                            trade_return = (entry_price - buy_price) / entry_price
                            capital *= (1 + trade_return - self.commission)
                            
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': timestamp,
                                'entry_price': entry_price,
                                'exit_price': buy_price,
                                'position': position,
                                'return': trade_return,
                                'exit_reason': 'stop_loss'
                            })
                            position = 0
                        
                        # Take profit check (price going down)
                        elif current_price <= entry_price * (1 - take_profit_pct):
                            # Exit with take profit
                            trade_return = (entry_price - buy_price) / entry_price
                            capital *= (1 + trade_return - self.commission)
                            
                            trades.append({
                                'entry_time': entry_time,
                                'exit_time': timestamp,
                                'entry_price': entry_price,
                                'exit_price': buy_price,
                                'position': position,
                                'return': trade_return,
                                'exit_reason': 'take_profit'
                            })
                            position = 0
                
                # Process signal
                if signal == 1 and position <= 0:  # Buy signal
                    # Close short position if exists
                    if position == -1:
                        trade_return = (entry_price - buy_price) / entry_price
                        capital *= (1 + trade_return - self.commission)
                        
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'entry_price': entry_price,
                            'exit_price': buy_price,
                            'position': position,
                            'return': trade_return,
                            'exit_reason': 'signal_reversal'
                        })
                    
                    # Open long position
                    position = 1
                    entry_price = buy_price
                    entry_time = timestamp
                
                elif signal == -1 and position >= 0:  # Sell signal
                    # Close long position if exists
                    if position == 1:
                        trade_return = (sell_price - entry_price) / entry_price
                        capital *= (1 + trade_return - self.commission)
                        
                        trades.append({
                            'entry_time': entry_time,
                            'exit_time': timestamp,
                            'entry_price': entry_price,
                            'exit_price': sell_price,
                            'position': position,
                            'return': trade_return,
                            'exit_reason': 'signal_reversal'
                        })
                    
                    # Open short position
                    position = -1
                    entry_price = sell_price
                    entry_time = timestamp
                
                # Track equity curve
                if position == 1:
                    unrealized_return = (current_price - entry_price) / entry_price
                    current_equity = capital * (1 + unrealized_return)
                elif position == -1:
                    unrealized_return = (entry_price - current_price) / entry_price
                    current_equity = capital * (1 + unrealized_return)
                else:
                    current_equity = capital
                
                equity_curve.append({
                    'timestamp': timestamp,
                    'equity': current_equity,
                    'position': position,
                    'price': current_price
                })
            
            # Close any remaining position
            if position != 0:
                final_price = df.iloc[-1]['close']
                if position == 1:
                    trade_return = (final_price * (1 - self.spread) - entry_price) / entry_price
                else:
                    trade_return = (entry_price - final_price * (1 + self.spread)) / entry_price
                
                capital *= (1 + trade_return - self.commission)
                
                trades.append({
                    'entry_time': entry_time,
                    'exit_time': df.index[-1],
                    'entry_price': entry_price,
                    'exit_price': final_price,
                    'position': position,
                    'return': trade_return,
                    'exit_reason': 'end_of_data'
                })
            
            # Calculate performance metrics
            performance = self.calculate_performance_metrics(trades, equity_curve, df)
            
            result = {
                'strategy_name': strategy_name,
                'trades': trades,
                'equity_curve': equity_curve,
                'performance': performance,
                'final_capital': capital,
                'total_return': (capital - self.initial_capital) / self.initial_capital
            }
            
            self.backtest_results[strategy_name] = result
            return result
            
        except Exception as e:
            self.logger.error(f"Error backtesting {strategy_name}: {e}")
            return {}
    
    def calculate_performance_metrics(self, trades: List[Dict], equity_curve: List[Dict], 
                                    price_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate comprehensive performance metrics"""
        if not trades:
            return {'error': 'No trades executed'}
        
        # Convert to DataFrames
        trades_df = pd.DataFrame(trades)
        equity_df = pd.DataFrame(equity_curve)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len(trades_df[trades_df['return'] > 0])
        losing_trades = len(trades_df[trades_df['return'] < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Return metrics
        total_return = (equity_df.iloc[-1]['equity'] - self.initial_capital) / self.initial_capital
        
        # Risk metrics
        returns = trades_df['return'].values
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        # Sharpe ratio (assuming risk-free rate of 2%)
        risk_free_rate = 0.02 / 252  # Daily risk-free rate
        sharpe_ratio = (avg_return - risk_free_rate) / std_return if std_return > 0 else 0
        
        # Maximum drawdown
        equity_values = [eq['equity'] for eq in equity_curve]
        peak = np.maximum.accumulate(equity_values)
        drawdown = (peak - equity_values) / peak
        max_drawdown = np.max(drawdown) * 100
        
        # Profit factor
        gross_profit = trades_df[trades_df['return'] > 0]['return'].sum()
        gross_loss = abs(trades_df[trades_df['return'] < 0]['return'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average trade metrics
        avg_win = trades_df[trades_df['return'] > 0]['return'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['return'] < 0]['return'].mean() if losing_trades > 0 else 0
        
        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)
        
        # Calmar ratio (return / max drawdown)
        calmar_ratio = (total_return * 100) / max_drawdown if max_drawdown > 0 else 0
        
        # Sortino ratio (downside deviation)
        negative_returns = returns[returns < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 0
        sortino_ratio = (avg_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        # Recovery factor
        recovery_factor = total_return / (max_drawdown / 100) if max_drawdown > 0 else 0
        
        # Trade duration analysis
        trade_durations = []
        for trade in trades:
            duration = (trade['exit_time'] - trade['entry_time']).total_seconds() / 3600  # Hours
            trade_durations.append(duration)
        
        avg_trade_duration = np.mean(trade_durations) if trade_durations else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return_pct': total_return * 100,
            'avg_return_per_trade': avg_return * 100,
            'std_return': std_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown,
            'profit_factor': profit_factor,
            'avg_win_pct': avg_win * 100,
            'avg_loss_pct': avg_loss * 100,
            'expectancy': expectancy * 100,
            'calmar_ratio': calmar_ratio,
            'sortino_ratio': sortino_ratio,
            'recovery_factor': recovery_factor,
            'avg_trade_duration_hours': avg_trade_duration
        }
    
    def run_strategy_comparison(self, strategies: Dict[str, Any], df: pd.DataFrame) -> pd.DataFrame:
        """Run backtests for multiple strategies and compare results"""
        self.logger.info(f"Running comparison backtest for {len(strategies)} strategies...")
        
        comparison_results = []
        
        for strategy_name, strategy_data in strategies.items():
            if 'signals' not in strategy_data:
                continue
                
            self.logger.info(f"Backtesting: {strategy_name}")
            
            result = self.run_single_strategy_backtest(
                df, strategy_data['signals'], strategy_name
            )
            
            if result and 'performance' in result:
                perf = result['performance']
                comparison_results.append({
                    'strategy': strategy_name,
                    'type': strategy_data.get('type', 'unknown'),
                    'total_return_pct': perf.get('total_return_pct', 0),
                    'win_rate': perf.get('win_rate', 0),
                    'sharpe_ratio': perf.get('sharpe_ratio', 0),
                    'max_drawdown_pct': perf.get('max_drawdown_pct', 0),
                    'profit_factor': perf.get('profit_factor', 0),
                    'total_trades': perf.get('total_trades', 0),
                    'calmar_ratio': perf.get('calmar_ratio', 0),
                    'sortino_ratio': perf.get('sortino_ratio', 0),
                    'expectancy': perf.get('expectancy', 0)
                })
        
        comparison_df = pd.DataFrame(comparison_results)
        
        # Rank strategies
        if not comparison_df.empty:
            # Create composite score
            comparison_df['composite_score'] = (
                comparison_df['total_return_pct'] * 0.3 +
                comparison_df['sharpe_ratio'] * 20 * 0.25 +
                comparison_df['win_rate'] * 0.2 +
                comparison_df['calmar_ratio'] * 0.15 +
                comparison_df['expectancy'] * 0.1
            )
            
            comparison_df = comparison_df.sort_values('composite_score', ascending=False)
        
        return comparison_df
    
    def optimize_strategy_parameters(self, strategy_func, df: pd.DataFrame, 
                                   param_ranges: Dict[str, List]) -> Dict[str, Any]:
        """Optimize strategy parameters using grid search"""
        self.logger.info("Starting parameter optimization...")
        
        best_result = None
        best_params = None
        best_score = -float('inf')
        
        # Generate parameter combinations
        import itertools
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        optimization_results = []
        
        for param_combo in itertools.product(*param_values):
            params = dict(zip(param_names, param_combo))
            
            try:
                # Generate signals with these parameters
                signals = strategy_func(df, **params)
                
                # Run backtest
                result = self.run_single_strategy_backtest(
                    df, signals, f"optimized_{hash(str(params))}"
                )
                
                if result and 'performance' in result:
                    perf = result['performance']
                    
                    # Calculate optimization score (you can customize this)
                    score = (
                        perf.get('total_return_pct', 0) * 0.4 +
                        perf.get('sharpe_ratio', 0) * 20 * 0.3 +
                        perf.get('calmar_ratio', 0) * 0.3
                    )
                    
                    optimization_results.append({
                        'params': params,
                        'score': score,
                        'performance': perf
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_params = params
                        best_result = result
                        
            except Exception as e:
                self.logger.warning(f"Error optimizing params {params}: {e}")
                continue
        
        return {
            'best_params': best_params,
            'best_score': best_score,
            'best_result': best_result,
            'all_results': optimization_results
        }
    
    def monte_carlo_analysis(self, trades: List[Dict], num_simulations: int = 1000) -> Dict[str, Any]:
        """Perform Monte Carlo analysis on trade results"""
        if not trades:
            return {'error': 'No trades for Monte Carlo analysis'}
        
        returns = [trade['return'] for trade in trades]
        
        # Bootstrap sampling
        simulated_equity_curves = []
        
        for _ in range(num_simulations):
            # Randomly sample returns with replacement
            sampled_returns = np.random.choice(returns, len(returns), replace=True)
            
            # Calculate equity curve
            equity = self.initial_capital
            equity_curve = [equity]
            
            for ret in sampled_returns:
                equity *= (1 + ret - self.commission)
                equity_curve.append(equity)
            
            simulated_equity_curves.append(equity_curve)
        
        # Analyze results
        final_values = [curve[-1] for curve in simulated_equity_curves]
        
        return {
            'mean_final_value': np.mean(final_values),
            'std_final_value': np.std(final_values),
            'percentile_5': np.percentile(final_values, 5),
            'percentile_95': np.percentile(final_values, 95),
            'prob_profit': sum(1 for val in final_values if val > self.initial_capital) / num_simulations,
            'expected_return': (np.mean(final_values) - self.initial_capital) / self.initial_capital
        }
    
    def create_portfolio_backtest(self, strategies: Dict[str, Any], df: pd.DataFrame, 
                                 weights: Dict[str, float] = None) -> Dict[str, Any]:
        """Create a portfolio of strategies and backtest"""
        if not weights:
            # Equal weight portfolio
            weights = {name: 1.0 / len(strategies) for name in strategies.keys()}
        
        self.logger.info(f"Running portfolio backtest with {len(strategies)} strategies")
        
        # Run individual backtests
        individual_results = {}
        for name, strategy in strategies.items():
            if 'signals' in strategy:
                result = self.run_single_strategy_backtest(df, strategy['signals'], name)
                individual_results[name] = result
        
        # Combine signals using weights
        combined_signals = pd.Series(0.0, index=df.index)
        
        for name, weight in weights.items():
            if name in strategies and 'signals' in strategies[name]:
                strategy_signals = strategies[name]['signals']
                # Normalize signals to -1, 0, 1 and apply weight
                normalized_signals = strategy_signals.clip(-1, 1) * weight
                combined_signals += normalized_signals
        
        # Threshold combined signals
        portfolio_signals = pd.Series(0, index=combined_signals.index)
        portfolio_signals[combined_signals > 0.3] = 1
        portfolio_signals[combined_signals < -0.3] = -1
        
        # Run portfolio backtest
        portfolio_result = self.run_single_strategy_backtest(
            df, portfolio_signals, "Portfolio"
        )
        
        return {
            'portfolio_result': portfolio_result,
            'individual_results': individual_results,
            'weights': weights,
            'combined_signals': combined_signals
        }
    
    def generate_report(self, strategy_name: str, save_plots: bool = True) -> str:
        """Generate comprehensive backtest report"""
        if strategy_name not in self.backtest_results:
            return f"No results found for strategy: {strategy_name}"
        
        result = self.backtest_results[strategy_name]
        perf = result['performance']
        
        # Create report
        report = f"""
===============================================
BACKTEST REPORT: {strategy_name}
===============================================

PERFORMANCE SUMMARY:
- Total Return: {perf.get('total_return_pct', 0):.2f}%
- Win Rate: {perf.get('win_rate', 0):.1f}%
- Total Trades: {perf.get('total_trades', 0)}
- Profit Factor: {perf.get('profit_factor', 0):.2f}

RISK METRICS:
- Sharpe Ratio: {perf.get('sharpe_ratio', 0):.3f}
- Sortino Ratio: {perf.get('sortino_ratio', 0):.3f}
- Max Drawdown: {perf.get('max_drawdown_pct', 0):.2f}%
- Calmar Ratio: {perf.get('calmar_ratio', 0):.2f}

TRADE ANALYSIS:
- Average Win: {perf.get('avg_win_pct', 0):.2f}%
- Average Loss: {perf.get('avg_loss_pct', 0):.2f}%
- Expectancy: {perf.get('expectancy', 0):.2f}%
- Avg Trade Duration: {perf.get('avg_trade_duration_hours', 0):.1f} hours

CAPITAL PROGRESSION:
- Initial Capital: ${self.initial_capital:,.2f}
- Final Capital: ${result.get('final_capital', 0):,.2f}
- Total P&L: ${result.get('final_capital', 0) - self.initial_capital:,.2f}
"""
        
        if save_plots:
            self.create_performance_plots(strategy_name)
        
        return report
    
    def create_performance_plots(self, strategy_name: str):
        """Create performance visualization plots"""
        if strategy_name not in self.backtest_results:
            return
        
        result = self.backtest_results[strategy_name]
        equity_curve = pd.DataFrame(result['equity_curve'])
        trades_df = pd.DataFrame(result['trades'])
        
        # Create plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle(f'Performance Analysis: {strategy_name}', fontsize=16)
        
        # Equity curve
        axes[0, 0].plot(equity_curve['timestamp'], equity_curve['equity'])
        axes[0, 0].set_title('Equity Curve')
        axes[0, 0].set_ylabel('Portfolio Value ($)')
        axes[0, 0].grid(True)
        
        # Returns distribution
        if not trades_df.empty:
            axes[0, 1].hist(trades_df['return'] * 100, bins=30, alpha=0.7, edgecolor='black')
            axes[0, 1].set_title('Trade Returns Distribution')
            axes[0, 1].set_xlabel('Return (%)')
            axes[0, 1].set_ylabel('Frequency')
            axes[0, 1].grid(True)
        
        # Drawdown
        equity_values = equity_curve['equity'].values
        peak = np.maximum.accumulate(equity_values)
        drawdown = (peak - equity_values) / peak * 100
        axes[1, 0].fill_between(equity_curve['timestamp'], drawdown, 0, alpha=0.3, color='red')
        axes[1, 0].set_title('Drawdown')
        axes[1, 0].set_ylabel('Drawdown (%)')
        axes[1, 0].grid(True)
        
        # Monthly returns heatmap (if enough data)
        if len(equity_curve) > 30:
            equity_curve['month'] = equity_curve['timestamp'].dt.to_period('M')
            monthly_returns = equity_curve.groupby('month')['equity'].last().pct_change().dropna()
            
            if len(monthly_returns) > 0:
                # Simple bar chart of monthly returns
                axes[1, 1].bar(range(len(monthly_returns)), monthly_returns * 100)
                axes[1, 1].set_title('Monthly Returns')
                axes[1, 1].set_ylabel('Return (%)')
                axes[1, 1].grid(True)
        
        plt.tight_layout()
        
        # Save plot
        plots_dir = Path("results/plots")
        plots_dir.mkdir(parents=True, exist_ok=True)
        plt.savefig(plots_dir / f"{strategy_name}_performance.png", dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self, filename: str = None):
        """Save backtest results to file"""
        if not filename:
            filename = f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path("results") / filename
        filepath.parent.mkdir(exist_ok=True)
        
        # Prepare serializable results
        serializable_results = {}
        for name, result in self.backtest_results.items():
            serializable_results[name] = {
                'strategy_name': result['strategy_name'],
                'performance': result['performance'],
                'final_capital': result['final_capital'],
                'total_return': result['total_return'],
                'trade_count': len(result['trades'])
            }
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        self.logger.info(f"Results saved to {filepath}")

def main():
    """Main execution function for backtesting"""
    print("🧪 AI Gold Scalper - Advanced Backtester")
    print("=" * 50)
    
    # Initialize components
    strategy_generator = StrategyGenerator()
    backtester = AdvancedBacktester(initial_capital=10000)
    
    # Generate strategies
    print("\n📊 Generating strategies...")
    strategies = strategy_generator.generate_all_strategies("1h")
    
    if not strategies:
        print("❌ No strategies generated")
        return
    
    # Load data
    df = strategy_generator.load_data("1h")
    if df.empty:
        print("❌ No data loaded")
        return
    
    df = strategy_generator.add_technical_indicators(df)
    
    # Run strategy comparison
    print(f"\n🔬 Running backtests for {len(strategies)} strategies...")
    comparison_results = backtester.run_strategy_comparison(strategies, df)
    
    if comparison_results.empty:
        print("❌ No backtest results")
        return
    
    # Display top strategies
    print("\n🏆 TOP 10 STRATEGIES:")
    print("=" * 80)
    top_strategies = comparison_results.head(10)
    
    for idx, row in top_strategies.iterrows():
        print(f"{idx+1:2d}. {row['strategy']:<25} | "
              f"Return: {row['total_return_pct']:6.2f}% | "
              f"Sharpe: {row['sharpe_ratio']:5.2f} | "
              f"Win Rate: {row['win_rate']:5.1f}% | "
              f"Trades: {row['total_trades']:3d}")
    
    # Generate detailed reports for top 3 strategies
    print("\n📝 Generating detailed reports for top 3 strategies...")
    for i in range(min(3, len(top_strategies))):
        strategy_name = top_strategies.iloc[i]['strategy']
        report = backtester.generate_report(strategy_name)
        print(f"\n{report}")
    
    # Save results
    backtester.save_results()
    
    # Portfolio analysis
    if len(strategies) >= 3:
        print("\n💼 Creating diversified portfolio...")
        top_3_strategies = {name: strategies[name] for name in top_strategies.head(3)['strategy']}
        portfolio_result = backtester.create_portfolio_backtest(top_3_strategies, df)
        
        if portfolio_result and 'portfolio_result' in portfolio_result:
            portfolio_perf = portfolio_result['portfolio_result']['performance']
            print(f"Portfolio Performance:")
            print(f"  • Total Return: {portfolio_perf.get('total_return_pct', 0):.2f}%")
            print(f"  • Sharpe Ratio: {portfolio_perf.get('sharpe_ratio', 0):.3f}")
            print(f"  • Max Drawdown: {portfolio_perf.get('max_drawdown_pct', 0):.2f}%")
    
    print("\n🎉 Backtesting completed!")
    print("💡 Next steps for LOCAL MACHINE:")
    print("   1. Review top performing strategies")
    print("   2. Optimize parameters for best strategies")
    print("   3. Run Monte Carlo analysis")
    print("   4. Deploy selected strategies to VPS")

if __name__ == "__main__":
    main()
