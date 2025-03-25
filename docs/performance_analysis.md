# Performance Analysis Guide

This guide explains how to analyze trading performance and generate comprehensive reports in the Quantitative Trading System.

## Performance Metrics

### Return Metrics

1. Basic Return Calculations
```python
def calculate_returns(portfolio_values: pd.Series) -> Dict[str, float]:
    """
    Calculate basic return metrics.
    """
    returns = portfolio_values.pct_change()
    
    metrics = {
        'total_return': (portfolio_values[-1] / portfolio_values[0]) - 1,
        'annualized_return': calculate_annualized_return(returns),
        'monthly_returns': calculate_monthly_returns(returns),
        'yearly_returns': calculate_yearly_returns(returns)
    }
    
    return metrics

def calculate_annualized_return(returns: pd.Series) -> float:
    """
    Calculate annualized return.
    """
    total_days = len(returns)
    total_return = (1 + returns).prod() - 1
    annualized_return = (1 + total_return) ** (252 / total_days) - 1
    return annualized_return
```

2. Risk-Adjusted Returns
```python
def calculate_risk_adjusted_returns(returns: pd.Series) -> Dict[str, float]:
    """
    Calculate risk-adjusted return metrics.
    """
    metrics = {
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'sortino_ratio': calculate_sortino_ratio(returns),
        'information_ratio': calculate_information_ratio(returns),
        'treynor_ratio': calculate_treynor_ratio(returns)
    }
    
    return metrics

def calculate_sharpe_ratio(returns: pd.Series,
                          risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio.
    """
    excess_returns = returns - risk_free_rate/252
    return np.sqrt(252) * excess_returns.mean() / returns.std()

def calculate_sortino_ratio(returns: pd.Series,
                          risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sortino ratio.
    """
    excess_returns = returns - risk_free_rate/252
    downside_returns = returns[returns < 0]
    downside_std = np.sqrt(np.mean(downside_returns**2))
    return np.sqrt(252) * excess_returns.mean() / downside_std
```

### Risk Metrics

1. Volatility Metrics
```python
def calculate_volatility_metrics(returns: pd.Series) -> Dict[str, float]:
    """
    Calculate volatility-based risk metrics.
    """
    metrics = {
        'volatility': returns.std() * np.sqrt(252),
        'downside_volatility': calculate_downside_volatility(returns),
        'upside_volatility': calculate_upside_volatility(returns),
        'volatility_skew': calculate_volatility_skew(returns)
    }
    
    return metrics

def calculate_downside_volatility(returns: pd.Series) -> float:
    """
    Calculate downside volatility.
    """
    downside_returns = returns[returns < 0]
    return np.sqrt(np.mean(downside_returns**2)) * np.sqrt(252)
```

2. Drawdown Analysis
```python
def analyze_drawdowns(portfolio_values: pd.Series) -> Dict[str, float]:
    """
    Analyze drawdowns in the portfolio.
    """
    drawdown = calculate_drawdown_series(portfolio_values)
    
    metrics = {
        'max_drawdown': drawdown.min(),
        'avg_drawdown': drawdown[drawdown < 0].mean(),
        'drawdown_duration': calculate_avg_drawdown_duration(drawdown),
        'time_to_recovery': calculate_time_to_recovery(drawdown)
    }
    
    return metrics

def calculate_drawdown_series(portfolio_values: pd.Series) -> pd.Series:
    """
    Calculate drawdown series.
    """
    rolling_max = portfolio_values.expanding().max()
    drawdown = portfolio_values / rolling_max - 1
    return drawdown
```

## Trade Analysis

### Trade Statistics

1. Basic Trade Metrics
```python
def analyze_trades(trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze trading performance statistics.
    """
    metrics = {
        'total_trades': len(trades),
        'winning_trades': len(trades[trades['pnl'] > 0]),
        'losing_trades': len(trades[trades['pnl'] < 0]),
        'win_rate': len(trades[trades['pnl'] > 0]) / len(trades),
        'avg_winner': trades[trades['pnl'] > 0]['pnl'].mean(),
        'avg_loser': trades[trades['pnl'] < 0]['pnl'].mean(),
        'largest_winner': trades['pnl'].max(),
        'largest_loser': trades['pnl'].min(),
        'avg_holding_period': trades['holding_period'].mean()
    }
    
    return metrics
```

2. Advanced Trade Analysis
```python
def analyze_trade_patterns(trades: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze trading patterns and behaviors.
    """
    analysis = {
        'time_analysis': analyze_trade_timing(trades),
        'size_analysis': analyze_position_sizing(trades),
        'market_analysis': analyze_market_conditions(trades),
        'consecutive_trades': analyze_consecutive_trades(trades)
    }
    
    return analysis

def analyze_trade_timing(trades: pd.DataFrame) -> Dict[str, float]:
    """
    Analyze trade timing patterns.
    """
    trades['hour'] = trades.index.hour
    trades['day_of_week'] = trades.index.dayofweek
    
    timing = {
        'best_hour': trades.groupby('hour')['pnl'].mean().idxmax(),
        'worst_hour': trades.groupby('hour')['pnl'].mean().idxmin(),
        'best_day': trades.groupby('day_of_week')['pnl'].mean().idxmax(),
        'worst_day': trades.groupby('day_of_week')['pnl'].mean().idxmin()
    }
    
    return timing
```

## Portfolio Analysis

### Position Analysis

1. Portfolio Composition
```python
def analyze_portfolio_composition(positions: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze portfolio composition and exposure.
    """
    analysis = {
        'sector_exposure': calculate_sector_exposure(positions),
        'asset_concentration': calculate_asset_concentration(positions),
        'market_cap_exposure': calculate_market_cap_exposure(positions),
        'factor_exposure': calculate_factor_exposure(positions)
    }
    
    return analysis

def calculate_sector_exposure(positions: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate sector exposures.
    """
    sector_exposure = positions.groupby('sector')['exposure'].sum()
    return sector_exposure.to_dict()
```

2. Risk Decomposition
```python
def decompose_portfolio_risk(positions: pd.DataFrame,
                           returns: pd.DataFrame) -> Dict[str, float]:
    """
    Decompose portfolio risk into factor contributions.
    """
    # Calculate factor exposures
    factor_exposures = calculate_factor_exposures(positions)
    
    # Calculate factor returns
    factor_returns = calculate_factor_returns(returns)
    
    # Calculate risk contributions
    risk_contrib = calculate_risk_contributions(
        factor_exposures,
        factor_returns
    )
    
    return risk_contrib
```

## Performance Attribution

### Factor Attribution

1. Returns Attribution
```python
def attribute_returns(returns: pd.Series,
                     factors: pd.DataFrame) -> Dict[str, float]:
    """
    Attribute returns to different factors.
    """
    # Perform returns regression
    model = LinearRegression()
    model.fit(factors, returns)
    
    # Calculate attribution
    attribution = {
        'alpha': model.intercept_ * 252,  # Annualized alpha
        'factor_contribution': dict(zip(
            factors.columns,
            model.coef_ * factors.mean() * 252
        ))
    }
    
    return attribution
```

2. Risk Attribution
```python
def attribute_risk(positions: pd.DataFrame,
                  risk_model: RiskModel) -> Dict[str, float]:
    """
    Attribute portfolio risk to different sources.
    """
    # Calculate factor exposures
    exposures = risk_model.calculate_exposures(positions)
    
    # Calculate risk contributions
    contributions = risk_model.decompose_risk(
        exposures,
        positions['weight']
    )
    
    return contributions
```

## Performance Reporting

### Report Generation

1. Performance Report
```python
def generate_performance_report(portfolio: Portfolio,
                              start_date: str,
                              end_date: str) -> Dict[str, Any]:
    """
    Generate comprehensive performance report.
    """
    report = {
        'summary': generate_summary_metrics(portfolio),
        'returns_analysis': analyze_returns(portfolio),
        'risk_analysis': analyze_risk(portfolio),
        'trade_analysis': analyze_trades(portfolio),
        'portfolio_analysis': analyze_portfolio(portfolio),
        'attribution': perform_attribution(portfolio)
    }
    
    return report

def generate_summary_metrics(portfolio: Portfolio) -> Dict[str, float]:
    """
    Generate summary performance metrics.
    """
    summary = {
        'total_return': portfolio.calculate_total_return(),
        'sharpe_ratio': portfolio.calculate_sharpe_ratio(),
        'max_drawdown': portfolio.calculate_max_drawdown(),
        'win_rate': portfolio.calculate_win_rate(),
        'profit_factor': portfolio.calculate_profit_factor()
    }
    
    return summary
```

2. Risk Report
```python
def generate_risk_report(portfolio: Portfolio) -> Dict[str, Any]:
    """
    Generate comprehensive risk report.
    """
    report = {
        'market_risk': analyze_market_risk(portfolio),
        'liquidity_risk': analyze_liquidity_risk(portfolio),
        'factor_risk': analyze_factor_risk(portfolio),
        'stress_tests': perform_stress_tests(portfolio),
        'scenario_analysis': perform_scenario_analysis(portfolio)
    }
    
    return report
```

## Visualization

### Performance Charts

1. Returns Visualization
```python
def plot_performance_charts(portfolio: Portfolio) -> None:
    """
    Create performance visualization charts.
    """
    # Plot cumulative returns
    plot_cumulative_returns(portfolio.returns)
    
    # Plot drawdown chart
    plot_drawdown_chart(portfolio.drawdown)
    
    # Plot monthly returns heatmap
    plot_monthly_returns_heatmap(portfolio.monthly_returns)
    
    # Plot rolling metrics
    plot_rolling_metrics(portfolio)

def plot_rolling_metrics(portfolio: Portfolio) -> None:
    """
    Plot rolling performance metrics.
    """
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Rolling Sharpe ratio
    portfolio.plot_rolling_sharpe(ax=axes[0, 0])
    
    # Rolling volatility
    portfolio.plot_rolling_volatility(ax=axes[0, 1])
    
    # Rolling beta
    portfolio.plot_rolling_beta(ax=axes[1, 0])
    
    # Rolling correlation
    portfolio.plot_rolling_correlation(ax=axes[1, 1])
```

2. Risk Visualization
```python
def plot_risk_charts(portfolio: Portfolio) -> None:
    """
    Create risk visualization charts.
    """
    # Plot risk decomposition
    plot_risk_decomposition(portfolio.risk_decomposition)
    
    # Plot factor exposures
    plot_factor_exposures(portfolio.factor_exposures)
    
    # Plot stress test results
    plot_stress_test_results(portfolio.stress_tests)
    
    # Plot risk contributions
    plot_risk_contributions(portfolio.risk_contributions)
```

## Best Practices

1. Performance Measurement
   - Use appropriate benchmarks
   - Consider risk-adjusted metrics
   - Account for transaction costs
   - Analyze multiple timeframes

2. Risk Assessment
   - Monitor risk limits
   - Perform stress tests
   - Analyze factor exposures
   - Track correlation changes

3. Attribution Analysis
   - Decompose returns properly
   - Consider multiple factors
   - Track attribution changes
   - Validate attribution results

4. Reporting
   - Maintain consistency
   - Include relevant metrics
   - Provide clear visualizations
   - Document assumptions

5. Review Process
   - Regular performance reviews
   - Document insights
   - Update strategies
   - Track improvements 