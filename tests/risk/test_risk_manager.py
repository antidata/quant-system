import pytest
import pandas as pd
import numpy as np
from src.risk.risk_manager import RiskManager

@pytest.fixture
def risk_manager():
    """Create a RiskManager instance for testing."""
    return RiskManager(
        initial_capital=100000.0,
        max_position_size=0.2,
        max_portfolio_risk=0.02,
        max_correlation=0.7,
        stop_loss_pct=0.02,
        max_drawdown=0.2
    )

def test_initialization(risk_manager):
    """Test RiskManager initialization."""
    assert risk_manager.initial_capital == 100000.0
    assert risk_manager.current_capital == 100000.0
    assert risk_manager.max_position_size == 0.2
    assert risk_manager.max_portfolio_risk == 0.02
    assert risk_manager.max_correlation == 0.7
    assert risk_manager.stop_loss_pct == 0.02
    assert risk_manager.max_drawdown == 0.2
    assert isinstance(risk_manager.positions, dict)
    assert len(risk_manager.positions) == 0

def test_calculate_position_size(risk_manager):
    """Test position size calculation with risk adjustment."""
    # Test long position with low volatility
    size = risk_manager.calculate_position_size(
        symbol="AAPL",
        signal=0.5,
        price=150.0,
        volatility=0.2
    )
    expected_size = (100000.0 * 0.2 * 0.5) * (1 / 1.2)  # Adjusted for volatility
    assert abs(size - expected_size) < 0.01
    
    # Test short position with high volatility
    size = risk_manager.calculate_position_size(
        symbol="GOOGL",
        signal=-0.8,
        price=2500.0,
        volatility=0.5
    )
    expected_size = -(100000.0 * 0.2 * 0.8) * (1 / 1.5)  # Adjusted for volatility
    assert abs(size - expected_size) < 0.01
    
    # Test zero signal
    size = risk_manager.calculate_position_size(
        symbol="MSFT",
        signal=0.0,
        price=300.0,
        volatility=0.3
    )
    assert size == 0.0

def test_check_portfolio_risk(risk_manager, sample_returns_data):
    """Test portfolio risk checking."""
    # Test empty portfolio
    assert risk_manager.check_portfolio_risk({}, {}) is True
    
    # Test single position
    positions = {'AAPL': 1000.0}
    assert risk_manager.check_portfolio_risk(positions, sample_returns_data) is True
    
    # Test multiple positions
    positions = {
        'AAPL': 10000.0,
        'GOOGL': -8000.0
    }
    result = risk_manager.check_portfolio_risk(positions, sample_returns_data)
    assert isinstance(result, bool)

def test_check_correlation_limits(risk_manager, sample_returns_data):
    """Test correlation limit checking."""
    # Test empty portfolio
    assert risk_manager.check_correlation_limits('AAPL', sample_returns_data) is True
    
    # Test with existing positions
    risk_manager.positions = {'GOOGL': 1000.0}
    result = risk_manager.check_correlation_limits('AAPL', sample_returns_data)
    assert isinstance(result, bool)
    
    # Test with non-existent symbol
    assert risk_manager.check_correlation_limits('NONEXISTENT', sample_returns_data) is True

def test_check_drawdown(risk_manager, sample_equity_curve):
    """Test drawdown checking."""
    # Test within limits
    assert risk_manager.check_drawdown(sample_equity_curve) is True
    
    # Test exceeding limits
    bad_equity_curve = sample_equity_curve * 0.7  # Create a 30% drawdown
    assert risk_manager.check_drawdown(bad_equity_curve) is False

def test_update_position(risk_manager):
    """Test position updates and capital adjustments."""
    # Test adding new position
    risk_manager.update_position(
        symbol="AAPL",
        size=100.0,
        price=150.0
    )
    assert risk_manager.positions["AAPL"] == 100.0
    assert risk_manager.current_capital == 85000.0  # 100000 - (100 * 150)
    
    # Test modifying existing position
    risk_manager.update_position(
        symbol="AAPL",
        size=50.0,
        price=160.0
    )
    assert risk_manager.positions["AAPL"] == 50.0
    assert abs(risk_manager.current_capital - 93000.0) < 0.01  # Previous capital + (50 * 160)
    
    # Test closing position
    risk_manager.update_position(
        symbol="AAPL",
        size=0.0,
        price=155.0
    )
    assert "AAPL" not in risk_manager.positions
    assert abs(risk_manager.current_capital - 100750.0) < 0.01

def test_get_stop_loss_price(risk_manager):
    """Test stop loss price calculation."""
    # Test long position
    stop_price = risk_manager.get_stop_loss_price(
        symbol="AAPL",
        entry_price=100.0,
        is_long=True
    )
    assert stop_price == 98.0  # 100 * (1 - 0.02)
    
    # Test short position
    stop_price = risk_manager.get_stop_loss_price(
        symbol="AAPL",
        entry_price=100.0,
        is_long=False
    )
    assert stop_price == 102.0  # 100 * (1 + 0.02)

def test_get_portfolio_stats(risk_manager):
    """Test portfolio statistics calculation."""
    # Set up some positions
    risk_manager.positions = {
        'AAPL': 1000.0,
        'GOOGL': -500.0
    }
    risk_manager.current_capital = 110000.0
    
    stats = risk_manager.get_portfolio_stats()
    
    assert stats['current_capital'] == 110000.0
    assert stats['total_exposure'] == 1500.0  # |1000| + |-500|
    assert stats['number_of_positions'] == 2
    assert stats['return_since_inception'] == 0.1  # (110000 - 100000) / 100000 