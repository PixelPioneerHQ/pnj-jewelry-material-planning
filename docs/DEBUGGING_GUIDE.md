# Debugging Guide - Constraint Violation Issues

## Problem: Over-allocation Beyond Demand Constraint

### Issue Description
The optimization system is allocating more product quantities than the actual demand, violating the fundamental constraint:
```
SUM(allocated_quantities) <= demand (D0)
```

**Example Case:**
- Product: `GNDDDDW011759`
- Demand (D0): 14
- Total Allocated (TOTAL_PB_NI): 20
- **Violation**: 20 > 14 ❌

---

## 🔍 Debugging Methodology

### Step 1: Verify Input Data Consistency

#### Check Demand Data
```sql
-- Verify demand input for specific product
SELECT 
    BASIC_NEW_2,
    PFSAP,
    SUM(SL) as TOTAL_DEMAND
FROM `pnj-material-planing.INPUT_MATERIAL_PLANING.D0_TEST`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
GROUP BY BASIC_NEW_2, PFSAP;
```

#### Check Step 1 Input Processing
```sql
-- Verify how demand flows into Step 1
SELECT 
    BASIC_NEW_2,
    PFSAP,
    D0,
    COUNT(DISTINCT PRODUCT_CODE_LEFT_13) as PRODUCT_VARIANTS,
    SUM(COMPONENT_QTY) as TOTAL_COMPONENT_REQUIRED
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
GROUP BY BASIC_NEW_2, PFSAP, D0;
```

### Step 2: Analyze Step 1 Optimization Logic

#### Check Constraint Implementation in Python

**File: [`main.py`](../main.py) Lines 31-37**

```python
# Current constraint implementation
for data in df[['BASIC_NEW_2', 'PFSAP', 'D0', 'PRODUCT_CODE_LEFT_13']].groupby(['BASIC_NEW_2', 'PFSAP']):
    demand = float(data[1].iloc[0].D0)
    for product in data[1].PRODUCT_CODE_LEFT_13.unique():
        variables_product_demand[product] = solver.IntVar(
            0.0, infinity, f'product_{product}')
    solver.Add(sum(variables_product_demand[product]
               for product in data[1].PRODUCT_CODE_LEFT_13.unique()) <= demand)
```

#### Debugging Step 1 Variables and Constraints

Add this debugging code to [`main.py`](../main.py) after line 37:

```python
# DEBUG: Add constraint verification
debug_constraints = {}
for data in df[['BASIC_NEW_2', 'PFSAP', 'D0', 'PRODUCT_CODE_LEFT_13']].groupby(['BASIC_NEW_2', 'PFSAP']):
    basic_new_2 = data[0][0]
    pfsap = data[0][1]
    demand = float(data[1].iloc[0].D0)
    products = data[1].PRODUCT_CODE_LEFT_13.unique()
    
    debug_constraints[f"{basic_new_2}_{pfsap}"] = {
        'demand': demand,
        'products': list(products),
        'product_count': len(products)
    }
    
    print(f"DEBUG CONSTRAINT: {basic_new_2} - Demand: {demand}, Products: {len(products)}")

# Save debug info for analysis
import json
with open('debug_constraints.json', 'w') as f:
    json.dump(debug_constraints, f, indent=2)
```

#### Verify Step 1 Results

```sql
-- Check Step 1 output for constraint violations
SELECT 
    BASIC_NEW_2,
    PFSAP,
    D0,
    COUNT(DISTINCT PRODUCT_CODE_LEFT_13) as PRODUCT_VARIANTS,
    SUM(PB_PRODUCT) as TOTAL_PB_PRODUCT,
    CASE 
        WHEN SUM(PB_PRODUCT) > D0 THEN 'VIOLATION'
        ELSE 'OK'
    END as CONSTRAINT_STATUS
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT`
GROUP BY BASIC_NEW_2, PFSAP, D0
HAVING SUM(PB_PRODUCT) > D0
ORDER BY (SUM(PB_PRODUCT) - D0) DESC;
```

### Step 3: Debug Data Flow Between Steps

#### Trace Product Flow Step 1 → Step 2 → Step 3

```sql
-- Step 1 to Step 2 flow
SELECT 
    'STEP_1' as step,
    BASIC_NEW_2,
    PFSAP,
    D0,
    SUM(PB_PRODUCT) as TOTAL_ALLOCATED
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
GROUP BY BASIC_NEW_2, PFSAP, D0

UNION ALL

SELECT 
    'STEP_2' as step,
    BASIC_NEW_2,
    PFSAP,
    D0,
    SUM(PB_PRODUCT) as TOTAL_ALLOCATED
FROM `pnj-material-planing.TESTING_MRP.STEP_2_MUAMOI_NVL_OUTPUT`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
GROUP BY BASIC_NEW_2, PFSAP, D0

UNION ALL

SELECT 
    'STEP_3_INPUT' as step,
    BASIC_NEW_2,
    PFSAP,
    NULL as D0,
    SUM(PB_PRODUCT) as TOTAL_ALLOCATED
FROM `pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_QUERY_N`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
GROUP BY BASIC_NEW_2, PFSAP

UNION ALL

SELECT 
    'STEP_3_OUTPUT' as step,
    BASIC_NEW_2,
    PFSAP,
    NULL as D0,
    SUM(PB_NI) as TOTAL_ALLOCATED
FROM `pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_OUTPUT_N`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
GROUP BY BASIC_NEW_2, PFSAP

ORDER BY step;
```

### Step 4: Debug Step 3 Size Distribution Logic

#### Check Step 3 Constraint Implementation

**File: [`main.py`](../main.py) Lines 156-158**

```python
# Current Step 3 constraints
solver.Add(sum(list_ni) <= pb_product)
solver.Add(sum(list_ni) >= pb_product)
```

#### Add Step 3 Debugging

Add this debugging code to [`main.py`](../main.py) after line 158:

```python
# DEBUG: Step 3 constraint verification
debug_step3 = {}
for data in df[['PRODUCT_CODE_LEFT_13', 'PB_PRODUCT', 'KHUNG_NI_BASIC', 'INV_AVAILABLE', 'ORG_SALES', 'AVG_SALES', 'TT_BASIC', 'INV_POSITION']].groupby('PRODUCT_CODE_LEFT_13'):
    product = data[0]
    pb_product = data[1].iloc[0].PB_PRODUCT
    size_count = len(data[1].KHUNG_NI_BASIC.unique())
    
    debug_step3[product] = {
        'pb_product': pb_product,
        'size_frameworks': list(data[1].KHUNG_NI_BASIC.unique()),
        'size_count': size_count
    }
    
    print(f"DEBUG STEP3: {product} - PB_PRODUCT: {pb_product}, Sizes: {size_count}")

# Save debug info
with open('debug_step3.json', 'w') as f:
    json.dump(debug_step3, f, indent=2)
```

---

## 🐛 Common Root Causes

### 1. **Demand Aggregation Error**
- Multiple PFSAP values for same BASIC_NEW_2 not properly grouped
- Demand (D0) miscalculated in BigQuery procedure

#### Fix: Check NHUCAU CTE in Step 1 Procedure
```sql
-- In PROD_STEP_1_PB_PRODUCT_QUERY.SQL around line 155
-- Verify this aggregation is correct:
SELECT B.BASIC_NEW_2
    ,M.PFSAP
    ,B.PRODUCT_FAMILY
    ,M.BASIC_NEW_CODE
    ,SUM(A.SL) AS D0  -- This should be the total demand
FROM `pnj-material-planing.INPUT_MATERIAL_PLANING.D0_TEST` A
-- ... rest of query
GROUP BY 1, 2, 3, 4  -- Make sure grouping is correct
```

### 2. **Solver Constraint Bug**
- Constraint not properly implemented in OR-Tools
- Variables not correctly mapped to constraints

#### Fix: Enhanced Constraint Validation
```python
# Replace current constraint logic in main.py
for data in df[['BASIC_NEW_2', 'PFSAP', 'D0', 'PRODUCT_CODE_LEFT_13']].groupby(['BASIC_NEW_2', 'PFSAP']):
    basic_new_2, pfsap = data[0]
    demand = float(data[1].iloc[0].D0)
    products = data[1].PRODUCT_CODE_LEFT_13.unique()
    
    # Create variables for each product
    product_vars = []
    for product in products:
        var = solver.IntVar(0.0, demand, f'product_{product}')  # Upper bound = demand
        variables_product_demand[product] = var
        product_vars.append(var)
    
    # Add demand constraint with validation
    constraint = solver.Add(sum(product_vars) <= demand)
    print(f"Added constraint for {basic_new_2}_{pfsap}: sum(products) <= {demand}")
    
    # Add constraint name for debugging
    constraint.SetName(f"demand_constraint_{basic_new_2}_{pfsap}")
```

### 3. **Data Duplication in Step 3**
- Product codes counted multiple times across different size frameworks
- Aggregation error in Step 3 procedure

#### Fix: Check Step 3 Aggregation Logic
```sql
-- In PROD_STEP_3_PHAN_RA_NI_QUERY_N, verify this section:
SELECT DISTINCT A.BASIC_NEW_2
  , A.PFSAP
  , A.D0
  , A.PRODUCT_CODE_LEFT_13
  , A.PB_PRODUCT   -- This should be consistent per product
FROM `pnj-material-planing.TESTING_MRP.STEP_2_MUAMOI_NVL_OUTPUT` A
WHERE A.PB_PRODUCT > 0
```

### 4. **Step 2 Data Transformation Error**
- PB_PRODUCT values incorrectly modified in Step 2
- Data duplication during merging operations

---

## 🔧 Immediate Fixes

### 1. Add Validation Checks

Create validation function in [`main.py`](../main.py):

```python
def validate_constraints(df_input, df_output, step_name):
    """Validate that constraints are not violated."""
    print(f"\n=== VALIDATION: {step_name} ===")
    
    # Group by BASIC_NEW_2, PFSAP for validation
    input_summary = df_input.groupby(['BASIC_NEW_2', 'PFSAP']).agg({
        'D0': 'first'
    }).reset_index()
    
    output_summary = df_output.groupby(['BASIC_NEW_2', 'PFSAP']).agg({
        'PB_PRODUCT': 'sum' if 'PB_PRODUCT' in df_output.columns else 'PB_NI': 'sum'
    }).reset_index()
    
    # Merge and check violations
    merged = pd.merge(input_summary, output_summary, on=['BASIC_NEW_2', 'PFSAP'])
    
    violation_col = 'PB_PRODUCT' if 'PB_PRODUCT' in merged.columns else 'PB_NI'
    violations = merged[merged[violation_col] > merged['D0']]
    
    if len(violations) > 0:
        print(f"❌ CONSTRAINT VIOLATIONS FOUND: {len(violations)}")
        print(violations[['BASIC_NEW_2', 'PFSAP', 'D0', violation_col]])
        
        # Save violations for analysis
        violations.to_csv(f'violations_{step_name}.csv', index=False)
        return False
    else:
        print(f"✅ No constraint violations in {step_name}")
        return True

# Add after each step
validate_constraints(df, result, "STEP_1")  # After Step 1
validate_constraints(result, df, "STEP_3")   # After Step 3
```

### 2. Enhanced Debugging Output

Add comprehensive logging in [`main.py`](../main.py):

```python
# Add after optimization solve
print(f"\n=== SOLVER RESULTS ===")
print(f"Solver status: {status}")
print(f"Optimal status: {pywraplp.Solver.OPTIMAL}")
print(f"Total products allocated: {total_product}")
print(f"Total stone usage: {total_material}")

# Check for specific violations
violation_products = []
for product_code, product_variable in variables_product_demand.items():
    allocated = int(product_variable.solution_value())
    if allocated > 0:
        # Find corresponding demand
        product_demand = df[df['PRODUCT_CODE_LEFT_13'] == product_code]['D0'].iloc[0]
        print(f"Product {product_code}: allocated={allocated}")
        
        if allocated > product_demand:
            violation_products.append({
                'product': product_code,
                'allocated': allocated,
                'demand': product_demand
            })

if violation_products:
    print(f"\n❌ INDIVIDUAL PRODUCT VIOLATIONS: {len(violation_products)}")
    for viol in violation_products:
        print(f"  {viol['product']}: {viol['allocated']} > {viol['demand']}")
```

---

## 🔍 Analysis Queries

### Query 1: Find All Constraint Violations
```sql
WITH step1_summary AS (
  SELECT 
    BASIC_NEW_2,
    PFSAP,
    D0,
    SUM(PB_PRODUCT) as TOTAL_PB_PRODUCT
  FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT`
  GROUP BY BASIC_NEW_2, PFSAP, D0
),
step3_summary AS (
  SELECT 
    BASIC_NEW_2,
    PFSAP,
    SUM(PB_NI) as TOTAL_PB_NI
  FROM `pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_OUTPUT_N`
  GROUP BY BASIC_NEW_2, PFSAP
)
SELECT 
  s1.BASIC_NEW_2,
  s1.PFSAP,
  s1.D0,
  s1.TOTAL_PB_PRODUCT,
  s3.TOTAL_PB_NI,
  CASE 
    WHEN s1.TOTAL_PB_PRODUCT > s1.D0 THEN 'STEP1_VIOLATION'
    WHEN s3.TOTAL_PB_NI > s1.D0 THEN 'STEP3_VIOLATION'
    WHEN s3.TOTAL_PB_NI > s1.TOTAL_PB_PRODUCT THEN 'STEP3_INCREASE'
    ELSE 'OK'
  END as STATUS
FROM step1_summary s1
LEFT JOIN step3_summary s3 ON s1.BASIC_NEW_2 = s3.BASIC_NEW_2 AND s1.PFSAP = s3.PFSAP
WHERE s1.TOTAL_PB_PRODUCT > s1.D0 
   OR s3.TOTAL_PB_NI > s1.D0
   OR s3.TOTAL_PB_NI > s1.TOTAL_PB_PRODUCT
ORDER BY (COALESCE(s3.TOTAL_PB_NI, s1.TOTAL_PB_PRODUCT) - s1.D0) DESC;
```

### Query 2: Detailed Product-Level Analysis
```sql
SELECT 
  BASIC_NEW_2,
  PFSAP,
  PRODUCT_CODE_LEFT_13,
  D0,
  PB_PRODUCT,
  CASE WHEN PB_PRODUCT > D0 THEN 'VIOLATION' ELSE 'OK' END as STATUS
FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT`
WHERE BASIC_NEW_2 = 'GNDDDDW011759'
ORDER BY PB_PRODUCT DESC;
```

---

## 📋 Debugging Checklist

- [ ] **Verify input demand data consistency**
- [ ] **Check Step 1 constraint implementation** 
- [ ] **Validate Step 1 output against demand**
- [ ] **Trace data flow through Steps 1-2-3**
- [ ] **Check Step 3 aggregation logic**
- [ ] **Add validation functions to code**
- [ ] **Run analysis queries to identify patterns**
- [ ] **Test with single product to isolate issue**
- [ ] **Review BigQuery procedure logic**
- [ ] **Check for data duplication**

## 🚨 Next Steps

1. **Run the analysis queries** to identify all violations
2. **Add debugging code** to Step 1 and Step 3 optimization
3. **Check the BigQuery procedures** for aggregation errors
4. **Validate constraint implementation** in OR-Tools
5. **Test with a subset** of products to isolate the issue

The most likely root cause is either a **constraint implementation bug** in the Python optimization code or a **data aggregation error** in the BigQuery procedures that's causing demand values to be incorrect.