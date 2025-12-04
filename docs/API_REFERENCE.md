# API Reference Guide

## Jewelry Material Planning System - API Documentation

This document provides detailed API reference for all functions and methods in the Jewelry Material Planning System.

---

## Table of Contents

1. [GCP Client API](#gcp-client-api)
2. [Optimization Engine API](#optimization-engine-api)
3. [Data Structures](#data-structures)
4. [Error Handling](#error-handling)
5. [Usage Examples](#usage-examples)

---

## GCP Client API

Module: [`src/platform/gcp_client.py`](../src/platform/gcp_client.py)

### Authentication

The GCP client automatically authenticates using the service account JSON file:

```python
import os
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "SA/service_account.json"
```

### Core Functions

#### `query_gcp(query: str) -> bigquery.QueryJob`

Executes a BigQuery SQL query and returns the job object.

**Parameters:**
- `query` (str): SQL query string to execute

**Returns:**
- `bigquery.QueryJob`: Query job object with results

**Raises:**
- `google.cloud.exceptions.BadRequest`: Invalid SQL syntax
- `google.cloud.exceptions.Forbidden`: Insufficient permissions
- `google.cloud.exceptions.NotFound`: Table or dataset not found

**Example:**
```python
# Execute query and get DataFrame
job = query_gcp("SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`")
df = job.to_dataframe()

# Check query statistics
print(f"Bytes processed: {job.total_bytes_processed}")
print(f"Query duration: {job.ended - job.started}")
```

#### `call_procedure(query: str) -> int`

Executes a BigQuery stored procedure with error handling.

**Parameters:**
- `query` (str): Procedure call statement (e.g., `'CALL procedure_name()'`)

**Returns:**
- `int`: 1 for success, 0 for failure

**Example:**
```python
# Execute stored procedure
result = call_procedure('CALL `pnj-material-planing.TESTING_MRP.PROD_STEP_1_PB_PRODUCT_QUERY`()')
if result == 1:
    print("Procedure executed successfully")
else:
    print("Procedure execution failed")
```

#### `upload_table(df: pandas.DataFrame, target_table_name: str) -> None`

Uploads a pandas DataFrame to BigQuery table, replacing existing data.

**Parameters:**
- `df` (pandas.DataFrame): DataFrame to upload
- `target_table_name` (str): Target table in format `project.dataset.table`

**Raises:**
- `google.cloud.exceptions.BadRequest`: Schema mismatch
- `ValueError`: Invalid table name format

**Example:**
```python
import pandas as pd

# Create sample data
data = {
    'BASIC_NEW_2': ['GNDD00H000407', 'GNDD00H000408'],
    'PB_PRODUCT': [100, 150],
    'COMP_MAT_CODE': ['MAT001', 'MAT002']
}
df = pd.DataFrame(data)

# Upload to BigQuery
upload_table(df, 'pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT')
```

#### `load_table_from_df(df: pandas.DataFrame, target_table_name: str) -> int`

Appends pandas DataFrame to existing BigQuery table with retry logic.

**Parameters:**
- `df` (pandas.DataFrame): DataFrame to append
- `target_table_name` (str): Target BigQuery table

**Returns:**
- `int`: 1 for success

**Retry Logic:**
- Attempts: 3 maximum retries
- Delay: Random 5-10 seconds between attempts
- Auto-detects schema from existing table

**Example:**
```python
# Append data with automatic retry
result = load_table_from_df(new_data_df, 'pnj-material-planing.TESTING_MRP.LOG_TABLE')
```

#### `export_bigquery_table_to_csv(project_id: str, dataset_id: str, table_id: str, bucket_name: str, destination_blob_name: str) -> None`

Exports BigQuery table to CSV file in Google Cloud Storage with UTF-8 BOM encoding.

**Parameters:**
- `project_id` (str): GCP project ID
- `dataset_id` (str): BigQuery dataset ID  
- `table_id` (str): BigQuery table ID
- `bucket_name` (str): GCS bucket name
- `destination_blob_name` (str): Output file name

**Features:**
- GZIP compression for transfer
- UTF-8 BOM encoding for Excel compatibility
- Automatic header inclusion
- Temporary file cleanup

**Example:**
```python
export_bigquery_table_to_csv(
    project_id='pnj-material-planing',
    dataset_id='TESTING_MRP', 
    table_id='STEP_3_PHAN_RA_NI_OUTPUT_N',
    bucket_name='mrp-exports',
    destination_blob_name='production_orders.csv'
)
```

### Utility Functions

#### `get_job_sde_from_gcp(view_name: str) -> tuple`

Retrieves ETL job configuration from BigQuery view.

**Returns:**
```python
(JOB_ID, SOURCE_SCHEMA, SOURCE_TABLE, TARGET_SCHEMA, TARGET_TABLE, 
 SOURCE_COMMAND, TARGET_COMMAND, COUNT_EXTRACT_COMMAND, FULL_LOAD_FLG, 
 PRIORITY, DATASOURCE_ID, RUN_JOB, PARTITION_FIELD)
```

#### `count_table_gcp(table_id: str) -> int`

Returns row count for specified BigQuery table.

**Example:**
```python
row_count = count_table_gcp('pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY')
print(f"Table contains {row_count} rows")
```

---

## Optimization Engine API

Module: [`main.py`](../main.py)

### Step 1: Product Disaggregation

#### Variables Definition

```python
from ortools.linear_solver import pywraplp

# Create solver instance
solver = pywraplp.Solver.CreateSolver("SCIP")

# Define decision variables
variables_product_demand = {}  # Product allocation variables
infinity = solver.infinity()

# Create integer variables for each product
for product in products:
    variables_product_demand[product] = solver.IntVar(
        0.0, infinity, f'product_{product}'
    )
```

#### Constraint Definition

```python
# Demand constraints: allocation cannot exceed demand
for basic_new, pfsap, demand, products in demand_groups:
    solver.Add(
        sum(variables_product_demand[product] for product in products) <= demand
    )

# Inventory constraints: component usage cannot exceed stock
for material, stock, components in material_groups:
    total_usage = []
    for product, component_qty in components:
        total_usage.append(variables_product_demand[product] * component_qty)
    solver.Add(sum(total_usage) <= stock)
```

#### Objective Function

```python
# Maximize stone utilization and product output
objective_terms = []

# Component utilization terms
for product, component_qty in all_components:
    objective_terms.append(variables_product_demand[product] * component_qty)

# Product output terms  
for product in all_products:
    objective_terms.append(variables_product_demand[product])

# Set objective
solver.Maximize(solver.Sum(objective_terms))
```

#### Solver Configuration

```python
# Set optimization parameters
gap = 0.001  # 0.1% optimality gap
solver_parameters = pywraplp.MPSolverParameters()
solver_parameters.SetDoubleParam(solver_parameters.RELATIVE_MIP_GAP, gap)

# Solve optimization problem
status = solver.Solve(solver_parameters)

# Check solution status
if status == pywraplp.Solver.OPTIMAL:
    print("Optimal solution found")
elif status == pywraplp.Solver.FEASIBLE:
    print("Feasible solution found")
else:
    print(f"Solver failed with status: {status}")
```

### Step 3: Size Distribution Optimization

#### Variables Definition

```python
# Size allocation variables
variables_pb_ni = {}    # Integer variables for size allocation
variables_z = {}        # Continuous variables for target deviation
variables_z1 = {}       # Continuous variables for sales deviation

for product_size in product_sizes:
    variables_pb_ni[product_size] = solver.IntVar(0.0, infinity, f'ni_{product_size}')
    variables_z[product_size] = solver.NumVar(0.0, infinity, f'z_{product_size}')
    variables_z1[product_size] = solver.NumVar(0.0, infinity, f'z1_{product_size}')
```

#### Constraint Definition

```python
# Allocation balance constraints
for product, pb_product, sizes in product_groups:
    size_vars = [variables_pb_ni[f'{product}.{size}'] for size in sizes]
    solver.Add(sum(size_vars) <= pb_product)
    solver.Add(sum(size_vars) >= pb_product)

# Target deviation constraints
for product_size, inv, position, target in size_data:
    var_ni = variables_pb_ni[product_size]
    var_z = variables_z[product_size]
    
    # Absolute deviation from inventory position target
    solver.Add(((var_ni + inv) / position) - target <= var_z)
    solver.Add(target - ((var_ni + inv) / position) <= var_z)

# Sales velocity constraints
for product_size, inv, avg_sales in sales_data:
    var_ni = variables_pb_ni[product_size]
    var_z1 = variables_z1[product_size]
    
    # Maintain 3-month inventory target
    solver.Add(((var_ni + inv) / avg_sales) - 3 <= var_z1)
    solver.Add(3 - ((var_ni + inv) / avg_sales) <= var_z1)
```

#### Objective Function

```python
# Minimize weighted deviations
objective_terms = []

for product_size, target_ratio in target_ratios:
    z = variables_z[product_size]
    z1 = variables_z1[product_size]
    
    # Weighted penalty function
    objective_terms.append(z + z + z1 * target_ratio)

# Set minimization objective
solver.Minimize(solver.Sum(objective_terms))
```

---

## Data Structures

### Input Data Structures

#### BOM Data Structure

```python
# DataFrame structure for Step 1 input
bom_columns = {
    'BASIC_NEW_2': 'str',        # Product family ID
    'PFSAP': 'str',              # Product structure code  
    'D0': 'int64',               # Demand quantity
    'PRODUCT_CODE_LEFT_13': 'str', # Product code (13 chars)
    'COMP_MAT_CODE': 'str',      # Component material code
    'COMPONENT_QTY': 'float64',  # Component quantity required
    'STOCK_AVAILABLE': 'int64'   # Available inventory
}
```

#### Sales Analytics Structure

```python
# DataFrame structure for Step 3 input
sales_columns = {
    'BASIC_NEW_2': 'str',        # Product family ID
    'PFSAP': 'str',              # Product structure code
    'PRODUCT_CODE_LEFT_13': 'str', # Product code
    'KHUNG_NI_BASIC': 'str',     # Size framework
    'PB_PRODUCT': 'int64',       # Allocated product quantity
    'INV_AVAILABLE': 'int64',    # Available inventory
    'ORG_SALES': 'float64',      # Original sales (6-month)
    'AVG_SALES': 'float64',      # Average monthly sales
    'TT_BASIC': 'float64',       # Target ratio
    'INV_POSITION': 'int64'      # Inventory position
}
```

### Output Data Structures

#### Step 1 Output

```python
# Product disaggregation results
step1_output = {
    'BASIC_NEW_2': 'str',
    'PFSAP': 'str', 
    'D0': 'int64',
    'PRODUCT_CODE_LEFT_13': 'str',
    'COMP_MAT_CODE': 'str',
    'COMPONENT_QTY': 'int64',
    'STOCK_AVAIL': 'int64',
    'PB_PRODUCT': 'int64',       # Allocated product quantity
    'PB_COMP': 'int64'           # Allocated component quantity
}
```

#### Step 3 Output

```python
# Size distribution results
step3_output = {
    'BASIC_NEW_2': 'str',
    'PFSAP': 'str',
    'PRODUCT_CODE_LEFT_13': 'str',
    'KHUNG_NI_BASIC': 'str',
    'PB_PRODUCT': 'int64',
    'PB_NI': 'int64',            # Allocated size quantity
    'INV_AVAILABLE': 'int64',
    'ORG_SALES': 'float64',
    'AVG_SALES': 'float64',
    'TT_BASIC': 'float64',
    'INV_POSITION': 'int64',
    'MATERIAL': 'str',
    'NOTE': 'str'
}
```

---

## Error Handling

### BigQuery Error Handling

```python
try:
    job = query_gcp("SELECT * FROM invalid_table")
    df = job.to_dataframe()
except google.cloud.exceptions.NotFound as e:
    print(f"Table not found: {e}")
except google.cloud.exceptions.BadRequest as e:
    print(f"Invalid query: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Optimization Error Handling

```python
# Check solver status
status = solver.Solve(solver_parameters)

if status == pywraplp.Solver.OPTIMAL:
    print("Optimal solution found")
    # Extract solution
    for product, variable in variables_product_demand.items():
        quantity = variable.solution_value()
        if quantity > 0:
            print(f"Product {product}: {quantity}")
            
elif status == pywraplp.Solver.FEASIBLE:
    print("Feasible solution found (not optimal)")
    # Still extract solution
    
elif status == pywraplp.Solver.INFEASIBLE:
    print("Problem is infeasible - no solution exists")
    # Check constraints for conflicts
    
elif status == pywraplp.Solver.UNBOUNDED:
    print("Problem is unbounded")
    # Review objective function
    
else:
    print(f"Solver failed with status: {status}")
    # Check input data and constraints
```

### Data Validation

```python
import pandas as pd
import warnings

# Suppress pandas warnings
warnings.filterwarnings("ignore")

# Validate input data
def validate_bom_data(df):
    """Validate BOM DataFrame structure and content."""
    
    # Check required columns
    required_columns = ['BASIC_NEW_2', 'PFSAP', 'D0', 'PRODUCT_CODE_LEFT_13', 
                       'COMP_MAT_CODE', 'COMPONENT_QTY', 'STOCK_AVAILABLE']
    
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    # Check data types
    df['COMPONENT_QTY'] = df['COMPONENT_QTY'].apply(lambda x: float(x))
    df['STOCK_AVAIL'] = df['STOCK_AVAILABLE']
    
    # Handle negative inventory
    df.loc[df['STOCK_AVAILABLE'] < 0, 'STOCK_AVAILABLE'] = 0
    
    # Validate non-null values
    if df['COMPONENT_QTY'].isna().any():
        raise ValueError("Component quantities cannot be null")
    
    return df
```

---

## Usage Examples

### Complete Pipeline Execution

```python
from datetime import datetime
import pandas as pd
from ortools.linear_solver import pywraplp
from src.platform.gcp_client import query_gcp, call_procedure, upload_table

def run_optimization_pipeline():
    """Execute complete 3-step optimization pipeline."""
    
    start_time = datetime.now()
    print(f'Pipeline started at: {start_time}')
    
    try:
        # Step 1: Prepare BOM data
        print('Step 1: Preparing BOM data...')
        success = call_procedure(
            'CALL `pnj-material-planing.TESTING_MRP.PROD_STEP_1_PB_PRODUCT_QUERY`()'
        )
        
        if success != 1:
            raise Exception("Failed to execute Step 1 procedure")
        
        # Load prepared data
        df = query_gcp(
            "SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`"
        ).to_dataframe()
        
        print(f'Loaded {len(df)} BOM records')
        
        # Step 1: Optimize product disaggregation
        print('Step 1: Running product disaggregation...')
        result_step1 = optimize_product_disaggregation(df)
        
        # Upload Step 1 results
        upload_table(result_step1, 
                    'pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT')
        print('Step 1 completed successfully')
        
        # Step 2: Calculate material requirements
        print('Step 2: Calculating material requirements...')
        result_step2 = calculate_material_requirements(result_step1)
        
        upload_table(result_step2,
                    'pnj-material-planing.TESTING_MRP.STEP_2_MUAMOI_NVL_OUTPUT')
        print('Step 2 completed successfully')
        
        # Step 3: Prepare sales analytics
        print('Step 3: Preparing sales analytics...')
        success = call_procedure(
            'CALL `pnj-material-planing.TESTING_MRP.PROD_STEP_3_PHAN_RA_NI_QUERY_N`()'
        )
        
        if success != 1:
            raise Exception("Failed to execute Step 3 procedure")
        
        # Load sales analytics data
        df_step3 = query_gcp(
            "SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_QUERY_N`"
        ).to_dataframe()
        
        print(f'Loaded {len(df_step3)} sales analytics records')
        
        # Step 3: Optimize size distribution
        print('Step 3: Running size distribution optimization...')
        result_step3 = optimize_size_distribution(df_step3)
        
        upload_table(result_step3,
                    'pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_OUTPUT_N')
        print('Step 3 completed successfully')
        
        end_time = datetime.now()
        duration = end_time - start_time
        print(f'Pipeline completed in: {duration}')
        
        return {
            'status': 'success',
            'duration': duration,
            'step1_records': len(result_step1),
            'step2_records': len(result_step2), 
            'step3_records': len(result_step3)
        }
        
    except Exception as e:
        end_time = datetime.now()
        duration = end_time - start_time
        print(f'Pipeline failed after: {duration}')
        print(f'Error: {str(e)}')
        
        return {
            'status': 'failed',
            'duration': duration,
            'error': str(e)
        }

# Execute pipeline
if __name__ == "__main__":
    result = run_optimization_pipeline()
    print(f"Pipeline result: {result}")
```

### Custom Optimization Example

```python
def optimize_custom_product_set(product_filter=None, max_runtime=3600):
    """Run optimization for specific product subset."""
    
    # Custom query with filter
    query = f"""
    SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`
    WHERE BASIC_NEW_2 LIKE '{product_filter}%'
    """ if product_filter else """
    SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`
    """
    
    df = query_gcp(query).to_dataframe()
    print(f'Optimizing {len(df)} records')
    
    # Create solver with custom timeout
    solver = pywraplp.Solver.CreateSolver("SCIP")
    solver_parameters = pywraplp.MPSolverParameters()
    solver_parameters.SetDoubleParam(solver_parameters.TIME_LIMIT, max_runtime)
    
    # ... optimization logic ...
    
    status = solver.Solve(solver_parameters)
    
    if status == pywraplp.Solver.OPTIMAL:
        print("Found optimal solution")
    elif status == pywraplp.Solver.FEASIBLE:
        print("Found feasible solution within time limit")
    else:
        print(f"Optimization failed: {status}")
    
    return extract_solution(solver, variables_product_demand)

# Run custom optimization
result = optimize_custom_product_set(
    product_filter="GNDD00H",  # Diamond jewelry only
    max_runtime=1800           # 30 minutes max
)
```

---

**API Reference Version**: 1.0  
**Last Updated**: January 2025  
**Compatibility**: Python 3.11+, OR-Tools 9.7+, Google Cloud BigQuery API v2  

For additional examples and advanced usage patterns, see the main [README.md](../README.md) documentation.