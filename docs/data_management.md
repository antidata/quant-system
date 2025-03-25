# Data Management Guide

This guide explains how to handle market data and manage data processing in the Quantitative Trading System.

## Market Data

### Data Sources

The system supports multiple data sources:

1. Yahoo Finance (via yfinance)
```python
from src.data.market_data import YahooFinanceData

# Initialize data source
yahoo_data = YahooFinanceData()

# Fetch historical data
data = yahoo_data.get_historical_data(
    symbols=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2023-12-31',
    interval='1d'
)

# Get real-time data
real_time_data = yahoo_data.get_real_time_data(['AAPL', 'MSFT'])
```

2. Alpha Vantage
```python
from src.data.market_data import AlphaVantageData

# Initialize with API key
alpha_vantage = AlphaVantageData(api_key='YOUR_API_KEY')

# Get historical data
data = alpha_vantage.get_historical_data(
    symbol='AAPL',
    interval='daily',
    output_size='full'
)

# Get technical indicators
sma = alpha_vantage.get_technical_indicator(
    symbol='AAPL',
    indicator='SMA',
    interval='daily',
    time_period=20
)
```

3. Custom Data Source
```python
class CustomDataSource:
    def __init__(self, connection_params: Dict[str, Any]):
        self.connection = self.establish_connection(connection_params)
    
    def get_historical_data(self,
                          symbols: List[str],
                          start_date: str,
                          end_date: str) -> pd.DataFrame:
        """
        Fetch historical data from custom source.
        """
        query = self.build_query(symbols, start_date, end_date)
        data = self.connection.execute(query)
        return self.process_data(data)
    
    def process_data(self, raw_data: Any) -> pd.DataFrame:
        """
        Process raw data into standardized format.
        """
        df = pd.DataFrame(raw_data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        return df
```

### Data Processing

1. Data Cleaning
```python
def clean_market_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Clean market data by handling missing values and outliers.
    """
    # Handle missing values
    data = data.fillna(method='ffill')  # Forward fill
    data = data.fillna(method='bfill')  # Backward fill
    
    # Remove outliers
    for column in ['open', 'high', 'low', 'close', 'volume']:
        if column in data.columns:
            mean = data[column].mean()
            std = data[column].std()
            data[column] = data[column].clip(
                lower=mean - 3*std,
                upper=mean + 3*std
            )
    
    return data
```

2. Feature Engineering
```python
def engineer_features(data: pd.DataFrame) -> pd.DataFrame:
    """
    Create technical indicators and features.
    """
    # Calculate returns
    data['returns'] = data['close'].pct_change()
    data['log_returns'] = np.log(1 + data['returns'])
    
    # Calculate volatility
    data['volatility'] = data['returns'].rolling(window=20).std()
    
    # Add technical indicators
    data['sma_20'] = data['close'].rolling(window=20).mean()
    data['sma_50'] = data['close'].rolling(window=50).mean()
    data['rsi'] = calculate_rsi(data['close'], period=14)
    
    return data
```

3. Data Normalization
```python
def normalize_data(data: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize data for machine learning models.
    """
    scaler = StandardScaler()
    
    # Select numerical columns
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    
    # Normalize each column
    data[numeric_cols] = scaler.fit_transform(data[numeric_cols])
    
    return data
```

## Data Storage

### Database Management

1. SQL Database
```python
class MarketDatabase:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
    
    def save_market_data(self, 
                        data: pd.DataFrame,
                        table_name: str,
                        if_exists: str = 'append'):
        """
        Save market data to database.
        """
        data.to_sql(
            table_name,
            self.engine,
            if_exists=if_exists,
            index=True
        )
    
    def load_market_data(self,
                        table_name: str,
                        start_date: str,
                        end_date: str) -> pd.DataFrame:
        """
        Load market data from database.
        """
        query = f"""
        SELECT *
        FROM {table_name}
        WHERE datetime BETWEEN '{start_date}' AND '{end_date}'
        """
        return pd.read_sql(query, self.engine, index_col='datetime')
```

2. Time Series Database
```python
class TSDatabase:
    def __init__(self, host: str, port: int):
        self.client = InfluxDBClient(host=host, port=port)
    
    def write_data(self,
                   measurement: str,
                   data: pd.DataFrame,
                   tags: Dict[str, str]):
        """
        Write data to time series database.
        """
        points = []
        for timestamp, row in data.iterrows():
            point = {
                "measurement": measurement,
                "tags": tags,
                "time": timestamp,
                "fields": row.to_dict()
            }
            points.append(point)
        
        self.client.write_points(points)
    
    def query_data(self,
                   measurement: str,
                   start_time: str,
                   end_time: str) -> pd.DataFrame:
        """
        Query data from time series database.
        """
        query = f"""
        SELECT *
        FROM {measurement}
        WHERE time >= '{start_time}' AND time <= '{end_time}'
        """
        result = self.client.query(query)
        return pd.DataFrame(result.get_points())
```

## Data Quality

### Quality Checks

1. Data Validation
```python
def validate_market_data(data: pd.DataFrame) -> bool:
    """
    Validate market data quality.
    """
    checks = {
        'missing_values': check_missing_values(data),
        'price_continuity': check_price_continuity(data),
        'volume_validity': check_volume_validity(data),
        'timestamp_sequence': check_timestamp_sequence(data)
    }
    
    return all(checks.values())

def check_missing_values(data: pd.DataFrame) -> bool:
    """
    Check for missing values.
    """
    missing_pct = data.isnull().mean()
    return all(missing_pct < 0.05)  # Less than 5% missing

def check_price_continuity(data: pd.DataFrame) -> bool:
    """
    Check for price jumps/gaps.
    """
    returns = data['close'].pct_change()
    return all(abs(returns) < 0.2)  # No jumps > 20%

def check_volume_validity(data: pd.DataFrame) -> bool:
    """
    Check volume data validity.
    """
    return all(data['volume'] >= 0)

def check_timestamp_sequence(data: pd.DataFrame) -> bool:
    """
    Check timestamp sequence validity.
    """
    timestamps = data.index
    return all(timestamps[i] < timestamps[i+1] 
              for i in range(len(timestamps)-1))
```

2. Data Monitoring
```python
class DataMonitor:
    def __init__(self):
        self.alerts = []
    
    def monitor_data_quality(self, data: pd.DataFrame):
        """
        Monitor data quality metrics.
        """
        metrics = {
            'missing_rate': data.isnull().mean(),
            'update_frequency': self.calculate_update_frequency(data),
            'data_latency': self.calculate_data_latency(data)
        }
        
        self.check_thresholds(metrics)
    
    def check_thresholds(self, metrics: Dict[str, float]):
        """
        Check if metrics exceed thresholds.
        """
        if metrics['missing_rate'].max() > 0.05:
            self.alerts.append("High missing data rate detected")
        
        if metrics['data_latency'] > 60:
            self.alerts.append("High data latency detected")
```

## Best Practices

1. Data Collection
   - Use reliable data sources
   - Implement proper error handling
   - Set up data quality checks
   - Monitor data collection process

2. Data Processing
   - Clean data systematically
   - Document cleaning procedures
   - Validate processed data
   - Maintain data consistency

3. Data Storage
   - Choose appropriate storage solution
   - Implement backup procedures
   - Monitor storage capacity
   - Optimize query performance

4. Data Access
   - Implement proper authentication
   - Control data access permissions
   - Log data access attempts
   - Monitor API usage

5. Data Documentation
   - Document data sources
   - Maintain data dictionaries
   - Record data transformations
   - Track data lineage 