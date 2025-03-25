# API Documentation

This document provides detailed information about the APIs available in the Quantitative Trading System.

## Core Components

### Strategy API

#### Base Strategy Class
```python
class Strategy:
    def __init__(self)
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, float]
    def validate_data(self, data: pd.DataFrame) -> bool
    def calculate_position_size(self, signal: float, price: float) -> float
    def get_required_timeframes(self) -> List[str]
    def get_required_symbols(self) -> List[str]
```

#### Strategy Parameters
- `data`: Market data in pandas DataFrame format
- `signal`: Signal strength (-1.0 to 1.0)
- `price`: Current market price

### Market Data API

#### MarketData Class
```python
class MarketData:
    def __init__(self, cache_dir: str = "./cache")
    def fetch_data(self, symbols: List[str], start_date: str, end_date: str) -> Dict[str, pd.DataFrame]
    def get_latest_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame
```

#### Data Format
Each DataFrame contains:
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume
- Additional technical indicators

### Risk Management API

#### RiskManager Class
```python
class RiskManager:
    def __init__(self, initial_capital: float, max_position_size: float)
    def calculate_position_size(self, symbol: str, signal: float, price: float) -> float
    def check_portfolio_risk(self, positions: Dict[str, float]) -> bool
    def update_position(self, symbol: str, size: float, price: float) -> None
```

#### Risk Parameters
- `initial_capital`: Starting capital
- `max_position_size`: Maximum position size as percentage
- `stop_loss_pct`: Stop loss percentage

### Backtesting API

#### BacktestEngine Class
```python
class BacktestEngine:
    def __init__(self, strategy: Strategy, risk_manager: RiskManager, **kwargs)
    def run(self) -> Dict[str, Any]
    def analyze_performance(self) -> Dict[str, float]
```

#### Backtest Results
Returns dictionary containing:
- Performance metrics
- Trade history
- Portfolio values
- Risk metrics

## Data Sources

### Supported Data Providers
1. **YFinance**
   ```python
   from src.data.sources import YFinanceDataSource
   data = YFinanceDataSource().fetch_data(symbols=["AAPL"], start_date="2023-01-01")
   ```

2. **Alpha Vantage**
   ```python
   from src.data.sources import AlphaVantageDataSource
   data = AlphaVantageDataSource(api_key="your_key").fetch_data(symbols=["GOOGL"])
   ```

### Custom Data Sources
Implement the `DataSource` interface:
```python
class CustomDataSource(DataSource):
    def fetch_data(self, symbols: List[str], **kwargs) -> Dict[str, pd.DataFrame]
    def validate_data(self, data: pd.DataFrame) -> bool
```

## Performance Analysis

### Metrics Calculation
```python
from src.analysis.performance import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_returns
)
```

### Visualization Tools
```python
from src.analysis.visualization import (
    plot_equity_curve,
    plot_drawdown,
    plot_returns_distribution
)
```

## Error Handling

### Common Exceptions
```python
class InsufficientDataError(Exception)
class InvalidStrategyError(Exception)
class DataValidationError(Exception)
class RiskLimitExceededError(Exception)
```

### Error Handling Example
```python
try:
    results = engine.run()
except RiskLimitExceededError as e:
    logger.error(f"Risk limit exceeded: {e}")
except InsufficientDataError as e:
    logger.error(f"Insufficient data: {e}")
```

## Configuration

### Environment Variables
Required environment variables:
```env
ALPHA_VANTAGE_API_KEY=your_key
DATA_CACHE_DIR=./cache
LOG_LEVEL=INFO
```

### Strategy Configuration
Example strategy configuration:
```yaml
strategy:
  name: "MovingAverageCross"
  parameters:
    fast_period: 10
    slow_period: 30
```

## Logging

### Logger Configuration
```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
```

### Log Levels
- DEBUG: Detailed information for debugging
- INFO: General information about operation
- WARNING: Indication of potential issues
- ERROR: Serious issues that need attention
- CRITICAL: Critical issues that need immediate attention 