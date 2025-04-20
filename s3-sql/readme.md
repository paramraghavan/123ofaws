# S3 SQL Manager

A Python/PySpark package for loading datasets from S3 and performing SQL queries on them.

## Features

- Load datasets from S3 bucket/prefix combinations
- Register datasets as named tables
- Perform SQL queries across multiple tables
- Join tables using standard SQL syntax
- Support for various file formats (Parquet, CSV, JSON, etc.)

## Installation

```bash
pip install s3-sql
```

## Requirements

- Python 3.6+
- PySpark 3.0+
- boto3

## Usage

### Basic Usage

```python
from s3_sql import S3DataManager

# Initialize the manager
manager = S3DataManager()

# Register datasets from S3
manager.register_dataset(
    bucket="my-data-bucket",
    prefix="customers/2023",
    table_name="customers",
    format="parquet"
)

manager.register_dataset(
    bucket="my-data-bucket",
    prefix="orders/2023",
    table_name="orders",
    format="csv",
    options={"header": "true", "inferSchema": "true"}
)

# Run a SQL query that joins the tables
result = manager.execute_sql("""
    SELECT c.customer_id, c.name, o.order_date, o.amount
    FROM customers c
    JOIN orders o ON c.customer_id = o.customer_id
    WHERE o.amount > 100
    ORDER BY o.amount DESC
""")

# Display the results
result.show()
```

### Available Methods

| Method | Description |
|--------|-------------|
| `register_dataset()` | Register a dataset from S3 as a table |
| `execute_sql()` | Run a SQL query on registered tables |
| `list_tables()` | List all registered tables |
| `get_table_schema()` | Get the schema of a registered table |
| `preview_table()` | Preview data from a registered table |
| `unregister_table()` | Unregister a previously registered table |

## Advanced Configuration

You can pass your own SparkSession to the S3DataManager:

```python
from pyspark.sql import SparkSession

# Create a custom SparkSession
spark = SparkSession.builder \
    .appName("MyApp") \
    .config("spark.executor.memory", "8g") \
    .getOrCreate()

# Initialize the manager with the custom SparkSession
manager = S3DataManager(spark=spark)
```

## AWS Credentials

The package uses boto3 for AWS authentication. Make sure your AWS credentials are properly configured using one of the following methods:

- Environment variables
- AWS credentials file
- IAM roles (for EC2 instances)
