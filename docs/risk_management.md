# Risk Management Guide

This guide outlines the risk management framework and best practices implemented in the Quantitative Trading System.

## Risk Management Framework

### Core Components
1. Position Sizing
2. Portfolio Risk
3. Stop Loss Management
4. Exposure Limits
5. Correlation Analysis

## Position Sizing

### Position Size Calculation
```python
def calculate_position_size(self, signal: float, price: float, volatility: float) -> float:
    """
    Calculate position size based on volatility and risk parameters.
    
    Args:
        signal: Signal strength (-1.0 to 1.0)
        price: Current asset price
        volatility: Asset volatility (standard deviation of returns)
    """
    # Calculate risk-adjusted position size
    risk_budget = self.capital * self.max_risk_per_trade
    position_size = risk_budget / (price * volatility)
    
    # Apply signal strength
    position_size *= abs(signal)
    
    # Apply direction
    return position_size if signal > 0 else -position_size
```

### Position Limits
```python
def apply_position_limits(self, position: float, price: float) -> float:
    """
    Apply position size limits.
    """
    # Maximum position size as percentage of capital
    max_position_value = self.capital * self.max_position_size
    position_value = abs(position * price)
    
    if position_value > max_position_value:
        position *= max_position_value / position_value
    
    return position
```

## Portfolio Risk Management

### Value at Risk (VaR)
```python
def calculate_var(self, positions: Dict[str, float], confidence: float = 0.95) -> float:
    """
    Calculate portfolio Value at Risk.
    """
    # Calculate portfolio returns
    portfolio_returns = self.calculate_portfolio_returns(positions)
    
    # Calculate VaR
    var = np.percentile(portfolio_returns, (1 - confidence) * 100)
    return var

def check_var_limits(self, positions: Dict[str, float]) -> bool:
    """
    Check if portfolio VaR is within limits.
    """
    var = self.calculate_var(positions)
    return abs(var) <= self.max_var_limit
```

### Portfolio Correlation
```python
def check_correlation_limits(self, positions: Dict[str, float]) -> bool:
    """
    Check portfolio correlation limits.
    """
    # Calculate correlation matrix
    returns = self.get_returns_data(list(positions.keys()))
    correlation = returns.corr()
    
    # Check correlation limits
    for i in range(len(correlation)):
        for j in range(i + 1, len(correlation)):
            if abs(correlation.iloc[i, j]) > self.max_correlation:
                return False
    
    return True
```

## Stop Loss Management

### Individual Position Stop Loss
```python
def apply_stop_loss(self, position: Dict[str, Any]) -> bool:
    """
    Check and apply stop loss for individual position.
    """
    current_price = position['current_price']
    entry_price = position['entry_price']
    
    if position['size'] > 0:  # Long position
        stop_price = entry_price * (1 - self.stop_loss_pct)
        return current_price < stop_price
    else:  # Short position
        stop_price = entry_price * (1 + self.stop_loss_pct)
        return current_price > stop_price
```

### Trailing Stop Loss
```python
def update_trailing_stop(self, position: Dict[str, Any]) -> float:
    """
    Update trailing stop loss level.
    """
    current_price = position['current_price']
    highest_price = position['highest_price']
    
    if position['size'] > 0:  # Long position
        if current_price > highest_price:
            position['highest_price'] = current_price
            position['stop_price'] = current_price * (1 - self.trailing_stop_pct)
    else:  # Short position
        if current_price < highest_price:
            position['highest_price'] = current_price
            position['stop_price'] = current_price * (1 + self.trailing_stop_pct)
    
    return position['stop_price']
```

## Exposure Management

### Sector Exposure
```python
def check_sector_exposure(self, positions: Dict[str, float]) -> bool:
    """
    Check sector exposure limits.
    """
    sector_exposure = defaultdict(float)
    
    for symbol, size in positions.items():
        sector = self.get_sector(symbol)
        exposure = abs(size * self.get_price(symbol)) / self.capital
        sector_exposure[sector] += exposure
    
    return all(exposure <= self.max_sector_exposure 
              for exposure in sector_exposure.values())
```

### Market Cap Exposure
```python
def check_market_cap_exposure(self, positions: Dict[str, float]) -> bool:
    """
    Check market capitalization exposure limits.
    """
    cap_exposure = defaultdict(float)
    
    for symbol, size in positions.items():
        cap_category = self.get_market_cap_category(symbol)
        exposure = abs(size * self.get_price(symbol)) / self.capital
        cap_exposure[cap_category] += exposure
    
    return all(exposure <= self.max_cap_exposure 
              for exposure in cap_exposure.values())
```

## Risk Metrics

### Portfolio Metrics
```python
def calculate_risk_metrics(self, positions: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate comprehensive risk metrics.
    """
    metrics = {
        'var_95': self.calculate_var(positions, 0.95),
        'var_99': self.calculate_var(positions, 0.99),
        'expected_shortfall': self.calculate_expected_shortfall(positions),
        'beta': self.calculate_portfolio_beta(positions),
        'volatility': self.calculate_portfolio_volatility(positions),
        'sharpe_ratio': self.calculate_sharpe_ratio(positions),
        'max_drawdown': self.calculate_max_drawdown(positions)
    }
    return metrics
```

### Performance Attribution
```python
def analyze_risk_attribution(self, positions: Dict[str, float]) -> Dict[str, float]:
    """
    Analyze risk attribution by position.
    """
    attribution = {}
    total_risk = self.calculate_portfolio_volatility(positions)
    
    for symbol, size in positions.items():
        # Calculate marginal contribution to risk
        mcr = self.calculate_marginal_risk_contribution(symbol, positions)
        attribution[symbol] = mcr / total_risk
    
    return attribution
```

## Risk Monitoring

### Real-time Monitoring
```python
def monitor_risk_limits(self) -> None:
    """
    Monitor risk limits in real-time.
    """
    while True:
        current_positions = self.get_current_positions()
        
        # Check risk limits
        var_breach = not self.check_var_limits(current_positions)
        correlation_breach = not self.check_correlation_limits(current_positions)
        exposure_breach = not self.check_sector_exposure(current_positions)
        
        if var_breach or correlation_breach or exposure_breach:
            self.handle_risk_breach(current_positions)
        
        time.sleep(self.monitoring_interval)
```

### Risk Reporting
```python
def generate_risk_report(self) -> Dict[str, Any]:
    """
    Generate comprehensive risk report.
    """
    positions = self.get_current_positions()
    
    report = {
        'timestamp': datetime.now(),
        'portfolio_value': self.calculate_portfolio_value(positions),
        'risk_metrics': self.calculate_risk_metrics(positions),
        'position_risks': self.analyze_risk_attribution(positions),
        'exposure': {
            'sector': self.get_sector_exposure(positions),
            'market_cap': self.get_market_cap_exposure(positions)
        },
        'alerts': self.get_risk_alerts(positions)
    }
    
    return report
```

## Best Practices

1. Regular Risk Review
   - Monitor risk metrics daily
   - Review position sizes and exposure
   - Check correlation changes
   - Update stop loss levels

2. Risk Parameters Adjustment
   - Adjust based on market conditions
   - Consider volatility regime changes
   - Review historical performance

3. Emergency Procedures
   - Define clear risk breach protocols
   - Implement automatic position reduction
   - Maintain emergency contact list
   - Document all risk events 