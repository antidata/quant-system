from typing import Dict, List, Optional, Union, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from src.core.strategy import Strategy
from src.data.market_data import MarketData
from src.risk.risk_manager import RiskManager

class BacktestEngine:
    """
    Backtesting engine for evaluating trading strategies using historical data.
    Implements realistic trading simulation with transaction costs and slippage.
    """
    
    def __init__(self,
                 strategy: Strategy,
                 initial_capital: float = 100000.0,
                 start_date: Union[str, datetime] = None,
                 end_date: Union[str, datetime] = None,
                 transaction_cost: float = 0.001,
                 slippage: float = 0.001):
        """
        Initialize the backtesting engine.
        
        Args:
            strategy: Trading strategy to test
            initial_capital: Initial capital for the backtest
            start_date: Start date for the backtest
            end_date: End date for the backtest
            transaction_cost: Transaction cost as a fraction of trade value
            slippage: Slippage as a fraction of price
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.start_date = pd.to_datetime(start_date) if start_date else None
        self.end_date = pd.to_datetime(end_date) if end_date else None
        self.transaction_cost = transaction_cost
        self.slippage = slippage
        
        self.market_data = MarketData()
        self.risk_manager = RiskManager(
            initial_capital=initial_capital,
            max_position_size=0.2,
            max_portfolio_risk=0.02
        )
        
        self.positions: Dict[str, float] = {}
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []
        self.logger = logging.getLogger(__name__)
        
    def run(self) -> Dict[str, Any]:
        """
        Run the backtest.
        
        Returns:
            Dictionary containing backtest results and performance metrics
        """
        # Fetch historical data
        data = self.market_data.fetch_data(
            symbols=self.strategy.get_required_symbols(),
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.strategy.get_required_timeframes()[0]
        )
        
        if not data:
            self.logger.error("Failed to fetch market data")
            return {}
            
        # Initialize results tracking
        current_capital = self.initial_capital
        self.equity_curve = [current_capital]
        
        # Get the common date range across all symbols
        dates = self._get_common_dates(data)
        
        # Main backtest loop
        for date in dates:
            # Get current market data
            current_data = self._get_data_slice(data, date)
            
            # Generate trading signals
            signals = self.strategy.generate_signals(current_data)
            
            # Execute trades
            for symbol, signal in signals.items():
                if abs(signal) > 0:
                    # Calculate position size
                    price = current_data[symbol]['close'].iloc[-1]
                    volatility = current_data[symbol]['volatility'].iloc[-1]
                    
                    position_size = self.risk_manager.calculate_position_size(
                        symbol=symbol,
                        signal=signal,
                        price=price,
                        volatility=volatility
                    )
                    
                    # Check risk limits
                    if self.risk_manager.check_portfolio_risk(
                        self.positions, 
                        {s: d['returns'] for s, d in current_data.items()}
                    ):
                        # Execute trade
                        self._execute_trade(
                            symbol=symbol,
                            size=position_size,
                            price=price,
                            date=date
                        )
            
            # Update equity curve
            current_capital = self._calculate_portfolio_value(current_data)
            self.equity_curve.append(current_capital)
            
        # Calculate performance metrics
        return self._calculate_performance_metrics()
    
    def _get_common_dates(self, data: Dict[str, pd.DataFrame]) -> pd.DatetimeIndex:
        """
        Get the common date range across all symbols.
        
        Args:
            data: Dictionary of market data for each symbol
            
        Returns:
            DatetimeIndex of common dates
        """
        common_dates = None
        for df in data.values():
            if common_dates is None:
                common_dates = df.index
            else:
                common_dates = common_dates.intersection(df.index)
        return common_dates
    
    def _get_data_slice(self,
                       data: Dict[str, pd.DataFrame],
                       date: pd.Timestamp) -> Dict[str, pd.DataFrame]:
        """
        Get market data slice up to the given date.
        
        Args:
            data: Dictionary of market data
            date: Current date
            
        Returns:
            Dictionary of market data slices
        """
        return {
            symbol: df[df.index <= date]
            for symbol, df in data.items()
        }
    
    def _execute_trade(self,
                      symbol: str,
                      size: float,
                      price: float,
                      date: pd.Timestamp) -> None:
        """
        Execute a trade with transaction costs and slippage.
        
        Args:
            symbol: Trading symbol
            size: Position size
            price: Current price
            date: Trade date
        """
        # Calculate transaction costs
        old_size = self.positions.get(symbol, 0.0)
        size_delta = size - old_size
        
        if size_delta == 0:
            return
            
        # Apply slippage
        executed_price = price * (1 + np.sign(size_delta) * self.slippage)
        
        # Calculate transaction cost
        transaction_cost = abs(size_delta * executed_price * self.transaction_cost)
        
        # Record trade
        self.trades.append({
            "date": date,
            "symbol": symbol,
            "size": size_delta,
            "price": executed_price,
            "transaction_cost": transaction_cost
        })
        
        # Update position
        self.positions[symbol] = size
        if self.positions[symbol] == 0:
            del self.positions[symbol]
            
        # Update risk manager
        self.risk_manager.update_position(symbol, size, executed_price)
    
    def _calculate_portfolio_value(self, current_data: Dict[str, pd.DataFrame]) -> float:
        """
        Calculate current portfolio value.
        
        Args:
            current_data: Current market data
            
        Returns:
            Current portfolio value
        """
        portfolio_value = self.risk_manager.current_capital
        
        for symbol, position in self.positions.items():
            if symbol in current_data:
                price = current_data[symbol]['close'].iloc[-1]
                portfolio_value += position * price
                
        return portfolio_value
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """
        Calculate backtest performance metrics.
        
        Returns:
            Dictionary of performance metrics
        """
        equity_curve = pd.Series(self.equity_curve)
        returns = equity_curve.pct_change().dropna()
        
        # Calculate metrics
        total_return = (equity_curve.iloc[-1] - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = annual_return / volatility if volatility != 0 else 0
        
        drawdown = (equity_curve - equity_curve.expanding().max()) / equity_curve.expanding().max()
        max_drawdown = abs(drawdown.min())
        
        # Calculate trade metrics
        trade_df = pd.DataFrame(self.trades)
        if not trade_df.empty:
            profitable_trades = len(trade_df[trade_df['size'] > 0])
            total_trades = len(trade_df)
            win_rate = profitable_trades / total_trades if total_trades > 0 else 0
            avg_trade_return = trade_df['size'].mean()
        else:
            win_rate = 0
            avg_trade_return = 0
            
        return {
            "total_return": total_return,
            "annual_return": annual_return,
            "volatility": volatility,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "win_rate": win_rate,
            "avg_trade_return": avg_trade_return,
            "total_trades": len(self.trades),
            "final_capital": self.equity_curve[-1],
            "equity_curve": self.equity_curve
        } 