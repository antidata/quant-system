import pytest
import pandas as pd
import numpy as np
from src.strategies.moving_average_cross import MovingAverageCross

@pytest.fixture
def strategy():
    """Create a MovingAverageCross strategy instance for testing."""
    return MovingAverageCross(
        name="Test_MA_Cross",
        symbols=["AAPL", "GOOGL"],
        fast_period=10,
        slow_period=30,
        signal_threshold=0.001
    )

def test_initialization(strategy):
    """Test strategy initialization."""
    assert strategy.name == "Test_MA_Cross"
    assert strategy.symbols == ["AAPL", "GOOGL"]
    assert strategy.parameters["fast_period"] == 10
    assert strategy.parameters["slow_period"] == 30
    assert strategy.parameters["signal_threshold"] == 0.001

def test_generate_signals(strategy, sample_market_data):
    """Test signal generation."""
    signals = strategy.generate_signals(sample_market_data)
    
    assert isinstance(signals, dict)
    assert all(symbol in signals for symbol in strategy.symbols)
    assert all(-1.0 <= signal <= 1.0 for signal in signals.values())

def test_signal_generation_with_trend(strategy):
    """Test signal generation with a clear trend."""
    # Create trending data
    dates = pd.date_range(start='2023-01-01', end='2023-01-50', freq='D')
    trend_data = pd.DataFrame({
        'open': np.linspace(100, 150, len(dates)),
        'high': np.linspace(102, 152, len(dates)),
        'low': np.linspace(98, 148, len(dates)),
        'close': np.linspace(100, 150, len(dates)),
        'volume': [1000000] * len(dates)
    }, index=dates)
    
    data = {'AAPL': trend_data}
    signals = strategy.generate_signals(data)
    
    assert signals['AAPL'] > 0  # Should detect uptrend

def test_signal_generation_with_reversal(strategy):
    """Test signal generation with trend reversal."""
    dates = pd.date_range(start='2023-01-01', end='2023-01-50', freq='D')
    
    # Create data with trend reversal
    prices = np.concatenate([
        np.linspace(100, 150, 25),  # Uptrend
        np.linspace(150, 100, 25)   # Downtrend
    ])
    
    reversal_data = pd.DataFrame({
        'open': prices * 0.99,
        'high': prices * 1.01,
        'low': prices * 0.98,
        'close': prices,
        'volume': [1000000] * len(dates)
    }, index=dates)
    
    data = {'AAPL': reversal_data}
    signals = strategy.generate_signals(data)
    
    assert signals['AAPL'] < 0  # Should detect downtrend at the end

def test_signal_threshold(strategy):
    """Test signal threshold filtering."""
    # Create sideways market data with small oscillations
    dates = pd.date_range(start='2023-01-01', end='2023-01-50', freq='D')
    small_oscillation = 100 + np.sin(np.linspace(0, 4*np.pi, len(dates))) * 0.1
    
    sideways_data = pd.DataFrame({
        'open': small_oscillation * 0.99,
        'high': small_oscillation * 1.01,
        'low': small_oscillation * 0.98,
        'close': small_oscillation,
        'volume': [1000000] * len(dates)
    }, index=dates)
    
    data = {'AAPL': sideways_data}
    signals = strategy.generate_signals(data)
    
    assert abs(signals['AAPL']) < 0.1  # Should generate weak or no signals

def test_momentum_calculation(strategy):
    """Test momentum calculation."""
    dates = pd.date_range(start='2023-01-01', end='2023-01-50', freq='D')
    
    # Create strong trend data
    strong_trend = pd.DataFrame({
        'close': np.exp(np.linspace(0, 0.5, len(dates))) * 100,
        'returns': [0.01] * len(dates)
    }, index=dates)
    
    momentum = strategy._calculate_momentum(strong_trend)
    assert 0.5 < momentum <= 1.0  # Should indicate strong momentum
    
    # Create weak trend data
    weak_trend = pd.DataFrame({
        'close': np.linspace(100, 101, len(dates)),
        'returns': [0.001] * len(dates)
    }, index=dates)
    
    momentum = strategy._calculate_momentum(weak_trend)
    assert 0.0 <= momentum <= 0.7  # Should indicate weak momentum

def test_get_required_timeframes(strategy):
    """Test getting required timeframes."""
    timeframes = strategy.get_required_timeframes()
    assert timeframes == ["1d"]

def test_get_min_history(strategy):
    """Test getting minimum required history."""
    min_history = strategy.get_min_history()
    assert min_history == 50  # slow_period(30) + 20

def test_invalid_data_handling(strategy):
    """Test handling of invalid data."""
    # Empty data
    assert strategy.generate_signals({}) == {}
    
    # Missing required columns
    invalid_data = {
        'AAPL': pd.DataFrame({
            'close': [1, 2, 3]  # Missing other required columns
        })
    }
    assert strategy.generate_signals(invalid_data) == {}
    
    # Insufficient data points
    short_data = {
        'AAPL': pd.DataFrame({
            'open': [1, 2],
            'high': [1, 2],
            'low': [1, 2],
            'close': [1, 2],
            'volume': [1000, 2000]
        })
    }
    assert strategy.generate_signals(short_data) == {} 