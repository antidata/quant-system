# Contributing Guide

This guide explains how to contribute to the Quantitative Trading System project.

## Getting Started

### Development Setup

1. Fork and Clone
```bash
# Fork the repository on GitHub
# Clone your fork locally
git clone https://github.com/your-username/quant-system.git
cd quant-system

# Add upstream remote
git remote add upstream https://github.com/original/quant-system.git
```

2. Create Virtual Environment
```bash
# Create conda environment
conda create -n quantsystem python=3.11
conda activate quantsystem

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Install Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install
```

## Development Process

### Code Style

1. Python Style Guide
```python
# Example of proper code style
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

class StrategyBase:
    """
    Base class for trading strategies.
    
    Attributes:
        name: Strategy name
        parameters: Strategy parameters
        position: Current position
    """
    
    def __init__(self,
                 name: str,
                 parameters: Dict[str, any]):
        """
        Initialize strategy.
        
        Args:
            name: Strategy name
            parameters: Strategy parameters
        """
        self.name = name
        self.parameters = parameters
        self.position = 0.0
    
    def generate_signals(self,
                        data: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.
        
        Args:
            data: Market data
            
        Returns:
            Series of trading signals
        """
        raise NotImplementedError
```

2. Documentation Style
```python
def calculate_metrics(returns: pd.Series) -> Dict[str, float]:
    """
    Calculate performance metrics from returns series.
    
    This function calculates various performance metrics including:
    - Total return
    - Annualized return
    - Sharpe ratio
    - Maximum drawdown
    
    Args:
        returns: Pandas Series of returns
        
    Returns:
        Dictionary containing calculated metrics
        
    Raises:
        ValueError: If returns series is empty
        
    Example:
        >>> returns = pd.Series([0.01, -0.02, 0.03])
        >>> metrics = calculate_metrics(returns)
        >>> print(metrics['total_return'])
        0.0194
    """
    if len(returns) == 0:
        raise ValueError("Returns series is empty")
    
    metrics = {
        'total_return': calculate_total_return(returns),
        'annualized_return': calculate_annualized_return(returns),
        'sharpe_ratio': calculate_sharpe_ratio(returns),
        'max_drawdown': calculate_max_drawdown(returns)
    }
    
    return metrics
```

### Testing

1. Unit Tests
```python
import pytest
import pandas as pd
from src.strategies.moving_average_cross import MovingAverageCross

class TestMovingAverageCross:
    @pytest.fixture
    def strategy(self):
        """
        Create strategy instance for testing.
        """
        params = {
            'short_window': 20,
            'long_window': 50,
            'entry_threshold': 0.001
        }
        return MovingAverageCross(parameters=params)
    
    @pytest.fixture
    def sample_data(self):
        """
        Create sample data for testing.
        """
        return pd.DataFrame({
            'close': range(100),
            'volume': [1000000] * 100
        })
    
    def test_signal_generation(self, strategy, sample_data):
        """
        Test signal generation logic.
        """
        signals = strategy.generate_signals(sample_data)
        
        assert isinstance(signals, pd.Series)
        assert len(signals) == len(sample_data)
        assert all(signals.isin([-1, 0, 1]))
```

2. Integration Tests
```python
class TestStrategyIntegration:
    @pytest.fixture
    def backtest_engine(self):
        """
        Create backtest engine for integration testing.
        """
        strategy = MovingAverageCross(parameters={'short_window': 20})
        data = load_test_data()
        return BacktestEngine(strategy=strategy, data=data)
    
    def test_complete_backtest(self, backtest_engine):
        """
        Test complete backtest execution.
        """
        results = backtest_engine.run()
        
        assert results is not None
        assert 'equity_curve' in results
        assert 'trades' in results
        assert len(results['trades']) > 0
```

### Code Review Process

1. Pull Request Template
```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing
Describe the tests you ran:
1. Unit tests
2. Integration tests
3. Performance tests

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] All tests passing
- [ ] No new warnings/errors
```

2. Review Guidelines
```python
# Example of code that needs review
class Strategy:
    def __init__(self):
        self.data = None  # What kind of data?
        self.position = 0  # Is this always a float?
    
    def process(self, x):  # What does x represent?
        # Magic numbers without explanation
        if x > 100:
            return 1
        elif x < 50:
            return -1
        return 0

# Better version
class Strategy:
    """Trading strategy base class."""
    
    def __init__(self):
        """Initialize strategy."""
        self.market_data: Optional[pd.DataFrame] = None
        self.current_position: float = 0.0
    
    def generate_signal(self, price: float) -> int:
        """
        Generate trading signal based on price.
        
        Args:
            price: Current asset price
            
        Returns:
            1 for buy, -1 for sell, 0 for hold
        """
        upper_threshold = self.parameters['upper_threshold']
        lower_threshold = self.parameters['lower_threshold']
        
        if price > upper_threshold:
            return 1
        elif price < lower_threshold:
            return -1
        return 0
```

## Project Structure

### Directory Organization
```
quant-system/
├── src/
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── moving_average_cross.py
│   ├── data/
│   │   ├── __init__.py
│   │   └── market_data.py
│   ├── backtesting/
│   │   ├── __init__.py
│   │   └── engine.py
│   └── risk/
│       ├── __init__.py
│       └── manager.py
├── tests/
│   ├── strategies/
│   │   └── test_moving_average_cross.py
│   ├── data/
│   │   └── test_market_data.py
│   └── backtesting/
│       └── test_engine.py
├── docs/
│   ├── api.md
│   ├── strategy_guide.md
│   └── contributing.md
├── config/
│   └── strategies/
│       └── moving_average_cross.yaml
├── requirements.txt
├── requirements-dev.txt
└── README.md
```

### Dependency Management
```toml
# pyproject.toml
[tool.poetry]
name = "quant-system"
version = "0.1.0"
description = "Quantitative Trading System"

[tool.poetry.dependencies]
python = "^3.11"
pandas = "^2.0.0"
numpy = "^1.24.0"
scipy = "^1.10.0"
scikit-learn = "^1.2.0"
ta-lib = "^0.4.0"

[tool.poetry.dev-dependencies]
pytest = "^7.3.0"
pytest-cov = "^4.0.0"
black = "^23.3.0"
flake8 = "^6.0.0"
mypy = "^1.3.0"
```

## Best Practices

1. Code Quality
   - Follow PEP 8 style guide
   - Write comprehensive docstrings
   - Use type hints
   - Keep functions focused and small

2. Testing
   - Write tests before code
   - Maintain high test coverage
   - Test edge cases
   - Use meaningful test names

3. Documentation
   - Keep docs up to date
   - Include examples
   - Document assumptions
   - Write clear commit messages

4. Version Control
   - Use feature branches
   - Write meaningful commits
   - Keep PRs focused
   - Squash commits when needed

5. Communication
   - Be respectful and professional
   - Provide constructive feedback
   - Ask questions when unclear
   - Share knowledge with others 