import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from src.strategies.moving_average_cross import MovingAverageCross
from src.backtesting.engine import BacktestEngine

def main():
    # Create a moving average crossover strategy
    strategy = MovingAverageCross(
        name="MA_Cross_Demo",
        symbols=["AAPL", "GOOGL", "MSFT"],
        fast_period=10,
        slow_period=30,
        signal_threshold=0.001
    )
    
    # Set up the backtesting engine
    engine = BacktestEngine(
        strategy=strategy,
        initial_capital=100000.0,
        start_date=datetime.now() - timedelta(days=365),
        end_date=datetime.now(),
        transaction_cost=0.001,
        slippage=0.001
    )
    
    # Run the backtest
    results = engine.run()
    
    if not results:
        print("Backtest failed to run")
        return
        
    # Print performance metrics
    print("\nBacktest Results:")
    print("-" * 40)
    print(f"Total Return: {results['total_return']:.2%}")
    print(f"Annual Return: {results['annual_return']:.2%}")
    print(f"Sharpe Ratio: {results['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"Win Rate: {results['win_rate']:.2%}")
    print(f"Total Trades: {results['total_trades']}")
    print(f"Final Capital: ${results['final_capital']:,.2f}")
    
    # Plot equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(results['equity_curve'])
    plt.title('Portfolio Equity Curve')
    plt.xlabel('Trading Days')
    plt.ylabel('Portfolio Value ($)')
    plt.grid(True)
    plt.show()

if __name__ == "__main__":
    main() 