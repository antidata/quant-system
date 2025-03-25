import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.backtesting.engine import BacktestEngine
from src.strategies.moving_average_cross import MovingAverageCross

@pytest.fixture
def strategy():
    """Create a strategy instance for testing."""
    return MovingAverageCross(
        name="Test_Strategy",
        symbols=["AAPL", "GOOGL"],
        fast_period=10,
        slow_period=30
    )

@pytest.fixture
def backtest_engine(strategy):
    """Create a BacktestEngine instance for testing."""
    return BacktestEngine(
        strategy=strategy,
        initial_capital=100000.0,
        start_date="2023-01-01",
        end_date="2023-12-31",
        transaction_cost=0.001,
        slippage=0.001
    )

def test_initialization(backtest_engine, strategy):
    """Test BacktestEngine initialization."""
    assert backtest_engine.strategy == strategy
    assert backtest_engine.initial_capital == 100000.0
    assert backtest_engine.transaction_cost == 0.001
    assert backtest_engine.slippage == 0.001
    assert isinstance(backtest_engine.positions, dict)
    assert isinstance(backtest_engine.trades, list)
    assert isinstance(backtest_engine.equity_curve, list)

def test_get_common_dates(backtest_engine):
    """Test getting common dates from multiple data series."""
    dates1 = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
    dates2 = pd.date_range(start='2023-01-05', end='2023-01-15', freq='D')
    
    data = {
        'AAPL': pd.DataFrame(index=dates1),
        'GOOGL': pd.DataFrame(index=dates2)
    }
    
    common_dates = backtest_engine._get_common_dates(data)
    expected_dates = pd.date_range(start='2023-01-05', end='2023-01-10', freq='D')
    pd.testing.assert_index_equal(common_dates, expected_dates)

def test_get_data_slice(backtest_engine, sample_market_data):
    """Test getting data slice up to a specific date."""
    date = pd.Timestamp('2023-06-30')
    data_slice = backtest_engine._get_data_slice(sample_market_data, date)
    
    assert all(df.index.max() <= date for df in data_slice.values())
    assert all(symbol in data_slice for symbol in sample_market_data.keys())

def test_execute_trade(backtest_engine):
    """Test trade execution with costs."""
    # Execute buy trade
    backtest_engine._execute_trade(
        symbol="AAPL",
        size=100.0,
        price=150.0,
        date=pd.Timestamp('2023-01-01')
    )
    
    assert "AAPL" in backtest_engine.positions
    assert backtest_engine.positions["AAPL"] == 100.0
    assert len(backtest_engine.trades) == 1
    assert backtest_engine.trades[0]["symbol"] == "AAPL"
    assert backtest_engine.trades[0]["size"] == 100.0
    
    # Execute sell trade
    backtest_engine._execute_trade(
        symbol="AAPL",
        size=-50.0,
        price=160.0,
        date=pd.Timestamp('2023-01-02')
    )
    
    assert backtest_engine.positions["AAPL"] == -50.0
    assert len(backtest_engine.trades) == 2

def test_calculate_portfolio_value(backtest_engine, sample_market_data):
    """Test portfolio value calculation."""
    backtest_engine.positions = {
        'AAPL': 100.0,
        'GOOGL': -50.0
    }
    backtest_engine.risk_manager.current_capital = 90000.0
    
    portfolio_value = backtest_engine._calculate_portfolio_value(sample_market_data)
    assert isinstance(portfolio_value, float)
    assert portfolio_value != backtest_engine.risk_manager.current_capital  # Should include position values

@patch('src.data.market_data.MarketData.fetch_data')
def test_backtest_run(mock_fetch_data, backtest_engine, sample_market_data):
    """Test running a complete backtest."""
    mock_fetch_data.return_value = sample_market_data
    
    results = backtest_engine.run()
    
    assert isinstance(results, dict)
    assert all(key in results for key in [
        'total_return', 'annual_return', 'volatility', 'sharpe_ratio',
        'max_drawdown', 'win_rate', 'total_trades', 'equity_curve'
    ])
    assert len(results['equity_curve']) > 1

def test_performance_metrics_calculation(backtest_engine):
    """Test calculation of performance metrics."""
    # Simulate a successful trading period
    backtest_engine.equity_curve = [
        100000.0,  # Initial capital
        102000.0,  # Day 1
        103000.0,  # Day 2
        101000.0,  # Day 3
        104000.0   # Day 4
    ]
    
    backtest_engine.trades = [
        {"size": 100.0, "price": 150.0, "date": pd.Timestamp('2023-01-01')},
        {"size": -100.0, "price": 160.0, "date": pd.Timestamp('2023-01-02')}
    ]
    
    metrics = backtest_engine._calculate_performance_metrics()
    
    assert metrics['total_return'] == 0.04  # (104000 - 100000) / 100000
    assert metrics['max_drawdown'] > 0
    assert metrics['total_trades'] == 2
    assert len(metrics['equity_curve']) == 5

def test_risk_management_integration(backtest_engine, sample_market_data):
    """Test integration with risk management system."""
    with patch.object(backtest_engine.risk_manager, 'check_portfolio_risk') as mock_check_risk:
        mock_check_risk.return_value = False  # Simulate risk limit breach
        
        # Try to execute a trade
        backtest_engine._execute_trade(
            symbol="AAPL",
            size=1000000.0,  # Very large position
            price=150.0,
            date=pd.Timestamp('2023-01-01')
        )
        
        # Check that risk manager was consulted
        assert mock_check_risk.called
        
def test_transaction_costs(backtest_engine):
    """Test transaction cost calculations."""
    # Execute a trade with known parameters
    size = 100.0
    price = 150.0
    expected_transaction_cost = abs(size * price * backtest_engine.transaction_cost)
    
    backtest_engine._execute_trade(
        symbol="AAPL",
        size=size,
        price=price,
        date=pd.Timestamp('2023-01-01')
    )
    
    actual_transaction_cost = backtest_engine.trades[0]["transaction_cost"]
    assert abs(actual_transaction_cost - expected_transaction_cost) < 0.01

def test_slippage_impact(backtest_engine):
    """Test slippage impact on trade execution."""
    size = 100.0
    price = 150.0
    expected_executed_price = price * (1 + backtest_engine.slippage)  # For buy order
    
    backtest_engine._execute_trade(
        symbol="AAPL",
        size=size,
        price=price,
        date=pd.Timestamp('2023-01-01')
    )
    
    actual_executed_price = backtest_engine.trades[0]["price"]
    assert abs(actual_executed_price - expected_executed_price) < 0.01 