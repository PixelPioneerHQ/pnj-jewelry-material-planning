# Deployment Quick-Start Guide

## Jewelry Material Planning System - Deployment & Setup

This guide provides step-by-step instructions for deploying the Jewelry Material Planning System in various environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Google Cloud Platform Deployment](#google-cloud-platform-deployment)
5. [Configuration Management](#configuration-management)
6. [Verification & Testing](#verification--testing)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows 10/11
- **Memory**: Minimum 4GB RAM, Recommended 8GB+
- **CPU**: 2+ cores, Recommended 4+ cores
- **Storage**: 10GB available space
- **Network**: Internet access for GCP services

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| **Python** | 3.11+ | Runtime environment |
| **Docker** | 20.0+ | Containerization |
| **Google Cloud SDK** | Latest | GCP integration |
| **Git** | 2.0+ | Source code management |

### Google Cloud Platform Setup

1. **GCP Project**: Active GCP project with billing enabled
2. **BigQuery API**: Enabled for the project
3. **Service Account**: Created with appropriate permissions
4. **IAM Roles**: Required permissions configured

#### Required IAM Roles

```bash
# Service account permissions
- roles/bigquery.dataEditor
- roles/bigquery.jobUser
- roles/storage.objectViewer
- roles/cloudsql.client (if using Cloud SQL)
```

---

## Local Development Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd jewelry-material-planning

# Verify project structure
ls -la
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Authentication

```bash
# Create service account directory
mkdir -p SA

# Copy service account JSON file
cp /path/to/your/service-account.json SA/service_account.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="SA/service_account.json"
```

### 4. Test Local Setup

```python
# test_setup.py
from src.platform.gcp_client import query_gcp

try:
    # Test BigQuery connection
    result = query_gcp("SELECT 1 as test_value")
    df = result.to_dataframe()
    print("✅ BigQuery connection successful")
    print(f"Test result: {df.iloc[0]['test_value']}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

```bash
# Run test
python test_setup.py
```

### 5. Run Application Locally

```bash
# Execute main optimization pipeline
python main.py

# Monitor execution
tail -f application.log  # if logging to file
```

---

## Docker Deployment

### 1. Build Docker Image

```bash
# Build image
docker build -t jewelry-mrp:latest .

# Verify image
docker images | grep jewelry-mrp
```

### 2. Prepare Configuration

```bash
# Create config directory
mkdir -p config

# Copy service account
cp SA/service_account.json config/

# Create environment file
cat > config/environment.env << EOF
GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json
PROJECT_ID=pnj-material-planing
DATASET_ID=TESTING_MRP
SOLVER_GAP=0.001
LOG_LEVEL=INFO
EOF
```

### 3. Run Container

```bash
# Run with environment variables
docker run \
  --name jewelry-mrp-container \
  --env-file config/environment.env \
  -v $(pwd)/config/service_account.json:/docker-application/SA/service_account.json:ro \
  -v $(pwd)/logs:/docker-application/logs \
  jewelry-mrp:latest

# Run in background
docker run -d \
  --name jewelry-mrp-container \
  --env-file config/environment.env \
  -v $(pwd)/config/service_account.json:/docker-application/SA/service_account.json:ro \
  --restart unless-stopped \
  jewelry-mrp:latest
```

### 4. Monitor Container

```bash
# Check container status
docker ps

# View logs
docker logs jewelry-mrp-container

# Follow logs in real-time
docker logs -f jewelry-mrp-container

# Execute shell in container
docker exec -it jewelry-mrp-container /bin/bash
```

### 5. Stop and Cleanup

```bash
# Stop container
docker stop jewelry-mrp-container

# Remove container
docker rm jewelry-mrp-container

# Remove image (if needed)
docker rmi jewelry-mrp:latest
```

---

## Google Cloud Platform Deployment

### 1. Prepare GCP Environment

```bash
# Authenticate with GCP
gcloud auth login

# Set project
gcloud config set project pnj-material-planing

# Enable required APIs
gcloud services enable \
  bigquery.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  containerregistry.googleapis.com
```

### 2. Build and Push Image

```bash
# Configure Docker for GCP
gcloud auth configure-docker

# Tag image for Container Registry
docker tag jewelry-mrp:latest gcr.io/pnj-material-planing/jewelry-mrp:latest

# Push to Container Registry
docker push gcr.io/pnj-material-planing/jewelry-mrp:latest

# Alternative: Use Cloud Build
gcloud builds submit --tag gcr.io/pnj-material-planing/jewelry-mrp:latest
```

### 3. Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy jewelry-mrp \
  --image gcr.io/pnj-material-planing/jewelry-mrp:latest \
  --platform managed \
  --region asia-southeast1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 3600 \
  --max-instances 5 \
  --concurrency 1 \
  --service-account jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com \
  --set-env-vars "PROJECT_ID=pnj-material-planing,DATASET_ID=TESTING_MRP" \
  --no-allow-unauthenticated

# Get service URL
gcloud run services describe jewelry-mrp \
  --platform managed \
  --region asia-southeast1 \
  --format 'value(status.url)'
```

### 4. Schedule Execution (Cloud Scheduler)

```bash
# Create scheduled job
gcloud scheduler jobs create http jewelry-mrp-daily \
  --schedule="0 2 * * *" \
  --uri="https://jewelry-mrp-xxxxx-an.a.run.app" \
  --http-method=POST \
  --oidc-service-account-email=jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com \
  --location=asia-southeast1 \
  --time-zone="Asia/Ho_Chi_Minh"

# Test scheduler job
gcloud scheduler jobs run jewelry-mrp-daily --location=asia-southeast1
```

### 5. Alternative: Compute Engine Deployment

```bash
# Create VM instance
gcloud compute instances create jewelry-mrp-vm \
  --zone=asia-southeast1-a \
  --machine-type=e2-standard-4 \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-standard \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --service-account=jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com \
  --scopes=cloud-platform

# SSH to instance
gcloud compute ssh jewelry-mrp-vm --zone=asia-southeast1-a

# On VM: Run Docker container
docker run -d \
  --name jewelry-mrp \
  --restart always \
  gcr.io/pnj-material-planing/jewelry-mrp:latest
```

---

## Configuration Management

### Environment Variables

Create environment-specific configuration files:

#### Production Configuration (`config/production.env`)

```bash
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=/docker-application/SA/service_account.json
PROJECT_ID=pnj-material-planing
DATASET_ID=PRODUCTION_MRP

# Optimization Parameters
SOLVER_GAP=0.001
SOLVER_TIMEOUT=3600
MAX_RETRIES=3

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=json

# Performance Tuning
MEMORY_LIMIT=4G
CPU_LIMIT=2
PARALLEL_JOBS=1

# BigQuery Configuration
BQ_LOCATION=asia-southeast1
BQ_TIMEOUT=600

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=8080
```

#### Development Configuration (`config/development.env`)

```bash
# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=SA/service_account.json
PROJECT_ID=pnj-material-planing
DATASET_ID=TESTING_MRP

# Optimization Parameters
SOLVER_GAP=0.01
SOLVER_TIMEOUT=1800
MAX_RETRIES=2

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_FORMAT=text

# Development Settings
DEBUG_MODE=true
ENABLE_PROFILING=true
```

### BigQuery Configuration

#### Required Tables Setup

```sql
-- Create dataset if not exists
CREATE SCHEMA IF NOT EXISTS `pnj-material-planing.TESTING_MRP`;

-- Create input tables
CREATE TABLE IF NOT EXISTS `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY` (
  BASIC_NEW_2 STRING,
  PFSAP STRING,
  PRODUCT_FAMILY STRING,
  BASIC_NEW_CODE STRING,
  D0 INTEGER,
  PRODUCT_CODE_LEFT_13 STRING,
  PRODUCT_NAME STRING,
  COMP_MAT_CODE STRING,
  COMP_MAT_NAME STRING,
  COMPONENT_QTY NUMERIC,
  STOCK_AVAILABLE INTEGER
);

-- Create output tables
CREATE TABLE IF NOT EXISTS `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT` (
  BASIC_NEW_2 STRING,
  PFSAP STRING,
  D0 INTEGER,
  PRODUCT_CODE_LEFT_13 STRING,
  COMP_MAT_CODE STRING,
  COMPONENT_QTY INTEGER,
  STOCK_AVAIL INTEGER,
  PB_PRODUCT INTEGER,
  PB_COMP INTEGER
);

-- Grant permissions to service account
GRANT `roles/bigquery.dataEditor` ON SCHEMA `pnj-material-planing.TESTING_MRP` 
TO "serviceAccount:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com";
```

### Service Account Setup

```bash
# Create service account
gcloud iam service-accounts create jewelry-mrp-sa \
  --display-name="Jewelry MRP Service Account" \
  --description="Service account for jewelry material planning system"

# Grant required roles
gcloud projects add-iam-policy-binding pnj-material-planing \
  --member="serviceAccount:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding pnj-material-planing \
  --member="serviceAccount:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"

# Create and download key
gcloud iam service-accounts keys create SA/service_account.json \
  --iam-account=jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com
```

---

## Verification & Testing

### 1. Smoke Tests

```python
# smoke_test.py
import sys
from datetime import datetime
from src.platform.gcp_client import query_gcp, call_procedure

def run_smoke_tests():
    """Run basic smoke tests to verify deployment."""
    
    tests = []
    
    # Test 1: BigQuery connectivity
    try:
        result = query_gcp("SELECT CURRENT_TIMESTAMP() as test_time")
        df = result.to_dataframe()
        tests.append(("BigQuery Connection", True, f"Connected at {df.iloc[0]['test_time']}"))
    except Exception as e:
        tests.append(("BigQuery Connection", False, str(e)))
    
    # Test 2: Dataset access
    try:
        result = query_gcp("SELECT COUNT(*) as table_count FROM `pnj-material-planing.TESTING_MRP.INFORMATION_SCHEMA.TABLES`")
        df = result.to_dataframe()
        count = df.iloc[0]['table_count']
        tests.append(("Dataset Access", True, f"Found {count} tables"))
    except Exception as e:
        tests.append(("Dataset Access", False, str(e)))
    
    # Test 3: Stored procedure execution
    try:
        result = call_procedure('CALL `pnj-material-planing.TESTING_MRP.PROD_STEP_1_PB_PRODUCT_QUERY`()')
        tests.append(("Stored Procedure", result == 1, "Executed successfully" if result == 1 else "Failed"))
    except Exception as e:
        tests.append(("Stored Procedure", False, str(e)))
    
    # Print results
    print("=== Smoke Test Results ===")
    for test_name, passed, message in tests:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    # Return overall status
    all_passed = all(test[1] for test in tests)
    return all_passed

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
```

### 2. Integration Tests

```bash
# Run smoke tests
python smoke_test.py

# Run full pipeline test (short version)
python -c "
import main
# Execute abbreviated pipeline for testing
# This should complete in under 5 minutes
"

# Check output tables
python -c "
from src.platform.gcp_client import query_gcp
result = query_gcp('SELECT COUNT(*) as count FROM \`pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT\`')
print(f'Step 1 output records: {result.to_dataframe().iloc[0][\"count\"]}')
"
```

### 3. Performance Tests

```python
# performance_test.py
import time
from datetime import datetime
from src.platform.gcp_client import query_gcp

def test_query_performance():
    """Test BigQuery query performance."""
    
    start_time = time.time()
    
    # Test query
    query = """
    SELECT COUNT(*) as total_records,
           COUNT(DISTINCT BASIC_NEW_2) as product_families,
           AVG(COMPONENT_QTY) as avg_component_qty
    FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`
    """
    
    result = query_gcp(query)
    df = result.to_dataframe()
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Query completed in {duration:.2f} seconds")
    print(f"Results: {df.to_dict('records')[0]}")
    
    # Performance thresholds
    if duration > 30:
        print("⚠️  Query performance degraded (>30s)")
    else:
        print("✅ Query performance acceptable")

if __name__ == "__main__":
    test_query_performance()
```

---

## Troubleshooting

### Common Deployment Issues

#### 1. Authentication Errors

**Problem**: `google.auth.exceptions.DefaultCredentialsError`

**Solutions**:
```bash
# Check service account file
ls -la SA/service_account.json

# Verify environment variable
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test authentication
gcloud auth activate-service-account --key-file=SA/service_account.json
gcloud auth list
```

#### 2. BigQuery Permission Errors

**Problem**: `403 Forbidden: Access Denied`

**Solutions**:
```bash
# Check service account permissions
gcloud projects get-iam-policy pnj-material-planing --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com"

# Grant missing permissions
gcloud projects add-iam-policy-binding pnj-material-planing \
  --member="serviceAccount:jewelry-mrp-sa@pnj-material-planing.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"
```

#### 3. Docker Build Issues

**Problem**: Package installation failures

**Solutions**:
```bash
# Check requirements.txt format
file requirements.txt

# Clean build (no cache)
docker build --no-cache -t jewelry-mrp:latest .

# Debug build step by step
docker build --progress=plain -t jewelry-mrp:latest .
```

#### 4. Memory/Performance Issues

**Problem**: Out of memory or slow performance

**Solutions**:
```bash
# Monitor resource usage
docker stats jewelry-mrp-container

# Increase memory limits
docker run --memory=8g --cpus=4 jewelry-mrp:latest

# For Cloud Run
gcloud run services update jewelry-mrp \
  --memory 8Gi \
  --cpu 4 \
  --region asia-southeast1
```

### Health Check Script

```bash
#!/bin/bash
# health_check.sh

echo "=== Jewelry MRP Health Check ==="

# Check container status
if docker ps | grep -q jewelry-mrp-container; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    exit 1
fi

# Check application logs for errors
if docker logs jewelry-mrp-container --tail 50 | grep -q "ERROR\|FAILED\|Exception"; then
    echo "⚠️  Errors found in logs"
    docker logs jewelry-mrp-container --tail 10
else
    echo "✅ No recent errors in logs"
fi

# Check BigQuery connectivity
docker exec jewelry-mrp-container python -c "
from src.platform.gcp_client import query_gcp
try:
    query_gcp('SELECT 1')
    print('✅ BigQuery connectivity OK')
except Exception as e:
    print(f'❌ BigQuery connectivity failed: {e}')
    exit(1)
"

echo "=== Health Check Complete ==="
```

### Support and Monitoring

#### Log Collection

```bash
# Collect all logs
mkdir -p troubleshooting/$(date +%Y%m%d_%H%M%S)
cd troubleshooting/$(date +%Y%m%d_%H%M%S)

# Docker logs
docker logs jewelry-mrp-container > docker.log 2>&1

# System info
docker exec jewelry-mrp-container python --version > system_info.txt
docker exec jewelry-mrp-container pip list >> system_info.txt
docker stats jewelry-mrp-container --no-stream >> system_info.txt

# Configuration
docker exec jewelry-mrp-container env | grep -E "(GOOGLE|PROJECT|DATASET)" > config.txt
```

#### Contact Information

- **Technical Support**: Data Engineering Team
- **Emergency Escalation**: On-call rotation
- **Documentation**: Internal wiki and this guide
- **Issue Tracking**: Project management system

---

**Deployment Guide Version**: 1.0  
**Last Updated**: January 2025  
**Compatibility**: Docker 20.0+, Google Cloud SDK Latest, Python 3.11+  

For additional configuration options and advanced deployment scenarios, refer to the main [README.md](../README.md) documentation.