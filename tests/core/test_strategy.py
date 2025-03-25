import pytest
import pandas as pd
from src.core.strategy import Strategy

class TestStrategy(Strategy):
    """Test strategy implementation for testing the base Strategy class."""
    def generate_signals(self, data):
        return {'AAPL': 0.5, 'GOOGL': -0.3}

def test_strategy_initialization():
    """Test strategy initialization with parameters."""
    strategy = TestStrategy(
        name="Test_Strategy",
        parameters={"param1": 10, "param2": "value"},
        symbols=["AAPL", "GOOGL"]
    )
    
    assert strategy.name == "Test_Strategy"
    assert strategy.parameters == {"param1": 10, "param2": "value"}
    assert strategy.symbols == ["AAPL", "GOOGL"]
    assert strategy.positions == {}
    assert strategy.current_signals == {}

def test_validate_data(sample_market_data):
    """Test data validation method."""
    strategy = TestStrategy(name="Test_Strategy")
    
    # Test valid data
    assert strategy.validate_data(sample_market_data) is True
    
    # Test invalid data cases
    assert strategy.validate_data({}) is False  # Empty data
    
    invalid_data = {'AAPL': pd.DataFrame({'close': [1, 2, 3]})}  # Missing required columns
    assert strategy.validate_data(invalid_data) is False
    
    invalid_data = {'AAPL': pd.DataFrame()}  # Empty DataFrame
    assert strategy.validate_data(invalid_data) is False
    
    invalid_data = {'AAPL': "not a dataframe"}  # Wrong type
    assert strategy.validate_data(invalid_data) is False

def test_calculate_position_size():
    """Test position size calculation."""
    strategy = TestStrategy(name="Test_Strategy")
    
    # Test long position
    size = strategy.calculate_position_size(
        signal=0.5,
        symbol="AAPL",
        portfolio_value=100000.0,
        risk_per_trade=0.02
    )
    assert size == 1000.0  # 100000 * 0.02 * 0.5
    
    # Test short position
    size = strategy.calculate_position_size(
        signal=-0.8,
        symbol="AAPL",
        portfolio_value=100000.0,
        risk_per_trade=0.02
    )
    assert size == -1600.0  # -100000 * 0.02 * 0.8
    
    # Test zero signal
    size = strategy.calculate_position_size(
        signal=0.0,
        symbol="AAPL",
        portfolio_value=100000.0,
        risk_per_trade=0.02
    )
    assert size == 0.0

def test_update_positions():
    """Test position updates based on signals."""
    strategy = TestStrategy(name="Test_Strategy")
    
    signals = {
        'AAPL': 0.5,
        'GOOGL': -0.3
    }
    
    new_positions = strategy.update_positions(
        signals=signals,
        portfolio_value=100000.0
    )
    
    assert new_positions['AAPL'] == 1000.0  # 100000 * 0.02 * 0.5
    assert new_positions['GOOGL'] == -600.0  # -100000 * 0.02 * 0.3
    assert strategy.positions == new_positions

def test_get_required_timeframes():
    """Test getting required timeframes."""
    strategy = TestStrategy(name="Test_Strategy")
    timeframes = strategy.get_required_timeframes()
    assert timeframes == ["1m"]  # Default value

def test_get_required_symbols():
    """Test getting required symbols."""
    strategy = TestStrategy(
        name="Test_Strategy",
        symbols=["AAPL", "GOOGL"]
    )
    symbols = strategy.get_required_symbols()
    assert symbols == ["AAPL", "GOOGL"]

def test_parameter_management():
    """Test parameter getting and setting."""
    strategy = TestStrategy(
        name="Test_Strategy",
        parameters={"param1": 10}
    )
    
    # Test getting parameters
    assert strategy.get_parameters() == {"param1": 10}
    
    # Test updating parameters
    strategy.set_parameters({"param2": 20})
    assert strategy.get_parameters() == {"param1": 10, "param2": 20}
    
    # Test overwriting parameters
    strategy.set_parameters({"param1": 30})
    assert strategy.get_parameters() == {"param1": 30, "param2": 20}

def test_string_representation():
    """Test string representation of strategy."""
    strategy = TestStrategy(
        name="Test_Strategy",
        symbols=["AAPL", "GOOGL"]
    )
    expected_str = "Test_Strategy Strategy (Symbols: AAPL, GOOGL)"
    assert str(strategy) == expected_str 