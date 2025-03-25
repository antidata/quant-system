from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime
import logging

class RiskManager:
    """
    Risk management system responsible for position sizing, exposure limits,
    and risk controls across the portfolio.
    """
    
    def __init__(self,
                 initial_capital: float,
                 max_position_size: float = 0.2,
                 max_portfolio_risk: float = 0.02,
                 max_correlation: float = 0.7,
                 stop_loss_pct: float = 0.02,
                 max_drawdown: float = 0.2):
        """
        Initialize the risk manager.
        
        Args:
            initial_capital: Starting capital
            max_position_size: Maximum position size as fraction of portfolio
            max_portfolio_risk: Maximum portfolio risk as fraction of portfolio
            max_correlation: Maximum allowed correlation between positions
            stop_loss_pct: Stop loss percentage
            max_drawdown: Maximum allowed drawdown
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation = max_correlation
        self.stop_loss_pct = stop_loss_pct
        self.max_drawdown = max_drawdown
        self.positions: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
        
    def calculate_position_size(self,
                              symbol: str,
                              signal: float,
                              price: float,
                              volatility: float) -> float:
        """
        Calculate the appropriate position size based on risk parameters.
        
        Args:
            symbol: Trading symbol
            signal: Trading signal (-1.0 to 1.0)
            price: Current price
            volatility: Current volatility
            
        Returns:
            Position size in base currency
        """
        # Calculate maximum position size based on portfolio value
        max_position = self.current_capital * self.max_position_size
        
        # Adjust for volatility
        volatility_scalar = 1.0 / (1.0 + volatility)
        
        # Scale by signal strength
        position_size = max_position * abs(signal) * volatility_scalar
        
        # Ensure position respects stop loss
        stop_loss_size = (self.current_capital * self.stop_loss_pct) / (price * volatility)
        position_size = min(position_size, stop_loss_size)
        
        return position_size if signal > 0 else -position_size
    
    def check_portfolio_risk(self, 
                           positions: Dict[str, float],
                           returns: Dict[str, pd.Series]) -> bool:
        """
        Check if the portfolio risk is within acceptable limits.
        
        Args:
            positions: Dictionary of current positions
            returns: Dictionary of historical returns
            
        Returns:
            True if portfolio risk is acceptable, False otherwise
        """
        if not positions or not returns:
            return True
            
        # Calculate portfolio variance
        position_values = pd.Series(positions)
        returns_df = pd.DataFrame(returns)
        correlation = returns_df.corr()
        volatilities = returns_df.std()
        
        portfolio_variance = 0.0
        for i, sym1 in enumerate(positions.keys()):
            for j, sym2 in enumerate(positions.keys()):
                portfolio_variance += (
                    positions[sym1] * positions[sym2] *
                    volatilities[sym1] * volatilities[sym2] *
                    correlation.loc[sym1, sym2]
                )
                
        portfolio_risk = np.sqrt(portfolio_variance)
        return portfolio_risk <= self.max_portfolio_risk
    
    def check_correlation_limits(self,
                               new_position: str,
                               returns: Dict[str, pd.Series]) -> bool:
        """
        Check if adding a new position would violate correlation limits.
        
        Args:
            new_position: Symbol of the new position
            returns: Dictionary of historical returns
            
        Returns:
            True if correlation limits are respected, False otherwise
        """
        if not self.positions or new_position not in returns:
            return True
            
        returns_df = pd.DataFrame(returns)
        correlation = returns_df.corr()
        
        for existing_position in self.positions:
            if existing_position in correlation.columns:
                if abs(correlation.loc[new_position, existing_position]) > self.max_correlation:
                    return False
                    
        return True
    
    def check_drawdown(self, equity_curve: pd.Series) -> bool:
        """
        Check if the current drawdown exceeds the maximum allowed.
        
        Args:
            equity_curve: Series of portfolio equity values
            
        Returns:
            True if drawdown is acceptable, False otherwise
        """
        rolling_max = equity_curve.expanding().max()
        drawdown = (equity_curve - rolling_max) / rolling_max
        return abs(drawdown.min()) <= self.max_drawdown
    
    def update_position(self,
                       symbol: str,
                       size: float,
                       price: float) -> None:
        """
        Update a position in the portfolio.
        
        Args:
            symbol: Trading symbol
            size: New position size
            price: Current price
        """
        old_size = self.positions.get(symbol, 0.0)
        self.positions[symbol] = size
        
        # Update current capital
        position_change = (size - old_size) * price
        self.current_capital -= position_change
        
    def get_stop_loss_price(self,
                           symbol: str,
                           entry_price: float,
                           is_long: bool) -> float:
        """
        Calculate the stop loss price for a position.
        
        Args:
            symbol: Trading symbol
            entry_price: Position entry price
            is_long: Whether the position is long
            
        Returns:
            Stop loss price
        """
        if is_long:
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)
    
    def get_portfolio_stats(self) -> Dict[str, float]:
        """
        Get current portfolio statistics.
        
        Returns:
            Dictionary of portfolio statistics
        """
        return {
            "current_capital": self.current_capital,
            "total_exposure": sum(abs(pos) for pos in self.positions.values()),
            "number_of_positions": len(self.positions),
            "return_since_inception": (self.current_capital - self.initial_capital) / self.initial_capital
        } 