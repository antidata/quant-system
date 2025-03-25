# Strategy Development Guide

This guide provides detailed information about developing trading strategies for the Quantitative Trading System.

## Strategy Basics

### Strategy Components
1. Signal Generation
2. Position Sizing
3. Risk Management
4. Performance Monitoring

### Base Strategy Class
All strategies must inherit from the base `Strategy` class:
```python
from src.core.strategy import Strategy

class MyStrategy(Strategy):
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__()
        self.parameters = parameters
```

## Implementing a Strategy

### 1. Signal Generation
```python
def generate_signals(self, data: pd.DataFrame) -> Dict[str, float]:
    """
    Generate trading signals for each symbol.
    Returns a dictionary of symbol -> signal strength (-1.0 to 1.0)
    """
    signals = {}
    for symbol, df in data.items():
        # Calculate technical indicators
        sma_fast = df['close'].rolling(window=self.parameters['fast_period']).mean()
        sma_slow = df['close'].rolling(window=self.parameters['slow_period']).mean()
        
        # Generate signal (-1.0 to 1.0)
        signal = np.tanh(sma_fast - sma_slow)
        signals[symbol] = signal.iloc[-1]
    
    return signals
```

### 2. Position Sizing
```python
def calculate_position_size(self, signal: float, price: float) -> float:
    """
    Calculate the position size based on signal strength and risk parameters.
    """
    max_position = self.parameters['max_position_size']
    position_size = max_position * abs(signal)
    return position_size if signal > 0 else -position_size
```

### 3. Risk Management Integration
```python
def apply_risk_limits(self, position: float, price: float) -> float:
    """
    Apply risk management rules to position size.
    """
    max_risk = self.parameters['max_risk_pct'] * self.capital
    position_value = abs(position * price)
    
    if position_value > max_risk:
        position *= max_risk / position_value
    
    return position
```

## Strategy Types

### 1. Trend Following
Example moving average crossover strategy:
```python
class MovingAverageCross(Strategy):
    def __init__(self, fast_period: int = 10, slow_period: int = 30):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, float]:
        signals = {}
        for symbol, df in data.items():
            ma_fast = df['close'].rolling(window=self.fast_period).mean()
            ma_slow = df['close'].rolling(window=self.slow_period).mean()
            
            # Calculate crossover signal
            signal = np.where(ma_fast > ma_slow, 1.0, -1.0)
            signals[symbol] = signal[-1]
        
        return signals
```

### 2. Mean Reversion
Example RSI mean reversion strategy:
```python
class RSIMeanReversion(Strategy):
    def __init__(self, rsi_period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__()
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, float]:
        signals = {}
        for symbol, df in data.items():
            rsi = talib.RSI(df['close'], timeperiod=self.rsi_period)
            
            # Generate mean reversion signals
            signal = 0.0
            if rsi[-1] < self.oversold:
                signal = 1.0  # Buy when oversold
            elif rsi[-1] > self.overbought:
                signal = -1.0  # Sell when overbought
            
            signals[symbol] = signal
        
        return signals
```

### 3. Multi-Strategy Ensemble
Example strategy that combines multiple sub-strategies:
```python
class StrategyEnsemble(Strategy):
    def __init__(self,
                 name: str = "Strategy_Ensemble",
                 symbols: List[str] = None,
                 weights: Dict[str, float] = None):
        """
        Initialize the Strategy Ensemble.
        
        Args:
            name: Strategy name
            symbols: List of symbols to trade
            weights: Dictionary mapping strategy names to their weights
        """
        super().__init__(name=name, symbols=symbols)
        self.strategies = {}
        self.weights = weights or {}
        
        # Initialize sub-strategies
        self.strategies['trend'] = MovingAverageCross(
            name="MA_Cross",
            symbols=symbols,
            fast_period=10,
            slow_period=30
        )
        
        self.strategies['mean_reversion'] = RSIMeanReversion(
            name="RSI_MR",
            symbols=symbols,
            rsi_period=14,
            oversold=30,
            overbought=70
        )
        
        # Set default weights if not provided
        if not self.weights:
            self.weights = {
                'trend': 0.5,
                'mean_reversion': 0.5
            }
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Generate trading signals by combining signals from all sub-strategies.
        
        Args:
            data: Dictionary mapping symbols to their market data
            
        Returns:
            Dictionary mapping symbols to their trading signals (-1.0 to 1.0)
        """
        if not self.validate_data(data):
            return {}
        
        # Get signals from each strategy
        strategy_signals = {}
        for name, strategy in self.strategies.items():
            strategy_signals[name] = strategy.generate_signals(data)
        
        # Combine signals using weights
        combined_signals = {}
        for symbol in self.symbols:
            signal = 0.0
            for name, signals in strategy_signals.items():
                if symbol in signals:
                    signal += signals[symbol] * self.weights[name]
            combined_signals[symbol] = np.clip(signal, -1.0, 1.0)
        
        return combined_signals
    
    def optimize_weights(self,
                        data: Dict[str, pd.DataFrame],
                        optimization_method: str = 'equal_risk_contribution') -> None:
        """
        Optimize strategy weights based on historical performance.
        
        Args:
            data: Historical market data
            optimization_method: Method to use for weight optimization
        """
        if optimization_method == 'equal_risk_contribution':
            self._optimize_equal_risk_contribution(data)
        elif optimization_method == 'maximum_sharpe':
            self._optimize_maximum_sharpe(data)
        else:
            self._optimize_minimum_variance(data)
    
    def _optimize_equal_risk_contribution(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Optimize weights to achieve equal risk contribution from each strategy.
        """
        # Get historical returns for each strategy
        strategy_returns = {}
        for name, strategy in self.strategies.items():
            signals = strategy.generate_signals(data)
            returns = self._calculate_strategy_returns(signals, data)
            strategy_returns[name] = returns
        
        # Calculate covariance matrix
        returns_df = pd.DataFrame(strategy_returns)
        cov_matrix = returns_df.cov()
        
        # Calculate risk contribution weights
        weights = self._calculate_risk_parity_weights(cov_matrix)
        self.weights = dict(zip(self.strategies.keys(), weights))
    
    def _calculate_strategy_returns(self,
                                  signals: Dict[str, float],
                                  data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Calculate historical returns for a strategy.
        """
        portfolio_returns = pd.Series(0.0, index=data[self.symbols[0]].index)
        for symbol, signal in signals.items():
            returns = data[symbol]['returns']
            portfolio_returns += signal * returns
        return portfolio_returns
    
    def _calculate_risk_parity_weights(self, cov_matrix: pd.DataFrame) -> np.ndarray:
        """
        Calculate risk parity weights using numerical optimization.
        """
        n = len(cov_matrix)
        
        def risk_parity_objective(weights):
            portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            risk_contributions = weights * (np.dot(cov_matrix, weights)) / portfolio_risk
            return np.sum((risk_contributions[:, None] - risk_contributions) ** 2)
        
        # Optimize with constraints
        from scipy.optimize import minimize
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x}  # non-negative weights
        ]
        
        result = minimize(
            risk_parity_objective,
            x0=np.ones(n) / n,  # Start with equal weights
            constraints=constraints,
            method='SLSQP'
        )
        
        return result.x

# Example usage
def main():
    # Create and configure the strategy ensemble
    ensemble = StrategyEnsemble(
        name="Multi_Strategy",
        symbols=["AAPL", "MSFT", "GOOGL"],
        weights={
            'trend': 0.6,
            'mean_reversion': 0.4
        }
    )
    
    # Set up the backtesting engine
    engine = BacktestEngine(
        strategy=ensemble,
        initial_capital=100000.0,
        transaction_cost=0.001
    )
    
    # Run backtest
    results = engine.run()
    
    # Optimize strategy weights
    ensemble.optimize_weights(
        data=engine.get_historical_data(),
        optimization_method='equal_risk_contribution'
    )
    
    # Run backtest with optimized weights
    optimized_results = engine.run()
```

## Technical Indicators

### Using TA-Lib
```python
import talib

# Moving Averages
sma = talib.SMA(close_prices, timeperiod=20)
ema = talib.EMA(close_prices, timeperiod=20)

# Momentum Indicators
rsi = talib.RSI(close_prices, timeperiod=14)
macd, signal, hist = talib.MACD(close_prices)

# Volatility Indicators
bbands_upper, bbands_middle, bbands_lower = talib.BBANDS(close_prices)
atr = talib.ATR(high_prices, low_prices, close_prices)
```

### Custom Indicators
```python
def calculate_momentum(self, prices: pd.Series, period: int = 14) -> float:
    """
    Calculate price momentum indicator.
    """
    returns = prices.pct_change()
    momentum = returns.rolling(window=period).mean()
    return momentum.iloc[-1]

def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
    """
    Calculate price volatility.
    """
    returns = prices.pct_change()
    volatility = returns.rolling(window=period).std()
    return volatility.iloc[-1]
```

## Strategy Optimization

### Parameter Optimization
```python
def optimize_parameters(self, data: pd.DataFrame, param_grid: Dict) -> Dict:
    """
    Optimize strategy parameters using grid search.
    """
    best_sharpe = -np.inf
    best_params = None
    
    for params in ParameterGrid(param_grid):
        self.set_parameters(params)
        results = self.backtest(data)
        sharpe = self.calculate_sharpe_ratio(results)
        
        if sharpe > best_sharpe:
            best_sharpe = sharpe
            best_params = params
    
    return best_params
```

### Walk-Forward Analysis
```python
def walk_forward_analysis(self, data: pd.DataFrame, window_size: int = 252) -> List[Dict]:
    """
    Perform walk-forward analysis for strategy validation.
    """
    results = []
    for i in range(0, len(data) - window_size, window_size):
        train_data = data.iloc[i:i+window_size]
        test_data = data.iloc[i+window_size:i+2*window_size]
        
        # Optimize on training data
        optimal_params = self.optimize_parameters(train_data)
        self.set_parameters(optimal_params)
        
        # Test on unseen data
        test_results = self.backtest(test_data)
        results.append({
            'params': optimal_params,
            'performance': test_results
        })
    
    return results
```

## Best Practices

### 1. Data Validation
```python
def validate_data(self, data: pd.DataFrame) -> bool:
    """
    Validate input data quality.
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    # Check for required columns
    if not all(col in data.columns for col in required_columns):
        return False
    
    # Check for missing values
    if data[required_columns].isnull().any().any():
        return False
    
    # Check for sufficient history
    if len(data) < self.get_min_history():
        return False
    
    return True
```

### 2. Performance Monitoring
```python
def monitor_performance(self, results: Dict[str, Any]) -> None:
    """
    Monitor strategy performance metrics.
    """
    # Calculate key metrics
    sharpe_ratio = self.calculate_sharpe_ratio(results['returns'])
    max_drawdown = self.calculate_max_drawdown(results['equity'])
    win_rate = len(results['wins']) / len(results['trades'])
    
    # Log performance metrics
    logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    logger.info(f"Max Drawdown: {max_drawdown:.2%}")
    logger.info(f"Win Rate: {win_rate:.2%}")
```

### 3. Risk Management
```python
def apply_risk_management(self, position: float, price: float) -> float:
    """
    Apply comprehensive risk management rules.
    """
    # Position size limits
    position = self.apply_position_limits(position)
    
    # Portfolio concentration limits
    position = self.apply_concentration_limits(position)
    
    # Stop loss
    if self.check_stop_loss(price):
        position = 0.0
    
    return position
```

## Testing Strategies

### Unit Tests
```python
def test_signal_generation(self):
    """
    Test strategy signal generation.
    """
    data = self.generate_test_data()
    signals = self.strategy.generate_signals(data)
    
    assert isinstance(signals, dict)
    assert all(-1.0 <= signal <= 1.0 for signal in signals.values())

def test_position_sizing(self):
    """
    Test position sizing logic.
    """
    signal = 0.5
    price = 100.0
    position = self.strategy.calculate_position_size(signal, price)
    
    assert abs(position) <= self.strategy.parameters['max_position_size']
```

### Integration Tests
```python
def test_strategy_backtest(self):
    """
    Test full strategy backtest.
    """
    engine = BacktestEngine(
        strategy=self.strategy,
        data=self.test_data,
        initial_capital=100000
    )
    results = engine.run()
    
    assert results['final_equity'] > 0
    assert isinstance(results['trades'], list)
    assert len(results['trades']) > 0
``` 