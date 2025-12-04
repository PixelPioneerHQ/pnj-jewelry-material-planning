from datetime import datetime

import pandas as pd
from ortools.linear_solver import pywraplp
import csv
import tempfile
import gzip
import time
import random
import warnings
from src.platform.gcp_client import query_gcp, load_table_from_df, call_procedure, upload_table, export_bigquery_table_to_csv
start_time = datetime.now()
print('Step 1 start')
# Step1: disagg with available stock
a = call_procedure(
    'CALL `pnj-material-planing.TESTING_MRP.PROD_STEP_1_PB_PRODUCT_QUERY`()')
print(a)
df = query_gcp(
    """SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_QUERY` """).to_dataframe()


warnings.filterwarnings("ignore")
df['COMPONENT_QTY'] = df['COMPONENT_QTY'].apply(lambda x: float(x))
df['STOCK_AVAIL'] = df['STOCK_AVAILABLE']
df.loc[df['STOCK_AVAILABLE'] < 0, 'STOCK_AVAILABLE'] = 0

solver = pywraplp.Solver.CreateSolver("SCIP")
variables_product_demand = {}
infinity = solver.infinity()

for data in df[['BASIC_NEW_2', 'PFSAP', 'D0', 'PRODUCT_CODE_LEFT_13']].groupby(['BASIC_NEW_2', 'PFSAP']):
    demand = float(data[1].iloc[0].D0)
    for product in data[1].PRODUCT_CODE_LEFT_13.unique():
        variables_product_demand[product] = solver.IntVar(
            0.0, infinity, f'product_{product}')
    solver.Add(sum(variables_product_demand[product]
               for product in data[1].PRODUCT_CODE_LEFT_13.unique()) <= demand)
objective = []
for data in df[['PRODUCT_CODE_LEFT_13', 'COMP_MAT_CODE', 'COMPONENT_QTY', 'STOCK_AVAILABLE']].groupby(['COMP_MAT_CODE']):
    total_required_component = []
    stock_available = data[1].iloc[0].STOCK_AVAILABLE
    for i, row in data[1].iterrows():
        component_qty = row.COMPONENT_QTY
        product = row.PRODUCT_CODE_LEFT_13
        total_required_component.append(
            variables_product_demand[product] * component_qty)
        objective.append(variables_product_demand[product] * component_qty)
    solver.Add(sum(total_required_component) <= stock_available)

solver.Maximize(solver.Sum(objective + [variables_product_demand[product]
                for product in df.PRODUCT_CODE_LEFT_13.unique()]))
gap = 0.001
solver_parameters = pywraplp.MPSolverParameters()
solver_parameters.SetDoubleParam(solver_parameters.RELATIVE_MIP_GAP, gap)
status = solver.Solve(solver_parameters)
# print ("Solver status:", status)
# print("Optimal:", pywraplp.Solver.OPTIMAL)

total_product = 0
total_material = 0
num_pos = 0
material = 0
for product in df.PRODUCT_CODE_LEFT_13.unique():
    total_product += variables_product_demand[product].solution_value()
    if variables_product_demand[product].solution_value() > 0:
        num_pos += 1
for prod_mat in objective:
    total_material += prod_mat.solution_value()
# print ("Product disagg:", total_product)
# print ("Stone usage:", total_material)
# print (f'{num_pos}/{len(df.PRODUCT_CODE_LEFT_13.unique())}')

map_product = {}
for product_code, product_variable in variables_product_demand.items():
    map_product[product_code] = int(product_variable.solution_value())

df_basic_product = df[['BASIC_NEW_2', 'PFSAP',
                       'D0', 'PRODUCT_CODE_LEFT_13']].copy(deep=True)
df_basic_product['PB_PRODUCT'] = df_basic_product.PRODUCT_CODE_LEFT_13.map(
    map_product)
df_basic_product.drop_duplicates(inplace=True)

result = pd.merge(df_basic_product, df[['PRODUCT_CODE_LEFT_13', 'COMP_MAT_CODE',
                  'COMPONENT_QTY', 'STOCK_AVAILABLE', 'STOCK_AVAIL']], on='PRODUCT_CODE_LEFT_13')
result['PB_COMP'] = result['PB_PRODUCT'] * result['COMPONENT_QTY']
for col in ['COMPONENT_QTY','STOCK_AVAILABLE','STOCK_AVAIL','PB_COMP']:
    result[col] = result[col].astype('int64')
# print ("Solver status step 1:", status)
# print("Optimal status step 1:", pywraplp.Solver.OPTIMAL)
# print ("Product disagg step 1:", total_product)
# print ("Stone usage step 1:", total_material)
upload_table(
    result, 'pnj-material-planing.TESTING_MRP.STEP_1_PB_PRODUCT_OUTPUT')
print('Step 1 finished')
print('Step 2 start')
warnings.filterwarnings("ignore")
df = result
df_basic = df[['BASIC_NEW_2', 'PFSAP',
               'PRODUCT_CODE_LEFT_13', 'PB_PRODUCT']].drop_duplicates()
df_basic = df_basic.groupby(['BASIC_NEW_2', 'PFSAP']).sum(
).reset_index().rename(columns={'PB_PRODUCT': 'PB_BASIC'})
df_comp = df[['COMP_MAT_CODE', 'PB_COMP']].groupby(
    'COMP_MAT_CODE').sum().reset_index().rename(columns={'PB_COMP': 'PB_COMP_SUM'})
df = df.merge(df_basic[['BASIC_NEW_2','PFSAP','PB_BASIC']], how='left', on=['BASIC_NEW_2', 'PFSAP'])
df = df.merge(df_comp, how='left', on=['COMP_MAT_CODE'])
df['D0_REST'] = df['D0'] - df['PB_BASIC']
df['STOCK_AFTER'] = df['STOCK_AVAILABLE'] - df['PB_COMP_SUM']
df_2 = df.loc[df.BASIC_NEW_2 == df.PRODUCT_CODE_LEFT_13]
df_2['REST_COMP'] = df_2['D0_REST']*df_2['COMPONENT_QTY']
df_2.rename(columns={'D0_REST': 'REST_PRODUCT'}, inplace=True)
df_2 = df_2[['PRODUCT_CODE_LEFT_13', 'COMP_MAT_CODE',
             'COMPONENT_QTY', 'REST_PRODUCT', 'REST_COMP']]
df = df.merge(df_2, how='left', on=[
              'PRODUCT_CODE_LEFT_13', 'COMP_MAT_CODE', 'COMPONENT_QTY'])
df = df[['BASIC_NEW_2', 'PFSAP', 'D0', 'PRODUCT_CODE_LEFT_13', 'COMP_MAT_CODE', 'COMPONENT_QTY',
         'STOCK_AVAIL', 'PB_PRODUCT', 'PB_COMP', 'STOCK_AFTER', 'REST_PRODUCT', 'REST_COMP']].fillna(0)


upload_table(df, 'pnj-material-planing.TESTING_MRP.STEP_2_MUAMOI_NVL_OUTPUT')
print('Step 2 finished')
print('Step 3 start')
call_procedure(
    'CALL `pnj-material-planing.TESTING_MRP.PROD_STEP_3_PHAN_RA_NI_QUERY_N`()')
df = query_gcp(
    """SELECT * FROM `pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_QUERY_N` """).to_dataframe()
solver = pywraplp.Solver.CreateSolver("SCIP")
# print(df)
variables_pb_ni = {}
variables_z = {}
variables_z1 = {}
infinity = solver.infinity()
list_obj = []
for data in df[['PRODUCT_CODE_LEFT_13', 'PB_PRODUCT', 'KHUNG_NI_BASIC', 'INV_AVAILABLE', 'ORG_SALES', 'AVG_SALES', 'TT_BASIC', 'INV_POSITION']].groupby('PRODUCT_CODE_LEFT_13'):
    pb_product = data[1].iloc[0].PB_PRODUCT
    list_ni = []
    for idx, ni in enumerate(data[1].KHUNG_NI_BASIC.unique()):
        inv = float(data[1].iloc[idx].INV_AVAILABLE)
        inv_position = float(data[1].iloc[idx].INV_POSITION)
        avg_sales = float(data[1].iloc[idx].AVG_SALES)
        tt_basic = float(data[1].iloc[idx].TT_BASIC)
        ten_ni = f'{data[0]}.{ni}'  # Remove reference to IS_MEN_JEWELRY
        variables_pb_ni[ten_ni] = solver.IntVar(
            0.0, infinity, f'khungni_{ten_ni}')
        variables_z[ten_ni] = solver.NumVar(0.0, infinity, f'z_{ten_ni}')
        variables_z1[ten_ni] = solver.NumVar(0.0, infinity, f'z_{ten_ni}')
        list_ni.append(variables_pb_ni[ten_ni])
        solver.Add(((variables_pb_ni[ten_ni] + inv) /
                   inv_position) - tt_basic <= variables_z[ten_ni])
        solver.Add(
            tt_basic - ((variables_pb_ni[ten_ni] + inv) / inv_position) <= variables_z[ten_ni])
        solver.Add(((variables_pb_ni[ten_ni] + inv) /
                   avg_sales) - 3 <= variables_z1[ten_ni])
        solver.Add(
            3 - ((variables_pb_ni[ten_ni] + inv) / avg_sales) <= variables_z1[ten_ni])
        list_obj.append(
            variables_z[ten_ni] + variables_z[ten_ni] + variables_z1[ten_ni] * tt_basic)
    solver.Add(sum(list_ni) <= pb_product)
    solver.Add(sum(list_ni) >= pb_product)

solver.Minimize(solver.Sum(list_obj))
status = solver.Solve()

for data in df[['PRODUCT_CODE_LEFT_13', 'PB_PRODUCT', 'KHUNG_NI_BASIC', 'INV_AVAILABLE', 'ORG_SALES', 'AVG_SALES', 'TT_BASIC', 'INV_POSITION']].groupby('PRODUCT_CODE_LEFT_13'):
    pb_product = data[1].iloc[0].PB_PRODUCT
    list_ni = []
    for idx, ni in enumerate(data[1].KHUNG_NI_BASIC.unique()):
        ten_ni = f'{data[0]}.{ni}'

for index, row in df.iterrows():
    ten_ni = f"{row['PRODUCT_CODE_LEFT_13']}.{row['KHUNG_NI_BASIC']}"
    df.at[index, 'PB_NI'] = variables_pb_ni[ten_ni].solution_value()

df["MATERIAL"].fillna("None", inplace=True)
df["NOTE"].fillna("None", inplace=True)
df['PB_NI'] = df['PB_NI'].apply(lambda x: int(x))

# print ("Solver status:", status)
# print("Optimal:", pywraplp.Solver.OPTIMAL)

upload_table(df, 'pnj-material-planing.TESTING_MRP.STEP_3_PHAN_RA_NI_OUTPUT_N')
print('Step 3 finished')
end_time = datetime.now()
# print('Duration: {}'.format(end_time - start_time))
