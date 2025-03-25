from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from src.core.strategy import Strategy

class RSIMeanReversion(Strategy):
    """
    RSI Mean Reversion strategy that generates trading signals based on
    RSI (Relative Strength Index) overbought/oversold conditions.
    """
    
    def __init__(self,
                 name: str = "RSI_MR",
                 symbols: List[str] = None,
                 rsi_period: int = 14,
                 oversold: int = 30,
                 overbought: int = 70):
        """
        Initialize the RSI Mean Reversion strategy.
        
        Args:
            name: Strategy name
            symbols: List of symbols to trade
            rsi_period: Period for RSI calculation
            oversold: RSI level below which to generate buy signals
            overbought: RSI level above which to generate sell signals
        """
        parameters = {
            "rsi_period": rsi_period,
            "oversold": oversold,
            "overbought": overbought
        }
        super().__init__(name=name, parameters=parameters, symbols=symbols)
    
    def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Generate trading signals based on RSI values.
        
        Args:
            data: Dictionary mapping symbols to their market data
            
        Returns:
            Dictionary mapping symbols to their trading signals (-1.0 to 1.0)
        """
        if not self.validate_data(data):
            return {}
            
        signals = {}
        rsi_period = self.parameters["rsi_period"]
        oversold = self.parameters["oversold"]
        overbought = self.parameters["overbought"]
        
        for symbol, df in data.items():
            if len(df) < rsi_period:
                continue
                
            # Calculate RSI
            rsi = self._calculate_rsi(df['close'], rsi_period)
            
            # Generate signal based on RSI value
            last_rsi = rsi.iloc[-1]
            
            if last_rsi < oversold:
                # Strong buy signal when oversold
                signal = 1.0
            elif last_rsi > overbought:
                # Strong sell signal when overbought
                signal = -1.0
            else:
                # Scale signal between oversold and overbought levels
                # Center around 50 and normalize to [-1, 1]
                signal = -(last_rsi - 50) / (overbought - oversold) * 2
                signal = np.clip(signal, -1.0, 1.0)
            
            signals[symbol] = signal
            
        return signals
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate the RSI technical indicator.
        
        Args:
            prices: Price series
            period: RSI period
            
        Returns:
            RSI values as a pandas Series
        """
        # Calculate price changes
        delta = prices.diff()
        
        # Separate gains and losses
        gains = delta.copy()
        losses = delta.copy()
        gains[gains < 0] = 0
        losses[losses > 0] = 0
        losses = abs(losses)
        
        # Calculate average gains and losses
        avg_gains = gains.ewm(alpha=1/period, min_periods=period).mean()
        avg_losses = losses.ewm(alpha=1/period, min_periods=period).mean()
        
        # Calculate RS and RSI
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        
        # Handle edge cases
        rsi = rsi.fillna(50)  # Fill NaN with neutral value
        rsi = rsi.clip(0, 100)  # Ensure RSI is between 0 and 100
        
        return rsi
    
    def get_required_timeframes(self) -> List[str]:
        """
        Get the timeframes required by this strategy.
        
        Returns:
            List of required timeframe strings
        """
        return ["1d"]  # Daily timeframe for RSI calculation
    
    def get_min_history(self) -> int:
        """
        Get the minimum number of historical periods needed.
        
        Returns:
            Minimum number of periods
        """
        return self.parameters["rsi_period"] * 2  # Need extra periods for reliable RSI 