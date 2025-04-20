To properly configure a Glue table for Parquet format data, you need to update the configuration with Parquet-specific
settings. Here's how to create a Glue table for Parquet data and then access it using Python/PySpark:

## Creating a Glue Table for Parquet Data

```python
import boto3

glue_client = boto3.client('glue')

# Create table definition for Parquet data
response = glue_client.create_table(
    DatabaseName='my_etl_database',
    TableInput={
        'Name': 'my_parquet_table',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'column1', 'Type': 'string'},
                {'Name': 'column2', 'Type': 'int'},
                # Add all columns
            ],
            'Location': 's3://your-bucket/your-prefix/',
            # Parquet-specific formats
            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
                'Parameters': {}
            },
            'Compressed': True,  # If your Parquet data is compressed
            'StoredAsSubDirectories': False
        },
        'TableType': 'EXTERNAL_TABLE',
        'Parameters': {
            'classification': 'parquet',
            'typeOfData': 'file',
            'compressionType': 'none',  # or 'snappy', 'gzip', etc. if compressed
            'EXTERNAL': 'TRUE'
        }
    }
)
```

## Accessing Parquet Data from Python

### Option 1: Using AWS Data Wrangler (Recommended)

```python
import awswrangler as wr
import pandas as pd

# Read directly from S3 using the Glue Catalog
df = wr.athena.read_sql_table(
    table="my_parquet_table",
    database="my_etl_database"
)

# Alternatively, query with SQL
df = wr.athena.read_sql_query(
    sql="SELECT * FROM my_etl_database.my_parquet_table LIMIT 1000",
    database="my_etl_database"
)

print(df.head())
```

### Option 2: Using PyArrow (for direct Parquet access)

```python
import pyarrow.parquet as pq
import s3fs

# Create S3 filesystem
fs = s3fs.S3FileSystem()

# Read Parquet file directly from S3
dataset = pq.ParquetDataset('s3://your-bucket/your-prefix/*.parquet', filesystem=fs)
table = dataset.read()
df = table.to_pandas()

print(df.head())
```

### Option 3: Using boto3 and PyArrow

```python
import boto3
import pandas as pd
import pyarrow.parquet as pq
from io import BytesIO

# Get metadata from Glue to find exact S3 location
glue_client = boto3.client('glue')
table_info = glue_client.get_table(
    DatabaseName='my_etl_database',
    Name='my_parquet_table'
)

# Get the S3 location
s3_location = table_info['Table']['StorageDescriptor']['Location']
s3_path = s3_location.replace('s3://', '')
bucket_name = s3_path.split('/', 1)[0]
prefix = s3_path.split('/', 1)[1] if '/' in s3_path else ''

# List files in the location
s3_client = boto3.client('s3')
response = s3_client.list_objects_v2(
    Bucket=bucket_name,
    Prefix=prefix
)

# Get a sample file (first file)
if 'Contents' in response and len(response['Contents']) > 0:
    sample_file = response['Contents'][0]['Key']
    obj = s3_client.get_object(Bucket=bucket_name, Key=sample_file)
    parquet_data = obj['Body'].read()

    # Read into pandas using PyArrow
    table = pq.read_table(BytesIO(parquet_data))
    df = table.to_pandas()
    print(df.head())
```

## Accessing Parquet Data from PySpark

```python
from pyspark.sql import SparkSession

# Create a SparkSession with Glue catalog integration
spark = SparkSession.builder
    .appName("GlueParquetAccess")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
    .config("spark.sql.catalogImplementation", "hive")
    .config("hive.metastore.client.factory.class",
            "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory")
    .enableHiveSupport()
    .getOrCreate()

# Read the Parquet data from Glue Catalog
df = spark.sql("SELECT * FROM my_etl_database.my_parquet_table")
# or
df = spark.table("my_etl_database.my_parquet_table")

# Show data
df.show()

# Apply any transformations
df_filtered = df.filter(df.column2 > 100)

# Write back to S3 if needed
df_filtered.write.mode("overwrite").parquet("s3://your-output-bucket/filtered-data/")
```

## Performance Tips for Parquet

1. Take advantage of Parquet's columnar structure by selecting only needed columns:
   ```python
   # In PySpark
   df = spark.sql("SELECT column1, column2 FROM my_etl_database.my_parquet_table")
   
   # In AWS Data Wrangler
   df = wr.athena.read_sql_query("SELECT column1, column2 FROM my_etl_database.my_parquet_table")
   ```

2. Use Parquet's predicate pushdown capabilities:
   ```python
   # The filter is pushed down to Parquet reading level
   df = spark.sql("SELECT * FROM my_etl_database.my_parquet_table WHERE column2 > 100")
   ```

3. If your data is partitioned in S3 (e.g., by date), make sure to define partitions in your Glue table to take
   advantage of partition pruning.

