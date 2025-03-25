from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

class MarketData:
    """
    Market data handler responsible for fetching and preprocessing financial data.
    Supports multiple data sources and provides a unified interface for data access.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize the market data handler.
        
        Args:
            cache_dir: Directory to store cached data
        """
        self.cache_dir = cache_dir
        self.data_cache: Dict[str, pd.DataFrame] = {}
        self.logger = logging.getLogger(__name__)
        
    def fetch_data(self,
                   symbols: List[str],
                   start_date: Union[str, datetime],
                   end_date: Union[str, datetime],
                   interval: str = "1d",
                   source: str = "yfinance") -> Dict[str, pd.DataFrame]:
        """
        Fetch market data for multiple symbols.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date for data fetch
            end_date: End date for data fetch
            interval: Data interval (e.g., "1m", "1h", "1d")
            source: Data source to use
            
        Returns:
            Dictionary mapping symbols to their respective DataFrames
        """
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)
            
        # Use ThreadPoolExecutor for parallel data fetching
        with ThreadPoolExecutor(max_workers=min(len(symbols), 10)) as executor:
            fetch_func = partial(
                self._fetch_single_symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                source=source
            )
            results = list(executor.map(fetch_func, symbols))
            
        return {symbol: df for symbol, df in zip(symbols, results) if df is not None}
    
    def _fetch_single_symbol(self,
                           symbol: str,
                           start_date: datetime,
                           end_date: datetime,
                           interval: str,
                           source: str) -> Optional[pd.DataFrame]:
        """
        Fetch data for a single symbol.
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval
            source: Data source
            
        Returns:
            DataFrame containing the market data
        """
        try:
            if source == "yfinance":
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date,
                    end=end_date,
                    interval=interval
                )
                df.columns = [col.lower() for col in df.columns]
                return self._preprocess_data(df)
            else:
                raise ValueError(f"Unsupported data source: {source}")
                
        except Exception as e:
            self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
            return None
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess the raw market data.
        
        Args:
            df: Raw market data DataFrame
            
        Returns:
            Preprocessed DataFrame
        """
        # Handle missing values
        df = df.fillna(method='ffill')
        
        # Add basic technical indicators
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        df['volatility'] = df['returns'].rolling(window=20).std()
        
        # Add volume indicators
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_std'] = df['volume'].rolling(window=20).std()
        
        # Add price indicators
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        df['ma_200'] = df['close'].rolling(window=200).mean()
        
        return df
    
    def get_latest_data(self,
                       symbols: List[str],
                       lookback_periods: int = 100,
                       interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Get the most recent market data.
        
        Args:
            symbols: List of trading symbols
            lookback_periods: Number of historical periods to fetch
            interval: Data interval
            
        Returns:
            Dictionary mapping symbols to their latest data
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_periods)
        return self.fetch_data(symbols, start_date, end_date, interval)
    
    def cache_data(self, symbol: str, data: pd.DataFrame) -> None:
        """
        Cache market data for faster access.
        
        Args:
            symbol: Trading symbol
            data: Market data DataFrame
        """
        self.data_cache[symbol] = data
        
    def get_cached_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """
        Retrieve cached market data.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Cached DataFrame if available, None otherwise
        """
        return self.data_cache.get(symbol)
    
    def clear_cache(self) -> None:
        """Clear the data cache."""
        self.data_cache.clear() 