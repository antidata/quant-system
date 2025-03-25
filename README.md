# Quantitative Trading System

A professional-grade quantitative trading system built with Python, implementing modern software architecture and design patterns. This system provides a robust framework for developing, testing, and deploying trading strategies with proper risk management.

![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Coverage](https://img.shields.io/badge/coverage-83%25-yellowgreen.svg)

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [License](#license)

## Features

### Core Functionality
- 🚀 **Modular Architecture**: Easily implement and test new trading strategies
- 📊 **Data Processing**:
  - Real-time market data integration
  - Historical data management
  - Custom data source support
  - Efficient data caching
- 🔍 **Technical Analysis**:
  - Integration with TA-Lib
  - Custom indicator development
  - Signal generation framework

### Trading & Analysis
- ⚡ **High-Performance Backtesting**:
  - Event-driven architecture
  - Transaction cost modeling
  - Slippage simulation
  - Multi-asset support
- 🛡️ **Risk Management**:
  - Position sizing
  - Portfolio optimization
  - Stop-loss management
  - Exposure limits
  - Correlation analysis
- 📈 **Analytics**:
  - Performance metrics
  - Risk metrics
  - Trade statistics
  - Visualization tools

### System Features
- 🔄 **Live Trading**:
  - Broker integration support
  - Real-time order management
  - Position tracking
- 🧪 **Quality Assurance**:
  - Extensive test coverage
  - Continuous integration
  - Code quality tools
- 📦 **Deployment**:
  - Docker support
  - Cloud deployment ready
  - Monitoring tools

## System Architecture

```
src/
├── core/              # Core system components
│   ├── strategy.py    # Base strategy class
│   └── constants.py   # System constants
├── strategies/        # Trading strategies
│   ├── moving_average_cross.py
│   └── custom_strategies/
├── data/             # Data handling
│   ├── market_data.py
│   └── processors/
├── risk/             # Risk management
│   ├── risk_manager.py
│   └── position_sizer.py
├── utils/            # Utilities
│   ├── metrics.py
│   └── helpers.py
├── config/           # Configuration
│   └── settings.py
├── models/           # Data models
│   └── schemas.py
├── backtesting/      # Backtesting engine
│   └── engine.py
└── analysis/         # Analysis tools
    └── performance.py
tests/                # Test suite
└── docs/            # Documentation
```

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Git (for version control)

### Step-by-Step Installation

1. Clone the repository:
```bash
git clone https://github.com/antidata/quant-system.git
cd quant-system
```

2. Create a conda environment:
```bash
conda create -n quantsystem311 python=3.11
conda activate quantsystem311
```

3. Install dependencies:
```bash
pip install numpy pandas scikit-learn matplotlib ta-lib yfinance pytest pytest-cov
```

4. Verify installation:
```bash
python -c "import numpy as np; import pandas as pd; import talib; print('Installation successful!')"
```

## Quick Start

```python
# Import required modules
from src.backtesting.engine import BacktestEngine
from src.strategies.moving_average_cross import MovingAverageCross
from src.risk.risk_manager import RiskManager

# Initialize strategy
strategy = MovingAverageCross(
    fast_period=10,
    slow_period=30,
    momentum_period=14
)

# Setup risk management
risk_manager = RiskManager(
    initial_capital=100000,
    max_position_size=0.1,
    stop_loss_pct=0.02
)

# Create and run backtest
engine = BacktestEngine(
    strategy=strategy,
    risk_manager=risk_manager,
    start_date="2023-01-01",
    end_date="2023-12-31",
    symbols=["AAPL", "GOOGL"],
    timeframe="1d"
)

# Run backtest and analyze results
results = engine.run()
performance = engine.analyze_performance()
```

## Configuration

### Environment Variables
Create a `.env` file with your configuration:

```env
# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
POLYGON_API_KEY=your_key_here

# Trading Parameters
INITIAL_CAPITAL=100000
MAX_POSITION_SIZE=0.1
RISK_FREE_RATE=0.02

# System Settings
LOG_LEVEL=INFO
CACHE_DIR=./cache
DATA_DIR=./data
```

### Strategy Parameters
Configure strategy parameters in `config/strategy_config.yaml`:

```yaml
moving_average_cross:
  fast_period: 10
  slow_period: 30
  momentum_period: 14
  signal_threshold: 0.1
```

## Usage Examples

### Implementing a Custom Strategy

```python
from src.core.strategy import Strategy
from typing import Dict, Any

class MyCustomStrategy(Strategy):
    def __init__(self, parameters: Dict[str, Any]):
        super().__init__()
        self.parameters = parameters
        
    def generate_signals(self, data: pd.DataFrame) -> Dict[str, float]:
        """
        Generate trading signals for each symbol
        Returns: Dict[symbol, signal_strength]
        """
        signals = {}
        for symbol, df in data.items():
            # Implement your strategy logic here
            signals[symbol] = self._calculate_signal(df)
        return signals
        
    def _calculate_signal(self, df: pd.DataFrame) -> float:
        # Custom signal calculation logic
        return signal_strength
```

### Running Analysis

```python
from src.analysis.performance import analyze_performance

# Analyze backtest results
metrics = analyze_performance(results)
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
print(f"Annual Return: {metrics['annual_return']:.2%}")
```

## Development

### Code Quality Tools

1. Code formatting:
```bash
black src/ tests/
isort src/ tests/
```

2. Type checking:
```bash
mypy src/ tests/
```

3. Linting:
```bash
pylint src/ tests/
```

### Git Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make changes and commit:
```bash
git add .
git commit -m "feat: description of your changes"
```

3. Push and create PR:
```bash
git push origin feature/your-feature-name
```

## Testing

### Running Tests

1. Run all tests:
```bash
pytest tests/
```

2. Run with coverage:
```bash
pytest tests/ -v --cov=src/ --cov-report=term-missing
```

3. Run specific test category:
```bash
pytest tests/strategies/  # Run strategy tests only
pytest tests/backtesting/  # Run backtesting tests only
```

### Test Coverage (as of latest update)
- Overall coverage: 83%
- Core components: 96%
- Strategies: 81%
- Risk management: 98%
- Data handling: 100%

## Contributing

1. Fork the repository
2. Create a feature branch
3. Follow code style guidelines
4. Add tests for new features
5. Update documentation
6. Submit a pull request

## Documentation

- [API Documentation](docs/api.md)
- [Strategy Development Guide](docs/strategy_guide.md)
- [Risk Management Guide](docs/risk_management.md)
- [Performance Analysis Guide](docs/analysis_guide.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/antidata/quant-system/issues)
3. Create a new issue if needed

Made with ❤️ by Mars