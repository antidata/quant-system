import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.strategies.strategy_ensemble import StrategyEnsemble
from src.strategies.moving_average_cross import MovingAverageCross
from src.strategies.rsi_mean_reversion import RSIMeanReversion

@pytest.fixture
def sample_data():
    """Create sample market data for testing."""
    # Create a longer date range to ensure enough data for all indicators
    dates = pd.date_range(start='2023-01-01', end='2023-02-28', freq='D')
    symbols = ['AAPL', 'GOOGL']
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    data = {}
    for symbol in symbols:
        # Create a more complex price series with clear trends and reversals
        t = np.linspace(0, 4*np.pi, len(dates))  # Two complete cycles
        trend = np.linspace(100, 150, len(dates))  # Overall upward trend
        
        # Add both cyclical and random components for more realistic price movements
        cycle = 20 * np.sin(t)  # Cyclical component
        noise = np.random.normal(0, 3, len(dates))  # Increased random noise
        prices = trend + cycle + noise
        
        # Calculate returns with more volatility
        returns = pd.Series(prices).pct_change()
        returns.iloc[0] = 0.0  # Set first return to 0
        
        # Add some random spikes to ensure non-zero volatility
        spike_idx = np.random.choice(len(returns), size=5, replace=False)
        returns.iloc[spike_idx] = np.random.uniform(-0.05, 0.05, size=5)
        
        df = pd.DataFrame({
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(800000, 1200000, len(dates)),
            'returns': returns
        }, index=dates)
        
        data[symbol] = df
    
    return data

@pytest.fixture
def ensemble_strategy():
    """Create a StrategyEnsemble instance for testing."""
    return StrategyEnsemble(
        name="Test_Ensemble",
        symbols=["AAPL", "GOOGL"],
        weights={
            'trend': 0.6,
            'mean_reversion': 0.4
        }
    )

def test_ensemble_initialization(ensemble_strategy):
    """Test proper initialization of the ensemble strategy."""
    assert isinstance(ensemble_strategy.strategies['trend'], MovingAverageCross)
    assert isinstance(ensemble_strategy.strategies['mean_reversion'], RSIMeanReversion)
    assert ensemble_strategy.weights['trend'] == 0.6
    assert ensemble_strategy.weights['mean_reversion'] == 0.4
    assert sum(ensemble_strategy.weights.values()) == pytest.approx(1.0)

def test_default_weights():
    """Test initialization with default weights."""
    strategy = StrategyEnsemble(
        name="Test_Default_Weights",
        symbols=["AAPL", "GOOGL"]
    )
    assert strategy.weights['trend'] == 0.5
    assert strategy.weights['mean_reversion'] == 0.5
    assert sum(strategy.weights.values()) == pytest.approx(1.0)

def test_signal_generation(ensemble_strategy, sample_data):
    """Test signal generation from the ensemble."""
    signals = ensemble_strategy.generate_signals(sample_data)
    
    # Basic signal validation
    assert isinstance(signals, dict)
    assert all(symbol in signals for symbol in ["AAPL", "GOOGL"])
    assert all(-1.0 <= signal <= 1.0 for signal in signals.values())
    
    # Test signal combination
    trend_signals = ensemble_strategy.strategies['trend'].generate_signals(sample_data)
    mr_signals = ensemble_strategy.strategies['mean_reversion'].generate_signals(sample_data)
    
    for symbol in signals:
        # Calculate total valid weight
        valid_weight = 0.0
        weighted_signal = 0.0
        
        if symbol in trend_signals and not np.isnan(trend_signals[symbol]):
            weighted_signal += trend_signals[symbol] * ensemble_strategy.weights['trend']
            valid_weight += ensemble_strategy.weights['trend']
            
        if symbol in mr_signals and not np.isnan(mr_signals[symbol]):
            weighted_signal += mr_signals[symbol] * ensemble_strategy.weights['mean_reversion']
            valid_weight += ensemble_strategy.weights['mean_reversion']
        
        if valid_weight > 0:
            expected_signal = np.clip(weighted_signal / valid_weight, -1.0, 1.0)
            assert signals[symbol] == pytest.approx(expected_signal)

def test_optimize_equal_risk_contribution(ensemble_strategy, sample_data):
    """Test equal risk contribution optimization."""
    # Run optimization multiple times to ensure consistency
    results = []
    for _ in range(3):
        ensemble_strategy._optimize_equal_risk_contribution(sample_data)
        results.append(ensemble_strategy.weights.copy())
    
    # Check all results satisfy constraints
    for weights in results:
        # Check weights sum to 1
        assert sum(weights.values()) == pytest.approx(1.0)
        # Check all weights are positive and within bounds
        assert all(0.1 <= w <= 0.9 for w in weights.values())
        
        # Calculate risk contributions
        returns = {}
        for name, strategy in ensemble_strategy.strategies.items():
            signals = strategy.generate_signals(sample_data)
            returns[name] = ensemble_strategy._calculate_strategy_returns(signals, sample_data)
        
        returns_df = pd.DataFrame(returns).fillna(0)
        cov_matrix = returns_df.cov()
        cov_matrix = cov_matrix + np.eye(len(cov_matrix)) * 1e-6
        
        # Calculate risk contributions
        w = np.array(list(weights.values()))
        portfolio_risk = np.sqrt(np.dot(w, np.dot(cov_matrix, w)))
        risk_contributions = w * (np.dot(cov_matrix, w)) / portfolio_risk
        
        # Check risk contributions are approximately equal
        relative_diff = np.std(risk_contributions) / np.mean(risk_contributions)
        assert relative_diff < 0.2  # Allow for 20% relative difference

def test_calculate_strategy_returns(ensemble_strategy, sample_data):
    """Test calculation of strategy returns."""
    # Create test signals
    signals = {
        "AAPL": 0.5,
        "GOOGL": -0.3
    }
    
    returns = ensemble_strategy._calculate_strategy_returns(signals, sample_data)
    
    # Verify return calculations
    assert isinstance(returns, pd.Series)
    assert len(returns) == len(sample_data["AAPL"])
    assert not returns.isnull().any()

def test_invalid_data_handling(ensemble_strategy):
    """Test handling of invalid market data."""
    # Test with empty data
    assert ensemble_strategy.generate_signals({}) == {}
    
    # Test with missing required columns
    invalid_data = {
        "AAPL": pd.DataFrame({
            'close': [100, 101, 102],
            'volume': [1000, 1000, 1000]
        })
    }
    assert ensemble_strategy.generate_signals(invalid_data) == {}

def test_weight_constraints(ensemble_strategy, sample_data):
    """Test that optimized weights satisfy constraints."""
    ensemble_strategy.optimize_weights(sample_data, 'equal_risk_contribution')
    
    # Check weight constraints
    weights = ensemble_strategy.weights
    assert sum(weights.values()) == pytest.approx(1.0)  # Sum to 1
    assert all(0 <= w <= 1 for w in weights.values())  # Between 0 and 1
    assert len(weights) == len(ensemble_strategy.strategies)  # One weight per strategy

def test_optimization_methods(ensemble_strategy, sample_data):
    """Test different optimization methods."""
    # Test equal risk contribution
    ensemble_strategy.optimize_weights(sample_data, 'equal_risk_contribution')
    weights_erc = ensemble_strategy.weights.copy()
    
    # Verify optimization ran and produced valid weights
    assert weights_erc != {'trend': 0.6, 'mean_reversion': 0.4}
    assert sum(weights_erc.values()) == pytest.approx(1.0)
    
    # Test maximum Sharpe ratio
    ensemble_strategy.weights = {'trend': 0.6, 'mean_reversion': 0.4}  # Reset weights
    ensemble_strategy.optimize_weights(sample_data, 'maximum_sharpe')
    weights_sharpe = ensemble_strategy.weights.copy()
    
    # Verify Sharpe optimization
    assert weights_sharpe != weights_erc
    assert sum(weights_sharpe.values()) == pytest.approx(1.0)
    assert all(0.1 <= w <= 0.9 for w in weights_sharpe.values())
    
    # Test maximum Omega ratio
    ensemble_strategy.weights = {'trend': 0.6, 'mean_reversion': 0.4}  # Reset weights
    ensemble_strategy.optimize_weights(sample_data, 'maximum_omega')
    weights_omega = ensemble_strategy.weights.copy()
    
    # Verify Omega optimization
    assert weights_omega != weights_sharpe
    assert sum(weights_omega.values()) == pytest.approx(1.0)
    assert all(0.1 <= w <= 0.9 for w in weights_omega.values())
    
    # Test minimum variance (should fall back to this method)
    ensemble_strategy.weights = {'trend': 0.6, 'mean_reversion': 0.4}  # Reset weights
    ensemble_strategy.optimize_weights(sample_data, 'unknown_method')
    weights_min_var = ensemble_strategy.weights.copy()
    
    # Verify all methods produced different weights
    weights_list = [weights_erc, weights_sharpe, weights_omega, weights_min_var]
    for i in range(len(weights_list)):
        for j in range(i + 1, len(weights_list)):
            assert weights_list[i] != weights_list[j]

def test_sharpe_ratio_optimization(ensemble_strategy, sample_data):
    """Test Sharpe ratio optimization in detail."""
    # Run optimization with different risk-free rates
    ensemble_strategy._optimize_maximum_sharpe(sample_data, risk_free_rate=0.0)
    weights_zero_rf = ensemble_strategy.weights.copy()
    sharpe_zero = ensemble_strategy._calculate_portfolio_metrics(
        sample_data, weights_zero_rf, risk_free_rate=0.0)['sharpe_ratio']
    
    ensemble_strategy._optimize_maximum_sharpe(sample_data, risk_free_rate=0.1)  # Use larger difference
    weights_positive_rf = ensemble_strategy.weights.copy()
    sharpe_positive = ensemble_strategy._calculate_portfolio_metrics(
        sample_data, weights_positive_rf, risk_free_rate=0.1)['sharpe_ratio']
    
    # Verify that Sharpe ratios are reasonable and different
    assert sharpe_zero != sharpe_positive
    assert sharpe_zero > -np.inf
    assert sharpe_positive > -np.inf
    assert all(0.1 <= w <= 0.9 for w in weights_zero_rf.values())
    assert all(0.1 <= w <= 0.9 for w in weights_positive_rf.values())

def test_omega_ratio_optimization(ensemble_strategy, sample_data):
    """Test Omega ratio optimization in detail."""
    # Run optimization with different threshold returns
    ensemble_strategy._optimize_maximum_omega(sample_data, threshold_return=-0.01)  # Use negative threshold
    weights_negative_threshold = ensemble_strategy.weights.copy()
    omega_negative = ensemble_strategy._calculate_portfolio_metrics(
        sample_data, weights_negative_threshold, threshold_return=-0.01)['omega_ratio']
    
    ensemble_strategy._optimize_maximum_omega(sample_data, threshold_return=0.01)  # Use positive threshold
    weights_positive_threshold = ensemble_strategy.weights.copy()
    omega_positive = ensemble_strategy._calculate_portfolio_metrics(
        sample_data, weights_positive_threshold, threshold_return=0.01)['omega_ratio']
    
    # Verify that Omega ratios are reasonable and different
    assert omega_negative != omega_positive
    assert omega_negative > 0 and omega_negative < np.inf
    assert omega_positive > 0 and omega_positive < np.inf
    assert all(0.1 <= w <= 0.9 for w in weights_negative_threshold.values())
    assert all(0.1 <= w <= 0.9 for w in weights_positive_threshold.values())

def test_ensemble_with_single_symbol(sample_data):
    """Test ensemble behavior with a single symbol."""
    single_symbol_strategy = StrategyEnsemble(
        name="Single_Symbol_Test",
        symbols=["AAPL"]
    )
    
    signals = single_symbol_strategy.generate_signals({"AAPL": sample_data["AAPL"]})
    assert len(signals) == 1
    assert "AAPL" in signals
    assert -1.0 <= signals["AAPL"] <= 1.0 