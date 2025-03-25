from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from src.core.strategy import Strategy

class MovingAverageCross(Strategy):
    """
    Moving Average Crossover strategy that generates trading signals based on
    the crossing of two moving averages with different periods.
    """
    
    def __init__(self,
                 name: str = "MA_Cross",
                 symbols: List[str] = None,
                 fast_period: int = 10,
                 slow_period: int = 30,
                 signal_threshold: float = 0.0):
        """
        Initialize the Moving Average Crossover strategy.
        
        Args:
            name: Strategy name
            symbols: List of symbols to trade
            fast_period: Period for the fast moving average
            slow_period: Period for the slow moving average
            signal_threshold: Minimum difference between MAs to generate signal
        """
        parameters = {
            "fast_period": fast_period,
            "slow_period": slow_period,
            "signal_threshold": signal_threshold
        }
        super().__init__(name=name, parameters=parameters, symbols=symbols)
        
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Generate trading signals for each symbol based on MA crossover.
        
        Args:
            data: Dictionary mapping symbols to their market data
            
        Returns:
            Dictionary mapping symbols to their trading signals (-1.0 to 1.0)
        """
        if not self.validate_data(data):
            return {}
            
        signals = {}
        fast_period = self.parameters["fast_period"]
        slow_period = self.parameters["slow_period"]
        threshold = self.parameters["signal_threshold"]
        
        for symbol, df in data.items():
            if len(df) < slow_period:
                continue
                
            # Calculate moving averages
            fast_ma = df['close'].rolling(window=fast_period).mean()
            slow_ma = df['close'].rolling(window=slow_period).mean()
            
            # Calculate the difference between MAs
            ma_diff = (fast_ma - slow_ma) / df['close']
            
            # Generate signal based on MA difference
            if abs(ma_diff.iloc[-1]) > threshold:
                signal = np.clip(ma_diff.iloc[-1], -1.0, 1.0)
            else:
                signal = 0.0
                
            # Add momentum factor
            momentum = self._calculate_momentum(df)
            signal *= momentum
            
            signals[symbol] = signal
            
        return signals
    
    def _calculate_momentum(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate a momentum factor to adjust signal strength.
        
        Args:
            df: Market data DataFrame
            period: Lookback period for momentum calculation
            
        Returns:
            Momentum factor between 0.0 and 1.0
        """
        if len(df) < period:
            return 1.0
            
        # Calculate returns over the period
        returns = df['close'].pct_change(period).iloc[-1]
        
        # Calculate volatility
        volatility = df['returns'].rolling(window=period).std().iloc[-1]
        
        # Adjust momentum by volatility
        momentum = returns / (volatility + 1e-6)
        
        # Scale momentum to [0, 1] range
        momentum = 1.0 / (1.0 + np.exp(-momentum))  # Sigmoid function
        
        return momentum
    
    def get_required_timeframes(self) -> List[str]:
        """
        Get the timeframes required by this strategy.
        
        Returns:
            List of required timeframe strings
        """
        return ["1d"]  # Daily timeframe for MA calculation
    
    def get_min_history(self) -> int:
        """
        Get the minimum number of historical periods needed.
        
        Returns:
            Minimum number of periods
        """
        return max(
            self.parameters["slow_period"],
            self.parameters["fast_period"]
        ) + 20  # Additional periods for momentum calculation
    
    def __str__(self) -> str:
        """String representation of the strategy."""
        return (
            f"Moving Average Crossover Strategy "
            f"(Fast: {self.parameters['fast_period']}, "
            f"Slow: {self.parameters['slow_period']})"
        ) 