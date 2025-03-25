import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict

@pytest.fixture
def sample_market_data() -> Dict[str, pd.DataFrame]:
    """Create sample market data for testing."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    symbols = ['AAPL', 'GOOGL']
    data = {}
    
    for symbol in symbols:
        # Generate synthetic price data
        np.random.seed(42)  # For reproducibility
        prices = 100 * (1 + np.random.randn(len(dates)).cumsum() * 0.02)
        volume = np.random.randint(1000000, 5000000, size=len(dates))
        
        df = pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': volume
        }, index=dates)
        
        data[symbol] = df
    
    return data

@pytest.fixture
def sample_returns_data() -> Dict[str, pd.Series]:
    """Create sample returns data for testing."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    symbols = ['AAPL', 'GOOGL']
    data = {}
    
    for symbol in symbols:
        np.random.seed(42 + symbols.index(symbol))  # Different seed for each symbol
        returns = np.random.randn(len(dates)) * 0.01  # 1% daily volatility
        data[symbol] = pd.Series(returns, index=dates)
    
    return data

@pytest.fixture
def sample_equity_curve() -> pd.Series:
    """Create sample equity curve data for testing."""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    np.random.seed(42)
    
    # Generate synthetic equity curve with trend and noise
    returns = np.random.randn(len(dates)) * 0.01 + 0.0002  # Positive drift
    equity = 100000 * (1 + pd.Series(returns).cumsum())
    
    return pd.Series(equity, index=dates) 