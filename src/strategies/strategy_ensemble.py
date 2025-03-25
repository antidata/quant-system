from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from scipy.optimize import minimize

from src.core.strategy import Strategy
from src.strategies.moving_average_cross import MovingAverageCross
from src.strategies.rsi_mean_reversion import RSIMeanReversion

class StrategyEnsemble(Strategy):
    """
    A strategy that combines multiple trading strategies and their signals.
    Supports weighted signal combination and weight optimization methods.
    """
    
    def __init__(self,
                 name: str = "Strategy_Ensemble",
                 symbols: List[str] = None,
                 weights: Dict[str, float] = None):
        """
        Initialize the Strategy Ensemble.
        
        Args:
            name: Strategy name
            symbols: List of symbols to trade
            weights: Dictionary mapping strategy names to their weights
        """
        super().__init__(name=name, symbols=symbols)
        self.strategies = {}
        self.weights = weights or {}
        
        # Initialize sub-strategies
        self.strategies['trend'] = MovingAverageCross(
            name="MA_Cross",
            symbols=symbols,
            fast_period=10,
            slow_period=30
        )
        
        self.strategies['mean_reversion'] = RSIMeanReversion(
            name="RSI_MR",
            symbols=symbols,
            rsi_period=14,
            oversold=30,
            overbought=70
        )
        
        # Set default weights if not provided
        if not self.weights:
            self.weights = {
                'trend': 0.5,
                'mean_reversion': 0.5
            }
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Generate trading signals by combining signals from all sub-strategies.
        
        Args:
            data: Dictionary mapping symbols to their market data
            
        Returns:
            Dictionary mapping symbols to their trading signals (-1.0 to 1.0)
        """
        if not self.validate_data(data):
            return {}
        
        # Get signals from each strategy
        strategy_signals = {}
        for name, strategy in self.strategies.items():
            try:
                signals = strategy.generate_signals(data)
                if signals:  # Only store if we got valid signals
                    strategy_signals[name] = signals
            except Exception as e:
                print(f"Warning: Strategy {name} failed to generate signals: {e}")
                continue
        
        if not strategy_signals:
            return {}
        
        # Combine signals using weights
        combined_signals = {}
        for symbol in self.symbols:
            if symbol not in data:
                continue
                
            signal = 0.0
            valid_weights = 0.0
            
            for name, signals in strategy_signals.items():
                if symbol in signals and not np.isnan(signals[symbol]):
                    signal += signals[symbol] * self.weights[name]
                    valid_weights += self.weights[name]
            
            if valid_weights > 0:
                # Normalize by valid weights
                signal = signal / valid_weights
                combined_signals[symbol] = np.clip(signal, -1.0, 1.0)
        
        return combined_signals
    
    def optimize_weights(self,
                        data: Dict[str, pd.DataFrame],
                        optimization_method: str = 'equal_risk_contribution') -> None:
        """
        Optimize strategy weights based on historical performance.
        
        Args:
            data: Historical market data
            optimization_method: Method to use for weight optimization
                - 'equal_risk_contribution': Equal risk contribution from each strategy
                - 'minimum_variance': Minimize portfolio variance
                - 'maximum_sharpe': Maximize Sharpe ratio
                - 'maximum_omega': Maximize Omega ratio
        """
        if optimization_method == 'equal_risk_contribution':
            self._optimize_equal_risk_contribution(data)
        elif optimization_method == 'maximum_sharpe':
            self._optimize_maximum_sharpe(data)
        elif optimization_method == 'maximum_omega':
            self._optimize_maximum_omega(data)
        else:
            self._optimize_minimum_variance(data)
    
    def _optimize_equal_risk_contribution(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Optimize weights to achieve equal risk contribution from each strategy.
        """
        # Get historical returns for each strategy
        strategy_returns = {}
        for name, strategy in self.strategies.items():
            signals = strategy.generate_signals(data)
            returns = self._calculate_strategy_returns(signals, data)
            strategy_returns[name] = returns
        
        # Calculate covariance matrix
        returns_df = pd.DataFrame(strategy_returns).fillna(0)
        cov_matrix = returns_df.cov()
        
        # Add small diagonal value to ensure matrix is well-conditioned
        cov_matrix = cov_matrix + np.eye(len(cov_matrix)) * 1e-6
        
        def risk_parity_objective(weights):
            weights = np.array(weights)
            portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            if portfolio_risk == 0:
                return 1e6  # Penalize zero risk
            risk_contributions = weights * (np.dot(cov_matrix, weights)) / portfolio_risk
            target_risk = portfolio_risk / len(weights)  # Equal risk contribution
            # Use relative differences for better scaling
            relative_diffs = (risk_contributions - target_risk) / target_risk
            return np.sum(relative_diffs ** 2)
        
        # Optimize with constraints
        n_strategies = len(self.strategies)
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x - 0.1}  # minimum weight of 10%
        ]
        bounds = [(0.1, 0.9) for _ in range(n_strategies)]
        
        # Try multiple starting points with different initial weights
        best_result = None
        best_objective = float('inf')
        
        for _ in range(10):  # Increase number of attempts
            # Generate random weights that sum to 1
            x0 = np.random.dirichlet(np.ones(n_strategies))
            # Ensure minimum weight constraint
            x0 = np.clip(x0, 0.1, 0.9)
            x0 = x0 / x0.sum()  # Renormalize
            
            result = minimize(
                risk_parity_objective,
                x0=x0,
                bounds=bounds,
                constraints=constraints,
                method='SLSQP',
                options={'ftol': 1e-12, 'maxiter': 2000}
            )
            
            if result.fun < best_objective:
                best_objective = result.fun
                best_result = result
        
        # Update weights
        self.weights = dict(zip(self.strategies.keys(), best_result.x))
    
    def _optimize_minimum_variance(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Optimize weights to minimize portfolio variance while maintaining
        minimum expected return.
        """
        # Get historical returns for each strategy
        strategy_returns = {}
        for name, strategy in self.strategies.items():
            signals = strategy.generate_signals(data)
            returns = self._calculate_strategy_returns(signals, data)
            strategy_returns[name] = returns
        
        # Calculate covariance matrix and mean returns
        returns_df = pd.DataFrame(strategy_returns).fillna(0)
        cov_matrix = returns_df.cov()
        mean_returns = returns_df.mean()
        
        # Add small diagonal value to ensure matrix is well-conditioned
        cov_matrix = cov_matrix + np.eye(len(cov_matrix)) * 1e-6
        
        def min_variance_objective(weights):
            weights = np.array(weights)
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            expected_return = np.dot(weights, mean_returns)
            # Add return target as a penalty term
            return portfolio_variance - 0.1 * expected_return
        
        # Optimize with constraints
        n_strategies = len(self.strategies)
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x - 0.2}  # minimum weight of 20%
        ]
        bounds = [(0.2, 0.8) for _ in range(n_strategies)]
        
        # Try multiple starting points
        best_result = None
        best_objective = float('inf')
        
        for _ in range(5):  # Try 5 different random starting points
            x0 = np.random.dirichlet(np.ones(n_strategies))  # Random weights that sum to 1
            result = minimize(
                min_variance_objective,
                x0=x0,
                bounds=bounds,
                constraints=constraints,
                method='SLSQP',
                options={'ftol': 1e-12, 'maxiter': 1000}
            )
            
            if result.fun < best_objective:
                best_objective = result.fun
                best_result = result
        
        # Update weights
        self.weights = dict(zip(self.strategies.keys(), best_result.x))
    
    def _calculate_strategy_returns(self,
                                  signals: Dict[str, float],
                                  data: Dict[str, pd.DataFrame]) -> pd.Series:
        """
        Calculate historical returns for a strategy.
        
        Args:
            signals: Dictionary mapping symbols to their signals
            data: Market data dictionary
            
        Returns:
            Series of strategy returns
        """
        # Initialize returns with zeros
        first_symbol = next(iter(data))
        portfolio_returns = pd.Series(0.0, index=data[first_symbol].index)
        
        # Calculate position-weighted returns
        for symbol, signal in signals.items():
            if symbol in data and 'returns' in data[symbol]:
                symbol_returns = data[symbol]['returns'].fillna(0)  # Handle NaN values
                portfolio_returns += signal * symbol_returns
        
        return portfolio_returns / len(signals)  # Normalize by number of symbols 

    def _optimize_maximum_sharpe(self, data: Dict[str, pd.DataFrame], risk_free_rate: float = 0.0) -> None:
        """
        Optimize weights to maximize the Sharpe ratio.
        
        Args:
            data: Historical market data
            risk_free_rate: Annual risk-free rate (default: 0.0)
        """
        # Get historical returns for each strategy
        strategy_returns = {}
        for name, strategy in self.strategies.items():
            signals = strategy.generate_signals(data)
            returns = self._calculate_strategy_returns(signals, data)
            strategy_returns[name] = returns
        
        returns_df = pd.DataFrame(strategy_returns).fillna(0)
        daily_rf = risk_free_rate / 252  # Convert annual to daily
        
        def sharpe_ratio_objective(weights):
            weights = np.array(weights)
            portfolio_returns = returns_df.dot(weights)
            excess_returns = portfolio_returns - daily_rf
            
            # Add small noise to returns if volatility is too low
            if excess_returns.std() < 1e-8:
                noise = np.random.normal(0, 1e-8, len(excess_returns))
                excess_returns = excess_returns + noise
            
            sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
            return -sharpe  # Negative for minimization
        
        # Optimize with constraints
        n_strategies = len(self.strategies)
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x - 0.1}  # minimum weight of 10%
        ]
        bounds = [(0.1, 0.9) for _ in range(n_strategies)]
        
        # Try multiple starting points with different initial weights
        best_result = None
        best_objective = float('inf')
        
        for _ in range(10):  # Increase number of attempts
            # Generate random weights that sum to 1
            x0 = np.random.dirichlet(np.ones(n_strategies))
            # Ensure minimum weight constraint
            x0 = np.clip(x0, 0.1, 0.9)
            x0 = x0 / x0.sum()  # Renormalize
            
            result = minimize(
                sharpe_ratio_objective,
                x0=x0,
                bounds=bounds,
                constraints=constraints,
                method='SLSQP',
                options={'ftol': 1e-12, 'maxiter': 2000}
            )
            
            if result.fun < best_objective:
                best_objective = result.fun
                best_result = result
        
        # Update weights
        self.weights = dict(zip(self.strategies.keys(), best_result.x))

    def _optimize_maximum_omega(self, data: Dict[str, pd.DataFrame], threshold_return: float = 0.0) -> None:
        """
        Optimize weights to maximize the Omega ratio.
        The Omega ratio is the probability weighted ratio of gains versus losses for a threshold return.
        
        Args:
            data: Historical market data
            threshold_return: Daily threshold return (default: 0.0)
        """
        # Get historical returns for each strategy
        strategy_returns = {}
        for name, strategy in self.strategies.items():
            signals = strategy.generate_signals(data)
            returns = self._calculate_strategy_returns(signals, data)
            strategy_returns[name] = returns
        
        returns_df = pd.DataFrame(strategy_returns).fillna(0)
        
        def omega_ratio_objective(weights):
            weights = np.array(weights)
            portfolio_returns = returns_df.dot(weights)
            
            # Calculate gains and losses relative to threshold
            gains = portfolio_returns[portfolio_returns > threshold_return] - threshold_return
            losses = threshold_return - portfolio_returns[portfolio_returns < threshold_return]
            
            # Handle edge cases with regularization
            gains_sum = gains.sum() + 1e-6  # Add small constant to avoid division by zero
            losses_sum = losses.sum() + 1e-6
            
            # Calculate regularized Omega ratio
            omega = (gains_sum / len(portfolio_returns)) / (losses_sum / len(portfolio_returns))
            return -omega  # Negative for minimization
        
        # Optimize with constraints
        n_strategies = len(self.strategies)
        constraints = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},  # weights sum to 1
            {'type': 'ineq', 'fun': lambda x: x - 0.1}  # minimum weight of 10%
        ]
        bounds = [(0.1, 0.9) for _ in range(n_strategies)]
        
        # Try multiple starting points with different initial weights
        best_result = None
        best_objective = float('inf')
        
        for _ in range(10):  # Increase number of attempts
            # Generate random weights that sum to 1
            x0 = np.random.dirichlet(np.ones(n_strategies))
            # Ensure minimum weight constraint
            x0 = np.clip(x0, 0.1, 0.9)
            x0 = x0 / x0.sum()  # Renormalize
            
            result = minimize(
                omega_ratio_objective,
                x0=x0,
                bounds=bounds,
                constraints=constraints,
                method='SLSQP',
                options={'ftol': 1e-12, 'maxiter': 2000}
            )
            
            if result.fun < best_objective:
                best_objective = result.fun
                best_result = result
        
        # Update weights
        self.weights = dict(zip(self.strategies.keys(), best_result.x))

    def _calculate_portfolio_metrics(self, data: Dict[str, pd.DataFrame], weights: Dict[str, float], risk_free_rate: float = 0.0, threshold_return: float = 0.0) -> Dict[str, float]:
        """
        Calculate portfolio metrics including Sharpe ratio and Omega ratio.
        
        Args:
            data: Historical market data
            weights: Strategy weights
            risk_free_rate: Annual risk-free rate for Sharpe ratio calculation
            threshold_return: Daily threshold return for Omega ratio calculation
            
        Returns:
            Dictionary containing portfolio metrics
        """
        # Get historical returns for each strategy
        strategy_returns = {}
        for name, strategy in self.strategies.items():
            signals = strategy.generate_signals(data)
            returns = self._calculate_strategy_returns(signals, data)
            strategy_returns[name] = returns
        
        returns_df = pd.DataFrame(strategy_returns).fillna(0)
        portfolio_returns = returns_df.dot(pd.Series(weights))
        
        # Calculate annualized metrics
        annual_return = portfolio_returns.mean() * 252
        annual_vol = portfolio_returns.std() * np.sqrt(252)
        
        # Calculate Sharpe ratio with specified risk-free rate
        daily_rf = risk_free_rate / 252  # Convert annual to daily
        excess_returns = portfolio_returns - daily_rf
        
        # Add small noise to returns if volatility is too low
        if excess_returns.std() < 1e-8:
            noise = np.random.normal(0, 1e-8, len(excess_returns))
            excess_returns = excess_returns + noise
        
        sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
        
        # Calculate Omega ratio with specified threshold
        gains = portfolio_returns[portfolio_returns > threshold_return] - threshold_return
        losses = threshold_return - portfolio_returns[portfolio_returns < threshold_return]
        
        gains_sum = gains.sum() + 1e-6  # Add small constant to avoid division by zero
        losses_sum = losses.sum() + 1e-6
        omega_ratio = (gains_sum / len(portfolio_returns)) / (losses_sum / len(portfolio_returns))
        
        return {
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'sharpe_ratio': sharpe_ratio,
            'omega_ratio': omega_ratio
        } 