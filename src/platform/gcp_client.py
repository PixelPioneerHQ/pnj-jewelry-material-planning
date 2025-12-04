import time
import random
import os
from google.cloud import bigquery
from google.cloud import storage
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "D:/git/Docker-Material-Planing-N/enhance/SA/service_account.json"
def query_gcp(query):
    client = bigquery.Client()
    query_job = client.query(query)
    query_job.result()
    return query_job
def call_procedure(query):
    bigquery_client = bigquery.Client()
    query = """{};""".format(query)
    try:
        query_job = bigquery_client.query(query)
        query_job.result()
        is_success = 1
    except:
        is_success = 0
    return is_success
def get_job_sde_from_gcp(view_name):
    bigquery_client = bigquery.Client()
    query = """
    SELECT *
    FROM `{}`
    LIMIT 1""".format(view_name)
    query_job = bigquery_client.query(query) 
    query_job.result()
    for row in query_job:
        JOB_ID = row["JOB_ID"]
        SOURCE_SCHEMA = row["SOURCE_SCHEMA"]
        SOURCE_TABLE = row["SOURCE_TABLE"]
        TARGET_SCHEMA = row["TARGET_SCHEMA"]
        TARGET_TABLE = row["TARGET_TABLE"]
        SOURCE_COMMAND = row["SOURCE_COMMAND"]
        TARGET_COMMAND = row["TARGET_COMMAND"]
        COUNT_EXTRACT_COMMAND = row["COUNT_EXTRACT_COMMAND"]
        FULL_LOAD_FLG = row["FULL_LOAD_FLG"]
        PRIORITY = row["PRIORITY"]
        DATASOURCE_ID = row["DATASOURCE_ID"]
        RUN_JOB = row["RUN_JOB"]
        PARTITION_FIELD = row["PARTITION_FIELD"]
    return JOB_ID,SOURCE_SCHEMA,SOURCE_TABLE,TARGET_SCHEMA,TARGET_TABLE,SOURCE_COMMAND,TARGET_COMMAND,COUNT_EXTRACT_COMMAND,FULL_LOAD_FLG,PRIORITY,DATASOURCE_ID,RUN_JOB,PARTITION_FIELD
def count_table_gcp(table_id):
    bigquery_client = bigquery.Client()
    query = """
    SELECT count(*)
    FROM `{}`""".format(table_id)
    query_job = bigquery_client.query(query) 
    query_job.result()
    for row in query_job:
        count_initital = row[0]
    return count_initital
def get_batch_code(date_now):
    bigquery_client = bigquery.Client()
    query_batch = """
    SELECT *
    FROM `ADLOG.BATCH_LOG`
    WHERE SUBSTR(cast(BATCH_CODE as string),1,8) = '{}'
            AND BATCH_STATUS = 'Start'
    ORDER BY BATCH_CODE DESC
    LIMIT 1""".format(date_now)
    query_job = bigquery_client.query(query_batch) 
    query_job.result()
    for row in query_job:
        code = row[0]
    return code
def flag_run_job(JOB_ID):
    client = bigquery.Client()
    query = """UPDATE `ADLOG.ETL_JOB` SET RUN_JOB = 'Y' WHERE JOB_ID = {}""".format(JOB_ID)
    query_job = client.query(query)
    query_job.result()
    return query_job
def refesh_job_before_start_batch():
    client = bigquery.Client()
    query = """UPDATE `ADLOG.ETL_JOB` SET RUN_JOB = 'N' WHERE 1 = 1"""
    query_job = client.query(query)
    query_job.result()
    return 1
def get_job_sil_from_gcp(view_name):
    dict_job = {}
    bigquery_client = bigquery.Client()
    query_job_sde = """
    SELECT *
    FROM `{}`""".format(view_name)
    query_job = bigquery_client.query(query_job_sde) 
    query_job.result()
    for row in query_job:
        dict_job[row["JOB_ID"]] = {"SOURCE_SCHEMA" : row["SOURCE_SCHEMA"],
        "SOURCE_TABLE" : row["SOURCE_TABLE"],
        "TARGET_SCHEMA" : row["TARGET_SCHEMA"],
        "TARGET_TABLE" : row["TARGET_TABLE"],
        "SOURCE_COMMAND" : row["SOURCE_COMMAND"],
        "TARGET_COMMAND" : row["TARGET_COMMAND"],
        "COUNT_EXTRACT_COMMAND" : row["COUNT_EXTRACT_COMMAND"],
        "FULL_LOAD_FLG" : row["FULL_LOAD_FLG"],
        "PRIORITY" : row["PRIORITY"],
        "DATASOURCE_ID" : row["DATASOURCE_ID"],
        "RUN_JOB" : row["RUN_JOB"],
        "PARTITION_FIELD" : row["PARTITION_FIELD"]}
    return dict_job
def load_table_from_df(df,target_table_name):
    client = bigquery.Client()
    table = client.get_table(target_table_name)
    a = 0
    while a <3:
        try :
            job_config = bigquery.LoadJobConfig(
                        schema = table.schema,
                        autodetect=True,
                        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    )
            job = client.load_table_from_dataframe(
                        df, target_table_name , job_config=job_config
                    )  # Make an API request.
    
            job.result()
            break;
        except:
            print('Fail : {}'.format(a))
            time.sleep(random.randint(5, 10))
            a += 1
    return 1
def upload_table(df,target_table_name):
    client = bigquery.Client()
    table = client.get_table(target_table_name)

    job_config = bigquery.LoadJobConfig(
                schema = table.schema,
                autodetect=True,
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            )
    job = client.load_table_from_dataframe(
                df, target_table_name , job_config=job_config
            )
    job.result()
    print("Upload table successfully!")

def export_bigquery_table_to_csv(project_id, dataset_id, table_id, bucket_name, destination_blob_name):
    bq_client = bigquery.Client(project=project_id)
    storage_client = storage.Client(project=project_id)
    table_ref = bq_client.dataset(dataset_id).table(table_id)
    job_config = bigquery.ExtractJobConfig()
    job_config.destination_format = bigquery.DestinationFormat.CSV
    job_config.field_delimiter = ","
    job_config.print_header = True
    job_config.compression = bigquery.Compression.GZIP
    destination_uri = "gs://{}/{}".format(bucket_name, destination_blob_name)

    extract_job = bq_client.extract_table(
        table_ref,
        destination_uri,
        job_config=job_config
    )
    extract_job.result()
    temp_filename = tempfile.mktemp()
    blob = storage_client.bucket(bucket_name).blob(destination_blob_name)
    blob.download_to_filename(temp_filename)
    decompressed_filename = tempfile.mktemp()
    with gzip.open(temp_filename, 'rb') as f_in:
        with open(decompressed_filename, 'wb') as f_out:
            f_out.write(f_in.read())

    # Add BOM character to the file for UTF-8 encoding
    with open(decompressed_filename, "r", encoding="utf-8") as file:
        content = file.read()
    with open(decompressed_filename, "w", encoding="utf-8-sig") as file:
        file.write("\ufeff")
        file.write(content)

    # Upload the modified file back to Cloud Storage
    blob.upload_from_filename(decompressed_filename)

    print("Table exported successfully to: {}".format(destination_uri))