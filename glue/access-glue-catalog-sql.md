
# Accessing AWS Glue Catalog Table from PySpark

## Method 1: Using PySpark with AWS Glue Integration

```python
from pyspark.context import SparkContext
from pyspark.sql import SparkSession

# Create a SparkSession with AWS Glue catalog integration
spark = SparkSession.builder \
    .appName("GlueCatalogAccess") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
    .config("spark.sql.catalogImplementation", "hive") \
    .config("hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .enableHiveSupport() \
    .getOrCreate()

# Read the data from Glue Catalog
df = spark.sql("SELECT * FROM my_etl_database.my_table")

# Process the data
df.show()
```

## Method 2: Using PySpark with the Glue Data Catalog as the Hive metastore

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("GlueCatalogAccess") \
    .config("hive.metastore.glue.catalogid", "YOUR_AWS_ACCOUNT_ID") \
    .config("hive.metastore.client.factory.class", "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory") \
    .enableHiveSupport() \
    .getOrCreate()

# Read data
df = spark.table("my_etl_database.my_table")
df.show()
```

## Accessing AWS Glue Catalog Table from Python

### Method 1: Using AWS SDK (boto3)

```python
import boto3
import pandas as pd
from io import StringIO
import awswrangler as wr

# Method 1a: Using boto3 directly with Athena
athena_client = boto3.client('athena')
s3_client = boto3.client('s3')

# Execute query
query = "SELECT * FROM my_etl_database.my_table LIMIT 100"
query_execution = athena_client.start_query_execution(
    QueryString=query,
    QueryExecutionContext={
        'Database': 'my_etl_database'
    },
    ResultConfiguration={
        'OutputLocation': 's3://your-athena-results-bucket/path/'
    }
)

# Get query execution ID
query_execution_id = query_execution['QueryExecutionId']

# Wait for query to complete
import time
while True:
    query_status = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
    query_execution_status = query_status['QueryExecution']['Status']['State']
    
    if query_execution_status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
        break
    time.sleep(1)

# Get results
if query_execution_status == 'SUCCEEDED':
    result_location = query_status['QueryExecution']['ResultConfiguration']['OutputLocation']
    # Remove s3:// from the beginning
    path = result_location.replace('s3://', '')
    bucket = path.split('/', 1)[0]
    key = path.split('/', 1)[1]
    
    response = s3_client.get_object(Bucket=bucket, Key=key)
    data = response['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(data))
    print(df.head())
```

### Method 2: Using AWS Data Wrangler (recommended)

AWS Data Wrangler is a Python library that extends pandas to AWS services. It's much more convenient:

```python
# Install with: pip install awswrangler
import awswrangler as wr

# Read table directly into a Pandas DataFrame
df = wr.athena.read_sql_query(
    sql="SELECT * FROM my_etl_database.my_table LIMIT 1000",
    database="my_etl_database"
)

# Or read the entire table
df = wr.athena.read_sql_table(
    table="my_table",
    database="my_etl_database"
)

# Process with pandas
print(df.head())
```

### Method A3: Using PyAthena

```python
# Install with: pip install "PyAthena[pandas]"
from pyathena import connect
import pandas as pd

# Connect to Athena
conn = connect(
    s3_staging_dir='s3://your-athena-results-bucket/path/',
    region_name='your-region'
)

# Read data
df = pd.read_sql("SELECT * FROM my_etl_database.my_table LIMIT 100", conn)
print(df.head())
```

## Important Considerations

1. **IAM Permissions**: Ensure your execution environment has the necessary IAM permissions to access:
   - AWS Glue Catalog (glue:GetTable, glue:GetDatabase)
   - S3 data location (s3:GetObject, s3:ListBucket)
   - Athena if used (athena:StartQueryExecution, athena:GetQueryExecution, athena:GetQueryResults)

2. **Dependencies**: Install the necessary libraries:
   ```
   pip install boto3 pandas pyathena awswrangler
   ```

3. **Performance**: For large datasets, consider:
   - Using partitioning when querying
   - Implementing filters in your queries
   - Using appropriate file formats (Parquet is typically more performant than CSV)
