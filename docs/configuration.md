# Configuration and Deployment Guide

This guide explains how to configure and deploy the Quantitative Trading System.

## Configuration

### Environment Setup

1. Environment Variables
```bash
# .env file
# API Keys
ALPHA_VANTAGE_API_KEY=your_key_here
YAHOO_FINANCE_API_KEY=your_key_here
IEX_CLOUD_API_KEY=your_key_here

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quant_system
DB_USER=quant_user
DB_PASSWORD=your_password_here

# Trading Parameters
INITIAL_CAPITAL=100000
MAX_POSITION_SIZE=0.1
RISK_FREE_RATE=0.02
TRANSACTION_COST=0.001

# Risk Management
MAX_DRAWDOWN=0.2
STOP_LOSS_PCT=0.05
TRAILING_STOP_PCT=0.1
VAR_CONFIDENCE=0.95

# System Configuration
LOG_LEVEL=INFO
DATA_CACHE_DIR=/path/to/cache
RESULTS_DIR=/path/to/results
```

2. Configuration Class
```python
class SystemConfig:
    def __init__(self, config_file: str = '.env'):
        """
        Initialize system configuration.
        """
        self.config = self.load_config(config_file)
        self.validate_config()
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from file.
        """
        config = {}
        
        # Load environment variables
        load_dotenv(config_file)
        
        # Trading parameters
        config['initial_capital'] = float(os.getenv('INITIAL_CAPITAL'))
        config['max_position_size'] = float(os.getenv('MAX_POSITION_SIZE'))
        config['risk_free_rate'] = float(os.getenv('RISK_FREE_RATE'))
        config['transaction_cost'] = float(os.getenv('TRANSACTION_COST'))
        
        # Risk parameters
        config['max_drawdown'] = float(os.getenv('MAX_DRAWDOWN'))
        config['stop_loss_pct'] = float(os.getenv('STOP_LOSS_PCT'))
        config['trailing_stop_pct'] = float(os.getenv('TRAILING_STOP_PCT'))
        config['var_confidence'] = float(os.getenv('VAR_CONFIDENCE'))
        
        return config
    
    def validate_config(self):
        """
        Validate configuration parameters.
        """
        # Validate trading parameters
        assert self.config['initial_capital'] > 0
        assert 0 < self.config['max_position_size'] <= 1
        assert 0 <= self.config['risk_free_rate'] <= 1
        assert 0 <= self.config['transaction_cost'] <= 0.1
        
        # Validate risk parameters
        assert 0 < self.config['max_drawdown'] <= 1
        assert 0 < self.config['stop_loss_pct'] <= 1
        assert 0 < self.config['trailing_stop_pct'] <= 1
        assert 0 < self.config['var_confidence'] < 1
```

### Strategy Configuration

1. Strategy Parameters
```python
class StrategyConfig:
    def __init__(self, strategy_name: str):
        """
        Initialize strategy configuration.
        """
        self.strategy_name = strategy_name
        self.params = self.load_strategy_params()
    
    def load_strategy_params(self) -> Dict[str, Any]:
        """
        Load strategy-specific parameters.
        """
        # Load from configuration file
        config_path = f'config/strategies/{self.strategy_name}.yaml'
        with open(config_path, 'r') as f:
            params = yaml.safe_load(f)
        
        return params
    
    def update_params(self, new_params: Dict[str, Any]):
        """
        Update strategy parameters.
        """
        self.params.update(new_params)
        self.save_params()
    
    def save_params(self):
        """
        Save strategy parameters.
        """
        config_path = f'config/strategies/{self.strategy_name}.yaml'
        with open(config_path, 'w') as f:
            yaml.dump(self.params, f)
```

2. Example Strategy Configuration
```yaml
# config/strategies/moving_average_cross.yaml
name: MovingAverageCross
parameters:
  short_window: 20
  long_window: 50
  risk_per_trade: 0.02
  entry_threshold: 0.001
  exit_threshold: 0.001
risk_management:
  stop_loss: 0.05
  trailing_stop: 0.1
  max_position_size: 0.1
  max_correlation: 0.7
filters:
  min_volume: 1000000
  min_price: 5.0
  max_spread: 0.02
```

## Deployment

### Local Deployment

1. Development Environment
```python
class DevelopmentEnvironment:
    def __init__(self):
        """
        Initialize development environment.
        """
        self.config = SystemConfig()
        self.setup_logging()
        self.setup_database()
        self.setup_cache()
    
    def setup_logging(self):
        """
        Configure logging for development.
        """
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def setup_database(self):
        """
        Setup development database.
        """
        # Use SQLite for development
        self.db_path = 'data/development.db'
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        
    def setup_cache(self):
        """
        Setup data cache for development.
        """
        self.cache_dir = 'data/cache'
        os.makedirs(self.cache_dir, exist_ok=True)
```

2. Production Environment
```python
class ProductionEnvironment:
    def __init__(self):
        """
        Initialize production environment.
        """
        self.config = SystemConfig()
        self.setup_logging()
        self.setup_database()
        self.setup_monitoring()
    
    def setup_logging(self):
        """
        Configure logging for production.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/production.log'),
                logging.StreamHandler()
            ]
        )
    
    def setup_database(self):
        """
        Setup production database.
        """
        db_url = (f"postgresql://{self.config['DB_USER']}:"
                 f"{self.config['DB_PASSWORD']}@{self.config['DB_HOST']}:"
                 f"{self.config['DB_PORT']}/{self.config['DB_NAME']}")
        self.engine = create_engine(db_url)
    
    def setup_monitoring(self):
        """
        Setup production monitoring.
        """
        # Initialize monitoring tools
        self.setup_prometheus()
        self.setup_grafana()
```

### Docker Deployment

1. Dockerfile
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "src/main.py"]
```

2. Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  trading_system:
    build: .
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=quant_system
      - DB_USER=quant_user
      - DB_PASSWORD=your_password_here
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis

  postgres:
    image: postgres:13
    environment:
      - POSTGRES_DB=quant_system
      - POSTGRES_USER=quant_user
      - POSTGRES_PASSWORD=your_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Cloud Deployment

1. AWS Deployment
```python
class AWSDeployment:
    def __init__(self):
        """
        Initialize AWS deployment.
        """
        self.setup_aws_resources()
        self.setup_monitoring()
    
    def setup_aws_resources(self):
        """
        Setup AWS resources.
        """
        # Initialize AWS clients
        self.ec2 = boto3.client('ec2')
        self.rds = boto3.client('rds')
        self.s3 = boto3.client('s3')
        
        # Create EC2 instance
        self.create_ec2_instance()
        
        # Create RDS database
        self.create_rds_instance()
        
        # Create S3 buckets
        self.create_s3_buckets()
    
    def setup_monitoring(self):
        """
        Setup AWS monitoring.
        """
        # Setup CloudWatch
        self.cloudwatch = boto3.client('cloudwatch')
        
        # Setup alerts
        self.setup_cloudwatch_alerts()
```

2. Kubernetes Deployment
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: trading-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: trading-system
  template:
    metadata:
      labels:
        app: trading-system
    spec:
      containers:
      - name: trading-system
        image: trading-system:latest
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: trading-system-config
              key: db_host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: trading-system-secrets
              key: db_password
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
```

## Monitoring

### System Monitoring

1. Performance Monitoring
```python
class SystemMonitor:
    def __init__(self):
        """
        Initialize system monitoring.
        """
        self.setup_metrics()
        self.setup_alerts()
    
    def setup_metrics(self):
        """
        Setup system metrics.
        """
        # CPU usage
        self.cpu_gauge = Gauge('cpu_usage_percent', 'CPU usage in percent')
        
        # Memory usage
        self.memory_gauge = Gauge('memory_usage_bytes', 'Memory usage in bytes')
        
        # Disk usage
        self.disk_gauge = Gauge('disk_usage_percent', 'Disk usage in percent')
        
        # Network metrics
        self.network_in = Counter('network_in_bytes', 'Network in bytes')
        self.network_out = Counter('network_out_bytes', 'Network out bytes')
    
    def collect_metrics(self):
        """
        Collect system metrics.
        """
        # Update CPU metrics
        cpu_percent = psutil.cpu_percent()
        self.cpu_gauge.set(cpu_percent)
        
        # Update memory metrics
        memory = psutil.virtual_memory()
        self.memory_gauge.set(memory.used)
        
        # Update disk metrics
        disk = psutil.disk_usage('/')
        self.disk_gauge.set(disk.percent)
```

2. Application Monitoring
```python
class ApplicationMonitor:
    def __init__(self):
        """
        Initialize application monitoring.
        """
        self.setup_metrics()
        self.setup_logging()
    
    def setup_metrics(self):
        """
        Setup application metrics.
        """
        # Trading metrics
        self.trades_counter = Counter('trades_total', 'Total number of trades')
        self.position_gauge = Gauge('position_size', 'Current position size')
        
        # Performance metrics
        self.returns_gauge = Gauge('returns_percent', 'Returns in percent')
        self.sharpe_gauge = Gauge('sharpe_ratio', 'Current Sharpe ratio')
        
        # Error metrics
        self.error_counter = Counter('errors_total', 'Total number of errors')
    
    def log_metrics(self):
        """
        Log application metrics.
        """
        metrics = {
            'trades': self.trades_counter._value.get(),
            'position': self.position_gauge._value.get(),
            'returns': self.returns_gauge._value.get(),
            'sharpe': self.sharpe_gauge._value.get(),
            'errors': self.error_counter._value.get()
        }
        
        logging.info(f"Application metrics: {metrics}")
```

## Best Practices

1. Configuration Management
   - Use environment variables
   - Implement configuration validation
   - Maintain separate configs for environments
   - Document all configuration options

2. Deployment Process
   - Use version control
   - Implement CI/CD pipeline
   - Maintain deployment documentation
   - Test deployment process

3. Monitoring and Logging
   - Monitor system resources
   - Track application metrics
   - Implement proper logging
   - Set up alerts

4. Security
   - Secure sensitive data
   - Implement authentication
   - Regular security updates
   - Audit system access

5. Maintenance
   - Regular backups
   - System updates
   - Performance optimization
   - Documentation updates 