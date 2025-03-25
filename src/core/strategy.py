from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from datetime import datetime

class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    This class defines the interface that all strategy implementations must follow.
    It provides common functionality and enforces a consistent structure across
    different trading strategies.
    """
    
    def __init__(self, 
                 name: str,
                 parameters: Dict[str, Union[float, int, str]] = None,
                 symbols: List[str] = None):
        """
        Initialize the strategy with basic parameters.
        
        Args:
            name: Unique identifier for the strategy
            parameters: Dictionary of strategy-specific parameters
            symbols: List of trading symbols this strategy will track
        """
        self.name = name
        self.parameters = parameters or {}
        self.symbols = symbols or []
        self.positions: Dict[str, float] = {}
        self.current_signals: Dict[str, float] = {}
        
    @abstractmethod
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Generate trading signals for the given market data.
        
        Args:
            data: Dictionary mapping symbol to its market data DataFrame
            
        Returns:
            Dictionary mapping symbol to its signal (-1.0 to 1.0)
        """
        pass
    
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """
        Validate that the input data meets the strategy's requirements.
        
        Args:
            data: Dictionary mapping symbol to its market data DataFrame
            
        Returns:
            True if data is valid, False otherwise
        """
        if not data:
            return False
            
        required_columns = {'open', 'high', 'low', 'close', 'volume'}
        
        for symbol, df in data.items():
            if not isinstance(df, pd.DataFrame):
                return False
            if not required_columns.issubset(df.columns):
                return False
            if df.empty:
                return False
                
        return True
    
    def calculate_position_size(self, 
                              signal: float, 
                              symbol: str,
                              portfolio_value: float,
                              risk_per_trade: float = 0.02) -> float:
        """
        Calculate the position size based on the signal strength and risk parameters.
        
        Args:
            signal: Trading signal strength (-1.0 to 1.0)
            symbol: Trading symbol
            portfolio_value: Current portfolio value
            risk_per_trade: Maximum risk per trade as a fraction of portfolio
            
        Returns:
            Position size in base currency
        """
        max_position = portfolio_value * risk_per_trade
        position_size = max_position * abs(signal)
        return position_size if signal > 0 else -position_size
    
    def update_positions(self, 
                        signals: Dict[str, float],
                        portfolio_value: float) -> Dict[str, float]:
        """
        Update strategy positions based on new signals.
        
        Args:
            signals: Dictionary mapping symbol to its signal
            portfolio_value: Current portfolio value
            
        Returns:
            Dictionary mapping symbol to its target position size
        """
        new_positions = {}
        for symbol, signal in signals.items():
            new_positions[symbol] = self.calculate_position_size(
                signal, symbol, portfolio_value
            )
        self.positions = new_positions
        return new_positions
    
    def get_required_timeframes(self) -> List[str]:
        """
        Get the timeframes required by this strategy.
        
        Returns:
            List of required timeframe strings (e.g., ["1m", "5m", "1h"])
        """
        return ["1m"]  # Default to 1-minute timeframe
    
    def get_required_symbols(self) -> List[str]:
        """
        Get the symbols required by this strategy.
        
        Returns:
            List of required trading symbols
        """
        return self.symbols
    
    def get_parameters(self) -> Dict[str, Union[float, int, str]]:
        """
        Get the strategy's current parameters.
        
        Returns:
            Dictionary of strategy parameters
        """
        return self.parameters
    
    def set_parameters(self, parameters: Dict[str, Union[float, int, str]]) -> None:
        """
        Update the strategy's parameters.
        
        Args:
            parameters: New parameter values
        """
        self.parameters.update(parameters)
        
    def __str__(self) -> str:
        """String representation of the strategy."""
        return f"{self.name} Strategy (Symbols: {', '.join(self.symbols)})" 