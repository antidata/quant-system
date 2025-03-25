import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.datasets import make_classification
import talib

print('All packages imported successfully!')

# Test basic functionality
data = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
sma = talib.SMA(data, timeperiod=3)  # 3-period simple moving average
print('\nTest calculations:')
print(f'Input data: {data}')
print(f'3-period Simple Moving Average: {sma}') 