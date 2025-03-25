# Backtesting Guide

This guide explains how to use the backtesting engine in the Quantitative Trading System to evaluate trading strategies.

## Overview

The backtesting engine allows you to:
- Test trading strategies on historical data
- Evaluate performance metrics
- Analyze risk measures
- Optimize strategy parameters
- Generate detailed reports

## Basic Usage

### Setting Up a Backtest

```python
from src.backtesting.engine import BacktestEngine
from src.strategies.moving_average_cross import MovingAverageCross
from src.data.market_data import MarketData
from datetime import datetime

# Initialize market data
market_data = MarketData()
data = market_data.get_historical_data(
    symbols=['AAPL', 'MSFT'],
    start_date='2020-01-01',
    end_date='2023-12-31'
)

# Create strategy instance
strategy = MovingAverageCross(
    short_window=20,
    long_window=50,
    risk_per_trade=0.02
)

# Initialize backtest engine
engine = BacktestEngine(
    strategy=strategy,
    data=data,
    initial_capital=100000,
    transaction_costs=0.001
)

# Run backtest
results = engine.run()
```

### Analyzing Results

```python
# Get performance metrics
metrics = results.get_metrics()
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Total Return: {metrics['total_return']:.2%}")

# Plot equity curve
results.plot_equity_curve()

# Get trade statistics
trade_stats = results.get_trade_statistics()
print(f"Win Rate: {trade_stats['win_rate']:.2%}")
print(f"Avg Winner: ${trade_stats['avg_winner']:.2f}")
print(f"Avg Loser: ${trade_stats['avg_loser']:.2f}")
```

## Advanced Features

### Custom Data Sources

```python
class CustomDataSource:
    def __init__(self):
        self.data = None
    
    def load_data(self, filepath: str) -> pd.DataFrame:
        """
        Load custom data format.
        """
        self.data = pd.read_csv(filepath)
        self.data['datetime'] = pd.to_datetime(self.data['datetime'])
        self.data.set_index('datetime', inplace=True)
        return self.data

# Use custom data in backtest
custom_data = CustomDataSource()
data = custom_data.load_data('path/to/data.csv')
engine = BacktestEngine(strategy=strategy, data=data)
```

### Transaction Costs Model

```python
class CustomTransactionCosts:
    def __init__(self, commission_rate: float, slippage_std: float):
        self.commission_rate = commission_rate
        self.slippage_std = slippage_std
    
    def calculate_costs(self, price: float, size: float) -> float:
        """
        Calculate transaction costs including commission and slippage.
        """
        commission = abs(price * size * self.commission_rate)
        slippage = abs(price * size * np.random.normal(0, self.slippage_std))
        return commission + slippage

# Use custom transaction costs
costs_model = CustomTransactionCosts(commission_rate=0.001, slippage_std=0.0002)
engine = BacktestEngine(
    strategy=strategy,
    data=data,
    transaction_costs_model=costs_model
)
```

### Position Sizing

```python
class CustomPositionSizer:
    def __init__(self, risk_per_trade: float, max_position_size: float):
        self.risk_per_trade = risk_per_trade
        self.max_position_size = max_position_size
    
    def calculate_position_size(self, 
                              capital: float,
                              price: float,
                              volatility: float) -> float:
        """
        Calculate position size based on risk and volatility.
        """
        risk_amount = capital * self.risk_per_trade
        position_size = risk_amount / (price * volatility)
        
        # Apply maximum position size limit
        max_size = capital * self.max_position_size / price
        return min(position_size, max_size)

# Use custom position sizer
position_sizer = CustomPositionSizer(risk_per_trade=0.02, max_position_size=0.1)
strategy.set_position_sizer(position_sizer)
```

## Parameter Optimization

### Grid Search

```python
def optimize_parameters(strategy_class, param_grid: Dict, data: pd.DataFrame):
    """
    Perform grid search optimization.
    """
    best_sharpe = -np.inf
    best_params = None
    
    for params in itertools.product(*param_grid.values()):
        param_dict = dict(zip(param_grid.keys(), params))
        strategy = strategy_class(**param_dict)
        
        engine = BacktestEngine(strategy=strategy, data=data)
        results = engine.run()
        sharpe = results.get_metrics()['sharpe_ratio']
        
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = param_dict
    
    return best_params, best_sharpe

# Example usage
param_grid = {
    'short_window': range(10, 31, 5),
    'long_window': range(40, 81, 10),
    'risk_per_trade': [0.01, 0.02, 0.03]
}

best_params, best_sharpe = optimize_parameters(
    MovingAverageCross,
    param_grid,
    data
)
```

### Walk-Forward Analysis

```python
def walk_forward_analysis(strategy_class, 
                         data: pd.DataFrame,
                         train_size: int,
                         test_size: int,
                         param_grid: Dict):
    """
    Perform walk-forward optimization.
    """
    results = []
    
    for start in range(0, len(data) - train_size - test_size, test_size):
        # Split data into train and test periods
        train_data = data[start:start + train_size]
        test_data = data[start + train_size:start + train_size + test_size]
        
        # Optimize parameters on training data
        best_params, _ = optimize_parameters(
            strategy_class,
            param_grid,
            train_data
        )
        
        # Test optimized strategy
        strategy = strategy_class(**best_params)
        engine = BacktestEngine(strategy=strategy, data=test_data)
        test_results = engine.run()
        
        results.append({
            'period': f"{test_data.index[0]} to {test_data.index[-1]}",
            'parameters': best_params,
            'sharpe_ratio': test_results.get_metrics()['sharpe_ratio']
        })
    
    return pd.DataFrame(results)
```

## Performance Analysis

### Risk Metrics

```python
def calculate_risk_metrics(results):
    """
    Calculate comprehensive risk metrics.
    """
    returns = results.get_returns()
    
    metrics = {
        'sharpe_ratio': results.get_metrics()['sharpe_ratio'],
        'sortino_ratio': calculate_sortino_ratio(returns),
        'max_drawdown': calculate_max_drawdown(returns),
        'var_95': calculate_var(returns, 0.95),
        'expected_shortfall': calculate_expected_shortfall(returns),
        'skewness': returns.skew(),
        'kurtosis': returns.kurtosis(),
        'annualized_volatility': calculate_annualized_volatility(returns)
    }
    
    return metrics
```

### Trade Analysis

```python
def analyze_trades(results):
    """
    Analyze trading performance.
    """
    trades = results.get_trades()
    
    analysis = {
        'total_trades': len(trades),
        'winning_trades': len(trades[trades['pnl'] > 0]),
        'losing_trades': len(trades[trades['pnl'] < 0]),
        'win_rate': len(trades[trades['pnl'] > 0]) / len(trades),
        'avg_winner': trades[trades['pnl'] > 0]['pnl'].mean(),
        'avg_loser': trades[trades['pnl'] < 0]['pnl'].mean(),
        'profit_factor': abs(trades[trades['pnl'] > 0]['pnl'].sum() / 
                           trades[trades['pnl'] < 0]['pnl'].sum()),
        'avg_holding_period': trades['holding_period'].mean()
    }
    
    return analysis
```

## Best Practices

1. Data Preparation
   - Clean and validate historical data
   - Handle missing values appropriately
   - Ensure proper datetime indexing
   - Split data into training and testing periods

2. Strategy Development
   - Start with simple strategies
   - Add complexity gradually
   - Test edge cases
   - Implement proper risk management

3. Performance Evaluation
   - Use multiple metrics
   - Consider transaction costs
   - Account for slippage
   - Test across different market conditions

4. Optimization
   - Avoid overfitting
   - Use walk-forward analysis
   - Consider parameter stability
   - Test robustness

5. Documentation
   - Document assumptions
   - Record parameter choices
   - Keep track of changes
   - Maintain test results 