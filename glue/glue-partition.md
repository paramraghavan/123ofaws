# Creating and Using Partitioned Tables in AWS Glue

Partitioning your data in AWS Glue can significantly improve query performance and reduce costs. Let me show you how to
create and use various partition schemes in AWS Glue.

## Types of Partitions in AWS Glue

1. **Static Partitions**: Fixed partition values defined during table creation
2. **Dynamic Partitions**: Partition values determined at runtime based on data
3. **Projection Partitions**: Virtual partitions that don't require registering each partition

## Creating a Partitioned Table in AWS Glue

### Method 1: Using AWS Console

1. Go to AWS Glue Console → Tables → "Add table manually"
2. Fill in the basic table information
3. In the "Partition keys" section, add your partition columns:
    - Date-based: `year (int)`, `month (int)`, `day (int)`
    - Category-based: `region (string)`, `product (string)`
4. Define the schema excluding partition columns
5. Set the S3 location to the parent folder containing all partitions

### Method 2: Using AWS Glue API (Python)

```python
import boto3

glue_client = boto3.client('glue')

# Create a partitioned table for Parquet data
response = glue_client.create_table(
    DatabaseName='my_etl_database',
    TableInput={
        'Name': 'my_partitioned_table',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'user_id', 'Type': 'string'},
                {'Name': 'product_id', 'Type': 'string'},
                {'Name': 'purchase_amount', 'Type': 'double'},
                # Other data columns (excluding partition columns)
            ],
            'Location': 's3://your-bucket/data/',  # Base path
            'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat',
            'Compressed': True,
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
            },
        },
        'PartitionKeys': [
            {'Name': 'year', 'Type': 'int'},
            {'Name': 'month', 'Type': 'int'},
            {'Name': 'day', 'Type': 'int'},
            {'Name': 'region', 'Type': 'string'}
        ],
        'TableType': 'EXTERNAL_TABLE',
        'Parameters': {
            'classification': 'parquet',
            'EXTERNAL': 'TRUE'
        }
    }
)
```

## Different Partition Schemas

### 1. Date-Based Partitioning

```python
# S3 structure: s3://bucket/data/year=2023/month=12/day=31/*.parquet

glue_client.create_table(
    DatabaseName='my_etl_database',
    TableInput={
        # ... other properties ...
        'PartitionKeys': [
            {'Name': 'year', 'Type': 'int'},
            {'Name': 'month', 'Type': 'int'},
            {'Name': 'day', 'Type': 'int'}
        ],
        # ... other properties ...
    }
)
```

### 2. Category-Based Partitioning

```python
# S3 structure: s3://bucket/data/region=us-east/category=electronics/*.parquet

glue_client.create_table(
    DatabaseName='my_etl_database',
    TableInput={
        # ... other properties ...
        'PartitionKeys': [
            {'Name': 'region', 'Type': 'string'},
            {'Name': 'category', 'Type': 'string'}
        ],
        # ... other properties ...
    }
)
```

### 3. Hybrid Partitioning

```python
# S3 structure: s3://bucket/data/year=2023/month=12/region=us-east/*.parquet

glue_client.create_table(
    DatabaseName='my_etl_database',
    TableInput={
        # ... other properties ...
        'PartitionKeys': [
            {'Name': 'year', 'Type': 'int'},
            {'Name': 'month', 'Type': 'int'},
            {'Name': 'region', 'Type': 'string'}
        ],
        # ... other properties ...
    }
)
```

## Registering Partitions

After creating a partitioned table, you need to register the partitions. Without using the crawler, you can:

### 1. Add Partitions Manually (One-time)

```python
glue_client.batch_create_partition(
    DatabaseName='my_etl_database',
    TableName='my_partitioned_table',
    PartitionInputList=[
        {
            'Values': ['2023', '12', '31', 'us-east'],  # Matches partition key order
            'StorageDescriptor': {
                # Same as table's StorageDescriptor except for:
                'Location': 's3://your-bucket/data/year=2023/month=12/day=31/region=us-east/'
            }
        },
        # Add more partitions
    ]
)
```

### 2. Use Partition Projection (Recommended for Large Numbers of Partitions)

This allows AWS Glue to calculate partition locations without registering them:

```python
glue_client.update_table(
    DatabaseName='my_etl_database',
    TableInput={
        'Name': 'my_partitioned_table',
        # Other table properties remain the same
        'Parameters': {
            'classification': 'parquet',
            'EXTERNAL': 'TRUE',
            'projection.enabled': 'true',
            'projection.year.type': 'integer',
            'projection.year.range': '2020,2025',
            'projection.month.type': 'integer',
            'projection.month.range': '1,12',
            'projection.day.type': 'integer',
            'projection.day.range': '1,31',
            'projection.region.type': 'enum',
            'projection.region.values': 'us-east,us-west,eu-west',
            'storage.location.template': 's3://your-bucket/data/year=${year}/month=${month}/day=${day}/region=${region}'
        }
    }
)
```

## Querying Partitioned Tables

### Using Athena

```sql
-- Filter by partitions for efficient queries
SELECT * FROM my_etl_database.my_partitioned_table 
WHERE year = 2023 AND month = 12 AND region = 'us-east'
LIMIT 10;
```

### Using PySpark

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder
    .appName("QueryPartitionedData")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config("hive.metastore.client.factory.class",
            "com.amazonaws.glue.catalog.metastore.AWSGlueDataCatalogHiveClientFactory")
    .enableHiveSupport()
    .getOrCreate()

# Query with partition filtering
df = spark.sql("""
    SELECT * FROM my_etl_database.my_partitioned_table 
    WHERE year = 2023 AND month = 12
""")

# Alternative approach
df = spark.table("my_etl_database.my_partitioned_table")
    .filter("year = 2023 AND month = 12")

df.show()
```

### Using Python and AWS Data Wrangler

```python
import awswrangler as wr

# Query with partition filtering
df = wr.athena.read_sql_query(
    sql="SELECT * FROM my_etl_database.my_partitioned_table WHERE year=2023 AND month=12 AND region='us-east'",
    database="my_etl_database"
)

print(df.head())
```

## Automating Partition Registration

If you can't use a crawler but need to automate partition registration:

```python
import boto3
import os


def register_new_partitions():
    s3_client = boto3.client('s3')
    glue_client = boto3.client('glue')

    bucket = 'your-bucket'
    prefix = 'data/'

    # List all folders in the bucket
    paginator = s3_client.get_paginator('list_objects_v2')

    # Track registered partitions
    registered_partitions = set()

    # Get currently registered partitions
    paginator = glue_client.get_paginator('get_partitions')
    for page in paginator.paginate(
            DatabaseName='my_etl_database',
            TableName='my_partitioned_table'):
        for partition in page['Partitions']:
            registered_partitions.add(tuple(partition['Values']))

    # Find partitions in S3
    partitions_to_add = []

    # Example for year=YYYY/month=MM/day=DD/region=XX pattern
    for result in s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/'):
        if 'CommonPrefixes' in result:
            for year_prefix in result['CommonPrefixes']:
                year_val = year_prefix['Prefix'].split('=')[1].strip('/')

                # Repeat nested for loops for each partition level
                # ...

                # For simplicity, assume we've parsed out all partition values
                partition_values = [year_val, month_val, day_val, region_val]

                if tuple(partition_values) not in registered_partitions:
                    partitions_to_add.append({
                        'Values': partition_values,
                        'StorageDescriptor': {
                            # Copy from table but update location
                            'Location': f's3://{bucket}/{prefix}year={year_val}/month={month_val}/day={day_val}/region={region_val}/'
                        }
                    })

    # Register new partitions in batches (max 100 per call)
    if partitions_to_add:
        for i in range(0, len(partitions_to_add), 100):
            batch = partitions_to_add[i:i + 100]
            glue_client.batch_create_partition(
                DatabaseName='my_etl_database',
                TableName='my_partitioned_table',
                PartitionInputList=batch
            )
```

