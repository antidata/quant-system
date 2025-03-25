import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.data.market_data import MarketData
from unittest.mock import patch, MagicMock

@pytest.fixture
def market_data():
    """Create a MarketData instance for testing."""
    return MarketData(cache_dir="test_cache")

def test_initialization(market_data):
    """Test MarketData initialization."""
    assert market_data.cache_dir == "test_cache"
    assert isinstance(market_data.data_cache, dict)
    assert len(market_data.data_cache) == 0

def test_preprocess_data(market_data):
    """Test data preprocessing functionality."""
    # Create sample raw data
    dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
    raw_data = pd.DataFrame({
        'open': [100] * 10,
        'high': [105] * 10,
        'low': [95] * 10,
        'close': [101] * 10,
        'volume': [1000000] * 10
    }, index=dates)
    
    processed_data = market_data._preprocess_data(raw_data)
    
    # Check that all required columns are present
    required_columns = {
        'returns', 'log_returns', 'volatility',
        'volume_ma', 'volume_std',
        'ma_20', 'ma_50', 'ma_200'
    }
    assert all(col in processed_data.columns for col in required_columns)
    
    # Check calculations
    assert processed_data['returns'].iloc[1] == 0.0  # No change in price
    assert processed_data['volume_ma'].notna().any()  # Some values are calculated
    assert processed_data['volatility'].notna().any()  # Some values are calculated

@patch('yfinance.Ticker')
def test_fetch_single_symbol(mock_ticker, market_data):
    """Test fetching data for a single symbol."""
    # Mock the yfinance Ticker
    mock_history = pd.DataFrame({
        'Open': [100, 101],
        'High': [102, 103],
        'Low': [98, 99],
        'Close': [101, 102],
        'Volume': [1000000, 1100000]
    }, index=pd.date_range(start='2023-01-01', end='2023-01-02'))
    
    mock_ticker_instance = MagicMock()
    mock_ticker_instance.history.return_value = mock_history
    mock_ticker.return_value = mock_ticker_instance
    
    # Test successful fetch
    data = market_data._fetch_single_symbol(
        symbol="AAPL",
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 2),
        interval="1d",
        source="yfinance"
    )
    
    assert data is not None
    assert isinstance(data, pd.DataFrame)
    assert all(col in data.columns for col in ['open', 'high', 'low', 'close', 'volume'])
    
    # Test unsupported source
    with pytest.raises(ValueError):
        market_data._fetch_single_symbol(
            symbol="AAPL",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 2),
            interval="1d",
            source="unsupported"
        )

def test_fetch_data(market_data, sample_market_data):
    """Test fetching data for multiple symbols."""
    with patch.object(market_data, '_fetch_single_symbol') as mock_fetch:
        mock_fetch.side_effect = lambda symbol, **kwargs: sample_market_data[symbol]
        
        data = market_data.fetch_data(
            symbols=["AAPL", "GOOGL"],
            start_date="2023-01-01",
            end_date="2023-01-10",
            interval="1d"
        )
        
        assert len(data) == 2
        assert "AAPL" in data
        assert "GOOGL" in data
        assert isinstance(data["AAPL"], pd.DataFrame)
        assert isinstance(data["GOOGL"], pd.DataFrame)

def test_get_latest_data(market_data):
    """Test getting latest market data."""
    with patch.object(market_data, 'fetch_data') as mock_fetch:
        mock_fetch.return_value = {"AAPL": pd.DataFrame()}
        
        data = market_data.get_latest_data(
            symbols=["AAPL"],
            lookback_periods=100
        )
        
        assert mock_fetch.called
        assert isinstance(data, dict)
        assert "AAPL" in data

def test_cache_operations(market_data):
    """Test cache operations."""
    test_data = pd.DataFrame({'close': [1, 2, 3]})
    
    # Test caching data
    market_data.cache_data("AAPL", test_data)
    assert "AAPL" in market_data.data_cache
    assert market_data.data_cache["AAPL"].equals(test_data)
    
    # Test retrieving cached data
    cached_data = market_data.get_cached_data("AAPL")
    assert cached_data is not None
    assert cached_data.equals(test_data)
    
    # Test retrieving non-existent cached data
    assert market_data.get_cached_data("NONEXISTENT") is None
    
    # Test clearing cache
    market_data.clear_cache()
    assert len(market_data.data_cache) == 0 