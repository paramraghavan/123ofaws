```text
Here are my s3 buckets:
s3://bucket-name/dataset_name1/year=2024/month=12/day=1/data.parquet 
or 
s3://bucket-name/dataset_name2/year=2024/month=12/day=1/data.csv

Go step by step to sql query using python/pyspark  above s3 s3://bucket-name/dataset_name1 and s3://bucket-name/dataset_name2 using iceberg and Glue catalog
- What do need do to create Glue catalog
- how to enable iceberg to sql query dataset_name1 and dataset_name2  
- separate one time steps, from the steps that i need to over and over again

```

# Step-by-Step Guide for Using Iceberg with S3 and Glue Catalog

## One-Time Setup Steps

### 1. Set Up AWS Glue Data Catalog

```python
import boto3

# Initialize Glue client
glue_client = boto3.client('glue')

# Create a database in Glue Data Catalog
glue_client.create_database(
    DatabaseInput={
        'Name': 'my_iceberg_database',
        'Description': 'Database for Iceberg tables'
    }
)
```

### 2. Install Required Dependencies

```bash
# Install required packages
pip install pyspark==3.3.0 or higher
pip install boto3
pip install pyiceberg
```

### 3. Configure PySpark with Iceberg Support

```python
from pyspark.sql import SparkSession

# Initialize Spark with Iceberg and Glue Catalog support
spark = SparkSession.builder
    .appName("Iceberg with S3")
    .config("spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.3.0,org.apache.hadoop:hadoop-aws:3.3.1")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
    .config("spark.sql.catalog.glue_catalog.warehouse", "s3://bucket-name/iceberg-warehouse")
    .config("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
    .getOrCreate()
```

## 4. Register Existing S3 Data as Iceberg Tables

Here's how to convert your existing Parquet and CSV data to Iceberg format:

### For dataset_name1 (Parquet files)

```python
# Define table properties
table_properties = {
    'format-version': '2',
    'write.parquet.compression-codec': 'snappy'
}

# Create Iceberg table from existing Parquet data
spark.sql(f"""
CREATE TABLE glue_catalog.my_iceberg_database.dataset_name1
USING iceberg
PARTITIONED BY (year, month, day)
TBLPROPERTIES ({','.join([f"'{k}'='{v}'" for k, v in table_properties.items()])})
AS SELECT * FROM parquet.`s3://bucket-name/dataset_name1/`
""")
```

### For dataset_name2 (CSV files)

```python
# First, read and register the CSV data as a temporary view
spark.read.format("csv")
    .option("header", "true")
    .option("inferSchema", "true")
    .load("s3://bucket-name/dataset_name2/")
    .createOrReplaceTempView("dataset_name2_raw")

# Create Iceberg table from the temporary view
spark.sql("""
CREATE TABLE glue_catalog.my_iceberg_database.dataset_name2
USING iceberg
PARTITIONED BY (year, month, day)
AS SELECT * FROM dataset_name2_raw
""")
```

## Recurring Steps (Day-to-Day Operations)

### 1. Initialize Spark Session

Each time you want to work with the Iceberg tables, start with:

```python
from pyspark.sql import SparkSession

# Initialize Spark with Iceberg support
spark = SparkSession.builder
    .appName("Iceberg Query")
    .config("spark.jars.packages",
            "org.apache.iceberg:iceberg-spark-runtime-3.3_2.12:1.3.0,org.apache.hadoop:hadoop-aws:3.3.1")
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
    .config("spark.sql.catalog.glue_catalog", "org.apache.iceberg.spark.SparkCatalog")
    .config("spark.sql.catalog.glue_catalog.catalog-impl", "org.apache.iceberg.aws.glue.GlueCatalog")
    .config("spark.sql.catalog.glue_catalog.warehouse", "s3://bucket-name/iceberg-warehouse")
    .config("spark.sql.catalog.glue_catalog.io-impl", "org.apache.iceberg.aws.s3.S3FileIO")
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain")
    .getOrCreate()
```

### 2. Query the Iceberg Tables with SQL

```python
# Query dataset_name1
result1 = spark.sql("""
SELECT * 
FROM glue_catalog.my_iceberg_database.dataset_name1
WHERE year = 2024 AND month = 12 AND day = 1
LIMIT 10
""")
result1.show()

# Query dataset_name2
result2 = spark.sql("""
SELECT * 
FROM glue_catalog.my_iceberg_database.dataset_name2
WHERE year = 2024 AND month = 12
LIMIT 10
""")
result2.show()

# Join the datasets
joined_result = spark.sql("""
SELECT a.*, b.additional_column
FROM glue_catalog.my_iceberg_database.dataset_name1 a
JOIN glue_catalog.my_iceberg_database.dataset_name2 b
  ON a.some_id = b.some_id
WHERE a.year = 2024 AND a.month = 12
""")
joined_result.show()
```

### 3. Time Travel Queries (Optional)

```python
# Query data as of yesterday
yesterday_data = spark.sql("""
SELECT * 
FROM glue_catalog.my_iceberg_database.dataset_name1 
FOR TIMESTAMP AS OF (TIMESTAMP 'yesterday')
WHERE year = 2024 AND month = 12
""")
yesterday_data.show()
```

### 4. Update or Insert New Data

```python
# Insert new data
spark.sql("""
INSERT INTO glue_catalog.my_iceberg_database.dataset_name1
VALUES (1, 'value1', 'value2', 2024, 12, 2),
       (2, 'value3', 'value4', 2024, 12, 2)
""")

# Update existing data
spark.sql("""
UPDATE glue_catalog.my_iceberg_database.dataset_name1
SET column1 = 'new_value'
WHERE id = 1 AND year = 2024 AND month = 12 AND day = 1
""")
```

## Maintenance Operations (Occasional)

### Compaction (Optimize Small Files)

```python
spark.sql("""
CALL glue_catalog.system.rewrite_data_files(
  table => 'my_iceberg_database.dataset_name1',
  strategy => 'binpack',
  options => map('min-input-files','5')
)
""")
```

### Expire Snapshots (Clean Up Old Versions)

```python
spark.sql("""
CALL glue_catalog.system.expire_snapshots(
  table => 'my_iceberg_database.dataset_name1',
  older_than => TIMESTAMP '7 days ago',
  retain_last => 5
)
""")
```

## Summary

### One-Time Steps:

1. Create a Glue Data Catalog database
2. Install required dependencies
3. Configure PySpark with Iceberg support
4. Register existing S3 data as Iceberg tables

### Recurring Steps:

1. Initialize Spark session with Iceberg configurations
2. Query the tables using SQL
3. Perform data updates or inserts as needed

### Occasional Maintenance:

1. Compact files to optimize performance
2. Expire old snapshots to manage storage costs
