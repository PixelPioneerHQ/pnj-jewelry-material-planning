# Configuration Templates & Examples

## Jewelry Material Planning System - Configuration Reference

This document provides configuration templates, examples, and best practices for different deployment scenarios.

---

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [BigQuery Configuration](#bigquery-configuration)
3. [Docker Configuration](#docker-configuration)
4. [Optimization Parameters](#optimization-parameters)
5. [Monitoring & Logging](#monitoring--logging)
6. [Security Configuration](#security-configuration)
7. [Performance Tuning](#performance-tuning)

---

## Environment Configuration

### Production Environment Template

```bash
# config/production.env
# ====================================
# Production Configuration Template
# ====================================

# =============================================================================
# Google Cloud Platform Configuration
# =============================================================================
GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json
PROJECT_ID=pnj-material-planing
DATASET_ID=PRODUCTION_MRP
BQ_LOCATION=asia-southeast1
BQ_TIMEOUT=600

# =============================================================================
# Optimization Engine Parameters
# =============================================================================
SOLVER_ENGINE=SCIP
SOLVER_GAP=0.001
SOLVER_TIMEOUT=3600
MAX_ITERATIONS=10000
PARALLEL_THREADS=4

# =============================================================================
# Application Performance
# =============================================================================
MEMORY_LIMIT=8G
CPU_LIMIT=4
MAX_RETRIES=3
RETRY_DELAY_MIN=5
RETRY_DELAY_MAX=10
BATCH_SIZE=5000

# =============================================================================
# Data Processing
# =============================================================================
CHUNK_SIZE=1000
PARALLEL_JOBS=2
CACHE_ENABLED=true
CACHE_TTL=3600

# =============================================================================
# Logging & Monitoring
# =============================================================================
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/docker-application/logs/jewelry-mrp.log
METRICS_ENABLED=true
METRICS_PORT=8080
METRICS_PATH=/metrics

# =============================================================================
# Error Handling
# =============================================================================
FAIL_FAST=false
CONTINUE_ON_WARNING=true
ERROR_THRESHOLD=10
VALIDATION_STRICT=true

# =============================================================================
# Business Rules
# =============================================================================
MIN_COMPONENT_QTY=0.001
MAX_PRODUCT_ALLOCATION=999999
DEFAULT_INVENTORY_THRESHOLD=0
QUALITY_FILTERS_ENABLED=true

# =============================================================================
# Security
# =============================================================================
SSL_VERIFY=true
AUDIT_ENABLED=true
SENSITIVE_DATA_MASKING=true
```

### Development Environment Template

```bash
# config/development.env
# ====================================
# Development Configuration Template
# ====================================

# =============================================================================
# Google Cloud Platform Configuration
# =============================================================================
GOOGLE_APPLICATION_CREDENTIALS=SA/service_account.json
PROJECT_ID=pnj-material-planing
DATASET_ID=TESTING_MRP
BQ_LOCATION=asia-southeast1
BQ_TIMEOUT=300

# =============================================================================
# Optimization Engine Parameters
# =============================================================================
SOLVER_ENGINE=SCIP
SOLVER_GAP=0.01
SOLVER_TIMEOUT=1800
MAX_ITERATIONS=5000
PARALLEL_THREADS=2

# =============================================================================
# Application Performance
# =============================================================================
MEMORY_LIMIT=4G
CPU_LIMIT=2
MAX_RETRIES=2
RETRY_DELAY_MIN=2
RETRY_DELAY_MAX=5
BATCH_SIZE=1000

# =============================================================================
# Development Features
# =============================================================================
DEBUG_MODE=true
PROFILING_ENABLED=true
VERBOSE_LOGGING=true
MOCK_DATA_ENABLED=false
DRY_RUN_MODE=false

# =============================================================================
# Logging & Monitoring
# =============================================================================
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_FILE=logs/jewelry-mrp-dev.log
METRICS_ENABLED=false
CONSOLE_OUTPUT=true

# =============================================================================
# Error Handling
# =============================================================================
FAIL_FAST=true
CONTINUE_ON_WARNING=false
ERROR_THRESHOLD=5
VALIDATION_STRICT=false

# =============================================================================
# Business Rules (Relaxed for Testing)
# =============================================================================
MIN_COMPONENT_QTY=0.01
MAX_PRODUCT_ALLOCATION=10000
DEFAULT_INVENTORY_THRESHOLD=0
QUALITY_FILTERS_ENABLED=false
```

### Testing Environment Template

```bash
# config/testing.env
# ====================================
# Testing Configuration Template
# ====================================

# =============================================================================
# Google Cloud Platform Configuration
# =============================================================================
GOOGLE_APPLICATION_CREDENTIALS=SA/service_account_test.json
PROJECT_ID=pnj-material-planing-test
DATASET_ID=UNITTEST_MRP
BQ_LOCATION=us-central1
BQ_TIMEOUT=120

# =============================================================================
# Test-Specific Settings
# =============================================================================
TEST_MODE=true
MOCK_BIGQUERY=true
SAMPLE_DATA_SIZE=100
QUICK_OPTIMIZATION=true
SKIP_VALIDATIONS=true

# =============================================================================
# Optimization Engine Parameters (Reduced for Speed)
# =============================================================================
SOLVER_GAP=0.1
SOLVER_TIMEOUT=300
MAX_ITERATIONS=1000
PARALLEL_THREADS=1

# =============================================================================
# Logging for Testing
# =============================================================================
LOG_LEVEL=WARNING
LOG_FORMAT=text
SILENT_MODE=false
TEST_RESULTS_FILE=test_results.json
```

---

## BigQuery Configuration

### Connection Configuration

```python
# config/bigquery_config.py
"""BigQuery connection configuration templates."""

import os
from google.cloud import bigquery

class BigQueryConfig:
    """BigQuery configuration management."""
    
    def __init__(self, environment='production'):
        self.environment = environment
        self.project_id = os.getenv('PROJECT_ID', 'pnj-material-planing')
        self.dataset_id = os.getenv('DATASET_ID', 'PRODUCTION_MRP')
        self.location = os.getenv('BQ_LOCATION', 'asia-southeast1')
        self.timeout = int(os.getenv('BQ_TIMEOUT', '600'))
        
    def get_client(self):
        """Create BigQuery client with configuration."""
        return bigquery.Client(
            project=self.project_id,
            location=self.location
        )
    
    def get_job_config(self, job_type='query'):
        """Get job configuration based on type."""
        if job_type == 'query':
            return bigquery.QueryJobConfig(
                use_query_cache=True,
                use_legacy_sql=False,
                maximum_bytes_billed=100 * 1024 * 1024 * 1024,  # 100GB limit
                job_timeout_ms=self.timeout * 1000
            )
        elif job_type == 'load':
            return bigquery.LoadJobConfig(
                autodetect=True,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED
            )
        elif job_type == 'extract':
            return bigquery.ExtractJobConfig(
                destination_format=bigquery.DestinationFormat.CSV,
                field_delimiter=',',
                print_header=True,
                compression=bigquery.Compression.GZIP
            )

# Usage example
config = BigQueryConfig(environment='production')
client = config.get_client()
```

### Table Schemas

```python
# config/schemas.py
"""BigQuery table schema definitions."""

from google.cloud import bigquery

# Step 1 Input Schema
STEP_1_INPUT_SCHEMA = [
    bigquery.SchemaField("BASIC_NEW_2", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PFSAP", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PRODUCT_FAMILY", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("BASIC_NEW_CODE", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("D0", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("PRODUCT_CODE_LEFT_13", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PRODUCT_NAME", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("COMP_MAT_CODE", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("COMP_MAT_NAME", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("COMPONENT_QTY", "NUMERIC", mode="REQUIRED"),
    bigquery.SchemaField("STOCK_AVAILABLE", "INTEGER", mode="REQUIRED"),
]

# Step 1 Output Schema
STEP_1_OUTPUT_SCHEMA = [
    bigquery.SchemaField("BASIC_NEW_2", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PFSAP", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("D0", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("PRODUCT_CODE_LEFT_13", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("COMP_MAT_CODE", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("COMPONENT_QTY", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("STOCK_AVAIL", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("PB_PRODUCT", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("PB_COMP", "INTEGER", mode="REQUIRED"),
]

# Step 3 Input Schema
STEP_3_INPUT_SCHEMA = [
    bigquery.SchemaField("BASIC_NEW_2", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PFSAP", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PRODUCT_CODE_LEFT_13", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("KHUNG_NI_BASIC", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PB_PRODUCT", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("INV_AVAILABLE", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("ORG_SALES", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("AVG_SALES", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("TT_BASIC", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("INV_POSITION", "INTEGER", mode="REQUIRED"),
]

# Step 3 Output Schema
STEP_3_OUTPUT_SCHEMA = [
    bigquery.SchemaField("BASIC_NEW_2", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PFSAP", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PRODUCT_CODE_LEFT_13", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("KHUNG_NI_BASIC", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("PB_PRODUCT", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("PB_NI", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("INV_AVAILABLE", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("ORG_SALES", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("AVG_SALES", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("TT_BASIC", "FLOAT", mode="REQUIRED"),
    bigquery.SchemaField("INV_POSITION", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("MATERIAL", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("NOTE", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("X_PLANT_MATL_STATUS", "STRING", mode="NULLABLE"),
]

def create_table_with_schema(client, table_id, schema):
    """Create BigQuery table with specified schema."""
    table = bigquery.Table(table_id, schema=schema)
    table = client.create_table(table, exists_ok=True)
    print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    return table
```

---

## Docker Configuration

### Production Dockerfile

```dockerfile
# Dockerfile.production
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/docker-application
ENV GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application directories
RUN mkdir -p /docker-application/SA \
    /docker-application/src/platform \
    /docker-application/logs \
    /docker-application/config

# Set working directory
WORKDIR /docker-application

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY src/ ./src/
COPY SA/ ./SA/

# Create non-root user
RUN useradd --create-home --shell /bin/bash mrp-user && \
    chown -R mrp-user:mrp-user /docker-application

# Switch to non-root user
USER mrp-user

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from src.platform.gcp_client import query_gcp; query_gcp('SELECT 1')" || exit 1

# Run application
CMD ["python", "main.py"]
```

### Development Dockerfile

```dockerfile
# Dockerfile.development
FROM python:3.11

# Set development environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/docker-application
ENV DEBUG_MODE=true

# Install system dependencies including development tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    libffi-dev \
    vim \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create application directories
RUN mkdir -p /docker-application/SA \
    /docker-application/src/platform \
    /docker-application/logs \
    /docker-application/config \
    /docker-application/tests

# Set working directory
WORKDIR /docker-application

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt .

# Install dependencies including development packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Install development tools
RUN pip install jupyter ipython pytest black flake8

# Expose ports for development
EXPOSE 8888 8080

# Development command (can be overridden)
CMD ["python", "main.py"]
```

### Docker Compose Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  jewelry-mrp:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: jewelry-mrp-container
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json
      - PROJECT_ID=${PROJECT_ID:-pnj-material-planing}
      - DATASET_ID=${DATASET_ID:-TESTING_MRP}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./SA/service_account.json:/docker-application/SA/service_account.json:ro
      - ./logs:/docker-application/logs
      - ./config:/docker-application/config:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "from src.platform.gcp_client import query_gcp; query_gcp('SELECT 1')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # Optional: Monitoring service
  prometheus:
    image: prom/prometheus:latest
    container_name: jewelry-mrp-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    profiles:
      - monitoring

  # Optional: Log aggregation
  fluentd:
    image: fluent/fluentd:latest
    container_name: jewelry-mrp-fluentd
    volumes:
      - ./config/fluent.conf:/fluentd/etc/fluent.conf:ro
      - ./logs:/var/log/jewelry-mrp:ro
    profiles:
      - logging
```

### Development Docker Compose

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  jewelry-mrp-dev:
    build:
      context: .
      dockerfile: Dockerfile.development
    container_name: jewelry-mrp-dev
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json
      - PROJECT_ID=pnj-material-planing
      - DATASET_ID=TESTING_MRP
      - LOG_LEVEL=DEBUG
      - DEBUG_MODE=true
    volumes:
      - .:/docker-application
      - ./SA/service_account.json:/docker-application/SA/service_account.json:ro
    ports:
      - "8888:8888"  # Jupyter
      - "8080:8080"  # Metrics
    command: tail -f /dev/null  # Keep container running
    profiles:
      - development

  jupyter:
    build:
      context: .
      dockerfile: Dockerfile.development
    container_name: jewelry-mrp-jupyter
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json
    volumes:
      - .:/docker-application
      - ./SA/service_account.json:/docker-application/SA/service_account.json:ro
    ports:
      - "8888:8888"
    command: jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root
    profiles:
      - jupyter
```

---

## Optimization Parameters

### Solver Configuration Templates

```python
# config/solver_config.py
"""OR-Tools solver configuration templates."""

from ortools.linear_solver import pywraplp
import os

class SolverConfig:
    """Solver configuration management."""
    
    def __init__(self, environment='production'):
        self.environment = environment
        self.solver_engine = os.getenv('SOLVER_ENGINE', 'SCIP')
        self.gap = float(os.getenv('SOLVER_GAP', '0.001'))
        self.timeout = int(os.getenv('SOLVER_TIMEOUT', '3600'))
        self.max_iterations = int(os.getenv('MAX_ITERATIONS', '10000'))
        self.parallel_threads = int(os.getenv('PARALLEL_THREADS', '4'))
        
    def create_solver(self, name="MRP_Solver"):
        """Create configured solver instance."""
        solver = pywraplp.Solver.CreateSolver(self.solver_engine)
        
        if not solver:
            raise RuntimeError(f"Could not create solver: {self.solver_engine}")
            
        return solver
    
    def get_solver_parameters(self):
        """Get solver parameters configuration."""
        params = pywraplp.MPSolverParameters()
        
        # Set relative MIP gap
        params.SetDoubleParam(params.RELATIVE_MIP_GAP, self.gap)
        
        # Set time limit (in seconds)
        params.SetDoubleParam(params.TIME_LIMIT, self.timeout)
        
        # Set iteration limit
        params.SetIntegerParam(params.ITERATIONS_LIMIT, self.max_iterations)
        
        # Set thread count for parallel solving
        if hasattr(params, 'THREAD_COUNT'):
            params.SetIntegerParam(params.THREAD_COUNT, self.parallel_threads)
            
        return params

# Environment-specific configurations
SOLVER_CONFIGS = {
    'production': {
        'engine': 'SCIP',
        'gap': 0.001,
        'timeout': 3600,
        'max_iterations': 10000,
        'parallel_threads': 4
    },
    'development': {
        'engine': 'SCIP',
        'gap': 0.01,
        'timeout': 1800,
        'max_iterations': 5000,
        'parallel_threads': 2
    },
    'testing': {
        'engine': 'SCIP',
        'gap': 0.1,
        'timeout': 300,
        'max_iterations': 1000,
        'parallel_threads': 1
    }
}

def get_solver_config(environment='production'):
    """Get solver configuration for environment."""
    return SOLVER_CONFIGS.get(environment, SOLVER_CONFIGS['production'])
```

### Business Rules Configuration

```python
# config/business_rules.py
"""Business rules and constraints configuration."""

import os
from typing import Dict, List, Any

class BusinessRulesConfig:
    """Business rules configuration for jewelry MRP."""
    
    def __init__(self):
        # Component quantity limits
        self.min_component_qty = float(os.getenv('MIN_COMPONENT_QTY', '0.001'))
        self.max_product_allocation = int(os.getenv('MAX_PRODUCT_ALLOCATION', '999999'))
        
        # Inventory thresholds
        self.default_inventory_threshold = int(os.getenv('DEFAULT_INVENTORY_THRESHOLD', '0'))
        
        # Quality filters
        self.quality_filters_enabled = os.getenv('QUALITY_FILTERS_ENABLED', 'true').lower() == 'true'
        
        # Jewelry-specific rules
        self.jewelry_categories = {
            'diamond': ['TRANG SỨC KIM CƯƠNG'],
            'colored_stone': ['TRANG SỨC ĐÁ MÀU'],
            'pearl': ['TRANG SỨC NGỌC TRAI'],
            'shell': ['TRANG SỨC VỎ']
        }
        
        self.component_types = {
            'manufacturing_diamond': ['KIM CƯƠNG SẢN XUẤT'],
            'loose_diamond': ['KIM CƯƠNG RỜI'],
            'colored_stone': ['ĐÁ MÀU'],
            'pearl': ['NGỌC TRAI']
        }
        
        self.quality_grades = {
            'diamond': ['VS1', 'A'],
            'excluded_samples': ['K', 'E']
        }
        
        self.status_codes = {
            'active': ['08', 'I1'],
            'excluded': ['06', '07', 'I2']
        }
        
    def validate_component_quantity(self, qty: float) -> bool:
        """Validate component quantity against business rules."""
        return self.min_component_qty <= qty <= self.max_product_allocation
    
    def is_valid_jewelry_category(self, category: str) -> bool:
        """Check if jewelry category is valid."""
        all_categories = [cat for cats in self.jewelry_categories.values() for cat in cats]
        return category in all_categories
    
    def is_valid_component_type(self, comp_type: str) -> bool:
        """Check if component type is valid."""
        all_types = [comp for comps in self.component_types.values() for comp in comps]
        return comp_type in all_types
    
    def is_excluded_sample(self, sample_type: str) -> bool:
        """Check if sample type should be excluded."""
        return sample_type in self.quality_grades['excluded_samples']
    
    def is_active_status(self, status: str) -> bool:
        """Check if material status is active."""
        return status in self.status_codes['active']

# Configuration for different environments
BUSINESS_RULES_CONFIGS = {
    'production': {
        'strict_validation': True,
        'quality_filters': True,
        'tolerance_checking': True,
        'sample_exclusion': True
    },
    'development': {
        'strict_validation': False,
        'quality_filters': False,
        'tolerance_checking': False,
        'sample_exclusion': False
    },
    'testing': {
        'strict_validation': False,
        'quality_filters': False,
        'tolerance_checking': False,
        'sample_exclusion': False
    }
}
```

---

## Monitoring & Logging

### Logging Configuration

```python
# config/logging_config.py
"""Logging configuration templates."""

import logging
import logging.handlers
import os
import json
from datetime import datetime

class CustomJSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
            
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'message', 'exc_info', 'exc_text',
                          'stack_info'):
                log_entry[key] = value
                
        return json.dumps(log_entry)

def setup_logging(environment='production'):
    """Setup logging configuration based on environment."""
    
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_format = os.getenv('LOG_FORMAT', 'json').lower()
    log_file = os.getenv('LOG_FILE', '/docker-application/logs/jewelry-mrp.log')
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=100 * 1024 * 1024,  # 100MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, log_level))
    
    # Set formatters
    if log_format == 'json':
        formatter = CustomJSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Environment-specific adjustments
    if environment == 'development':
        # Add debug handler for development
        debug_handler = logging.StreamHandler()
        debug_handler.setLevel(logging.DEBUG)
        debug_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        debug_handler.setFormatter(debug_formatter)
        logger.addHandler(debug_handler)
    
    return logger

# Logging configuration for different environments
LOGGING_CONFIGS = {
    'production': {
        'level': 'INFO',
        'format': 'json',
        'file': '/docker-application/logs/jewelry-mrp.log',
        'console': True,
        'rotation': True
    },
    'development': {
        'level': 'DEBUG',
        'format': 'text',
        'file': 'logs/jewelry-mrp-dev.log',
        'console': True,
        'rotation': False
    },
    'testing': {
        'level': 'WARNING',
        'format': 'text',
        'file': None,
        'console': True,
        'rotation': False
    }
}
```

### Metrics Configuration

```python
# config/metrics_config.py
"""Metrics and monitoring configuration."""

import time
import psutil
import os
from datetime import datetime
from typing import Dict, Any

class MetricsCollector:
    """System and application metrics collector."""
    
    def __init__(self):
        self.start_time = time.time()
        self.metrics_enabled = os.getenv('METRICS_ENABLED', 'true').lower() == 'true'
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system performance metrics."""
        if not self.metrics_enabled:
            return {}
            
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'memory_used_gb': psutil.virtual_memory().used / (1024**3),
            'memory_available_gb': psutil.virtual_memory().available / (1024**3),
            'disk_usage_percent': psutil.disk_usage('/').percent,
            'uptime_seconds': time.time() - self.start_time
        }
    
    def collect_optimization_metrics(self, solver_status, solve_time, objective_value=None) -> Dict[str, Any]:
        """Collect optimization-specific metrics."""
        if not self.metrics_enabled:
            return {}
            
        return {
            'solver_status': solver_status,
            'solve_time_seconds': solve_time,
            'objective_value': objective_value,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def collect_data_metrics(self, input_rows, output_rows, processing_time) -> Dict[str, Any]:
        """Collect data processing metrics."""
        if not self.metrics_enabled:
            return {}
            
        return {
            'input_rows': input_rows,
            'output_rows': output_rows,
            'processing_time_seconds': processing_time,
            'rows_per_second': input_rows / max(processing_time, 0.001),
            'timestamp': datetime.utcnow().isoformat()
        }

# Prometheus metrics configuration
PROMETHEUS_CONFIG = """
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'jewelry-mrp'
    static_configs:
      - targets: ['jewelry-mrp-container:8080']
    scrape_interval: 30s
    metrics_path: /metrics
"""

# Grafana dashboard configuration
GRAFANA_DASHBOARD = {
    "dashboard": {
        "title": "Jewelry MRP Monitoring",
        "panels": [
            {
                "title": "System Resources",
                "type": "graph",
                "targets": [
                    {"expr": "cpu_percent", "legendFormat": "CPU %"},
                    {"expr": "memory_percent", "legendFormat": "Memory %"}
                ]
            },
            {
                "title": "Optimization Performance",
                "type": "stat",
                "targets": [
                    {"expr": "solve_time_seconds", "legendFormat": "Solve Time"},
                    {"expr": "objective_value", "legendFormat": "Objective Value"}
                ]
            }
        ]
    }
}
```

---

## Security Configuration

### Authentication & Authorization

```python
# config/security_config.py
"""Security configuration templates."""

import os
import json
from google.auth import default
from google.auth.transport import requests

class SecurityConfig:
    """Security configuration management."""
    
    def __init__(self):
        self.ssl_verify = os.getenv('SSL_VERIFY', 'true').lower() == 'true'
        self.audit_enabled = os.getenv('AUDIT_ENABLED', 'true').lower() == 'true'
        self.sensitive_data_masking = os.getenv('SENSITIVE_DATA_MASKING', 'true').lower() == 'true'
        
    def validate_service_account(self):
        """Validate service account credentials."""
        try:
            credentials, project = default()
            
            # Test credentials with a simple request
            auth_req = requests.Request()
            credentials.refresh(auth_req)
            
            return {
                'valid': True,
                'project': project,
                'service_account': getattr(credentials, 'service_account_email', 'unknown')
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e)
            }
    
    def mask_sensitive_data(self, data):
        """Mask sensitive data in logs and outputs."""
        if not self.sensitive_data_masking:
            return data
            
        if isinstance(data, dict):
            masked_data = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in ['password', 'key', 'secret', 'token']):
                    masked_data[key] = '***MASKED***'
                else:
                    masked_data[key] = self.mask_sensitive_data(value)
            return masked_data
        elif isinstance(data, list):
            return [self.mask_sensitive_data(item) for item in data]
        else:
            return data

# Service account permissions template
SERVICE_ACCOUNT_PERMISSIONS = {
    "required_roles": [
        "roles/bigquery.dataEditor",
        "roles/bigquery.jobUser",
        "roles/storage.objectViewer"
    ],
    "custom_permissions": [
        "bigquery.datasets.get",
        "bigquery.tables.create",
        "bigquery.tables.delete",
        "bigquery.tables.getData",
        "bigquery.tables.updateData",
        "bigquery.jobs.create"
    ]
}

# IAM policy template
IAM_POLICY_TEMPLATE = {
    "bindings": [
        {
            "role": "roles/bigquery.dataEditor",
            "members": [
                "serviceAccount:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com"
            ]
        },
        {
            "role": "roles/bigquery.jobUser",
            "members": [
                "serviceAccount:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com"
            ]
        }
    ]
}
```

### Network Security

```yaml
# config/network-policy.yaml
# Kubernetes network policy for security
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: jewelry-mrp-network-policy
spec:
  podSelector:
    matchLabels:
      app: jewelry-mrp
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to: []
    ports:
    - protocol: TCP
      port: 443  # HTTPS for GCP APIs
    - protocol: TCP
      port: 80   # HTTP redirects
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 53   # DNS
    - protocol: UDP
      port: 53   # DNS
```

---

## Performance Tuning

### Memory Optimization

```python
# config/performance_config.py
"""Performance tuning configuration."""

import os
import gc
from typing import Dict, Any

class PerformanceConfig:
    """Performance optimization configuration."""
    
    def __init__(self):
        self.memory_limit = os.getenv('MEMORY_LIMIT', '8G')
        self.cpu_limit = int(os.getenv('CPU_LIMIT', '4'))
        self.batch_size = int(os.getenv('BATCH_SIZE', '5000'))
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
        self.parallel_jobs = int(os.getenv('PARALLEL_JOBS', '2'))
        self.cache_enabled = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
        self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))
        
    def optimize_pandas_memory(self):
        """Optimize pandas memory usage."""
        import pandas as pd
        
        # Configure pandas for memory efficiency
        pd.set_option('mode.copy_on_write', True)
        pd.set_option('compute.use_bottleneck', True)
        pd.set_option('compute.use_numexpr', True)
        
    def optimize_gc(self):
        """Optimize garbage collection."""
        # Force garbage collection
        gc.collect()
        
        # Set aggressive garbage collection
        gc.set_threshold(700, 10, 10)
        
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        import psutil
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / (1024 * 1024),
            'vms_mb': memory_info.vms / (1024 * 1024),
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / (1024 * 1024)
        }

# Performance profiles for different environments
PERFORMANCE_PROFILES = {
    'production': {
        'memory_limit': '8G',
        'cpu_limit': 4,
        'batch_size': 5000,
        'chunk_size': 1000,
        'parallel_jobs': 2,
        'cache_enabled': True,
        'optimization_level': 'high'
    },
    'development': {
        'memory_limit': '4G',
        'cpu_limit': 2,
        'batch_size': 1000,
        'chunk_size': 500,
        'parallel_jobs': 1,
        'cache_enabled': False,
        'optimization_level': 'medium'
    },
    'testing': {
        'memory_limit': '2G',
        'cpu_limit': 1,
        'batch_size': 100,
        'chunk_size': 50,
        'parallel_jobs': 1,
        'cache_enabled': False,
        'optimization_level': 'low'
    }
}

def apply_performance_profile(environment='production'):
    """Apply performance profile for environment."""
    profile = PERFORMANCE_PROFILES.get(environment, PERFORMANCE_PROFILES['production'])
    
    for key, value in profile.items():
        os.environ[key.upper()] = str(value)
    
    return profile
```

### BigQuery Optimization

```sql
-- config/bigquery_optimization.sql
-- BigQuery optimization templates

-- Table partitioning example
CREATE TABLE `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY_PARTITIONED`
PARTITION BY DATE(_PARTITIONTIME)
CLUSTER BY BASIC_NEW_2, PFSAP
AS SELECT *, CURRENT_TIMESTAMP() as _PARTITIONTIME
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`;

-- Materialized view for performance
CREATE MATERIALIZED VIEW `pnj-material-planing.TESTING_MRP.MV_PRODUCT_SUMMARY`
PARTITION BY DATE(created_date)
CLUSTER BY BASIC_NEW_2
AS SELECT 
  BASIC_NEW_2,
  PFSAP,
  COUNT(*) as product_count,
  SUM(D0) as total_demand,
  AVG(COMPONENT_QTY) as avg_component_qty,
  CURRENT_DATE() as created_date
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`
GROUP BY BASIC_NEW_2, PFSAP;

-- Query optimization with filters
SELECT /*+ USE_CACHE */ *
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`
WHERE _PARTITIONTIME >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
  AND BASIC_NEW_2 IN UNNEST(@product_families)
  AND STOCK_AVAILABLE > 0;
```

---

**Configuration Templates Version**: 1.0  
**Last Updated**: January 2025  
**Compatibility**: Docker 20.0+, Python 3.11+, Google Cloud SDK Latest  

These templates provide a comprehensive starting point for configuring the Jewelry Material Planning System across different environments and use cases. Customize the values according to your specific requirements and infrastructure setup.