# Complete AWS Data Engineering Handbook
## For Beginners, Intermediate, and Advanced Users

**Version**: 1.2 (streamlined reference)
**Last Updated**: October 23, 2026
**Author**: Param Raghavan | Senior Data Engineer | 18+ Years Experience
**Target Audience**: Everyone from complete beginners to advanced practitioners

---

## How To Use This Reference

Use [the folder index](README.md) for reading order, [local labs](learn.md) for LocalStack API practice, and
[remote Jupyter](jupyter-lan-setup.md) for notebook/file commands. This reference focuses on AWS concepts and broader
data-platform examples; code blocks are independent teaching examples, not one runnable script.

Managed-service examples need existing resources, roles, and replacements for sample bucket names, ARNs, and release
labels. Use a separately configured AWS sandbox process; the local notebook's inherited `AWS_ENDPOINT_URL` and dummy
credentials instead point supported Boto3 clients at LocalStack. LocalStack does not provide managed Glue/EMR compute.

Spark `s3://` examples assume a configured managed runtime. Local Spark needs `s3a://`, matching Hadoop jars, and endpoint
settings from the linked Mac Spark guide. Create `spark` as in Chapter 7 before snippets that use it.

## Contents

- [Chapter 1: What is Cloud Computing & AWS?](#chapter-1-what-is-cloud-computing--aws)
- [Chapter 2: AWS Core Concepts](#chapter-2-aws-core-concepts)
- [Chapter 3: Python Basics for Data Engineers](#chapter-3-python-basics-for-data-engineers)
- [Chapter 4: Introduction to S3](#chapter-4-introduction-to-s3)
- [Chapter 5: Understanding IAM & Permissions](#chapter-5-understanding-iam--permissions)
- [Chapter 6: AWS Glue - The Data Catalog](#chapter-6-aws-glue---the-data-catalog)
- [Chapter 7: PySpark Basics](#chapter-7-pyspark-basics)
- [Chapter 8: ETL Pipelines](#chapter-8-etl-pipelines)
- [Chapter 9: AWS Lambda - Serverless Computing](#chapter-9-aws-lambda---serverless-computing)
- [Chapter 10: Orchestrating Workflows with Step Functions](#chapter-10-orchestrating-workflows-with-step-functions)
- [Chapter 11: EMR - Big Data Processing](#chapter-11-emr---big-data-processing)
- [Chapter 12: Advanced Spark Optimization](#chapter-12-advanced-spark-optimization)
- [Chapter 13: Data Governance & Lineage](#chapter-13-data-governance--lineage)
- [Chapter 14: Real-Time Data Streaming](#chapter-14-real-time-data-streaming)
- [Chapter 15: Multi-Account & Multi-Region Architecture](#chapter-15-multi-account--multi-region-architecture)
- [Chapter 16: AWS Systems Manager (SSM) - Configuration & Secrets](#chapter-16-aws-systems-manager-ssm---configuration--secrets)

## Chapter 1: What is Cloud Computing & AWS?

AWS provides storage, compute, databases, analytics, and security services. Data engineers combine them to ingest,
validate, transform, store, and serve data. Managed infrastructure reduces server administration but still requires
application design, permissions, monitoring, and cost management.

A typical data flow is `sources -> raw storage -> validation/transformation -> curated data -> consumers`.

## Chapter 2: AWS Core Concepts

| Concept | Meaning for a data engineer |
|---|---|
| Account | Resource, identity, and billing boundary |
| Region | Geographic service location; consider latency, availability, and residency |
| Availability Zone | Isolation boundary within a Region |
| IAM role/policy | Workload identity and permissions |
| S3 | Object storage for data lake files |
| Glue Catalog | Table and partition metadata |
| Glue / EMR | Managed data processing with different runtime/operational choices |
| Athena | SQL queries over compatible stored data |
| Step Functions | Workflow coordination; schedules need a scheduling service |

See [the service overview](README.md#services-to-know) for the introductory messaging services.

## Chapter 3: Python Basics for Data Engineers

### 3.1 Essential Python for Data Engineers

**Python is the language of data engineering.** You need to know these basics:

#### Variables and Data Types

```python
# Numbers
age = 25
salary = 50000.50

# Text (Strings)
name = "John"
city = "New York"

# Lists (Collections)
data_sources = ["database", "api", "csv_file"]
numbers = [1, 2, 3, 4, 5]

# Dictionaries (Key-Value pairs)
person = {
    "name": "John",
    "age": 25,
    "city": "New York"
}

# Accessing dictionary values
print(person["name"])  # Output: John
```

#### Functions

```python
# Define a function
def calculate_average(numbers):
    """This function calculates the average of numbers"""
    total = sum(numbers)
    count = len(numbers)
    return total / count

# Use the function
result = calculate_average([10, 20, 30])
print(result)  # Output: 20.0
```

#### Loops

```python
# Loop through a list
data_sources = ["S3", "RDS", "API"]
for source in data_sources:
    print(f"Processing {source}")

# Loop with counter
for i in range(5):  # 0, 1, 2, 3, 4
    print(f"Number: {i}")
```

#### Conditionals (If/Else)

```python
# Check conditions
age = 25

if age < 18:
    print("Too young")
elif age < 65:
    print("Working age")
else:
    print("Retirement age")
```

#### Error Handling

```python
# Handle errors gracefully
try:
    result = 10 / 0  # This will cause an error
except ZeroDivisionError:
    print("Cannot divide by zero!")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### 3.2 Working with Files

```python
import json
import csv

# Read a JSON file
with open('data.json', 'r') as file:
    data = json.load(file)
    print(data)

# Write JSON file
data = {"name": "John", "age": 25}
with open('output.json', 'w') as file:
    json.dump(data, file)

# Read CSV file
with open('data.csv', 'r') as file:
    reader = csv.DictReader(file)
    for row in reader:
        print(row)
```

### 3.3 Working with Dates & Time

```python
from datetime import datetime, timedelta

# Current time
now = datetime.now()
print(now)  # 2024-05-10 14:30:45.123456

# Format date
formatted = now.strftime("%Y-%m-%d")  # 2024-05-10

# Add days
tomorrow = now + timedelta(days=1)

# Parse date from string
date_str = "2024-05-10"
parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
```

### **Exercise 3.1: Data Processing Script**

**Problem:**
Write a Python script that:
1. Reads a JSON file with customer data
2. Filters customers over age 30
3. Prints their names

**Solution:**

```python
import json

# Sample data (save as customers.json)
sample_data = [
    {"name": "Alice", "age": 28},
    {"name": "Bob", "age": 35},
    {"name": "Charlie", "age": 42}
]

# Load data
with open('customers.json', 'r') as f:
    customers = json.load(f)

# Filter and print
for customer in customers:
    if customer['age'] > 30:
        print(f"{customer['name']} is {customer['age']} years old")

# Output:
# Bob is 35 years old
# Charlie is 42 years old
```

---

## Chapter 4: Introduction to S3

### 4.1 What is S3?

**S3 = Simple Storage Service**

Think of it like a giant, unlimited filing cabinet:
- Store any type of file (documents, images, data files)
- Access files from anywhere
- Pay only for storage used
- Can share files with others

### 4.2 S3 Basics

**Bucket = Container for files**

```
AWS Account
└── S3
    ├── Bucket 1: my-data-lake
    │   ├── customers.csv
    │   ├── orders.parquet
    │   └── logs/
    │       └── 2024/01/15/log.txt
    │
    └── Bucket 2: company-documents
        ├── report.pdf
        └── contracts/
            └── contract1.docx
```

**Key concepts:**
- **Bucket name**: Unique identifier (like `my-company-data-lake`)
- **Object**: A file stored in S3
- **Path/Key**: Location of file (`data/customers/2024/01/15/data.csv`)

### 4.3 Using S3 With Python

Use the [local S3 recipes](learn.md#s3-cloud-storage) for bucket/object operations. For managed AWS, create a Boto3 client
with your approved profile or workload role rather than a LocalStack endpoint. The exercise below adds a CSV upload.

### 4.4 S3 Best Practices

```
✅ DO:
- Organize files in folders: year/month/day/
- Use versioning for important files
- Encrypt sensitive data
- Use lifecycle policies to archive old data

❌ DON'T:
- Store millions of small files (combine them)
- Leave test data in production buckets
- Share your bucket with everyone
- Store passwords or secrets in S3
```

### **Exercise 4.1: Upload Data to S3**

**Problem:**
Upload a CSV file to S3 and verify it was uploaded.

**Solution:**

```python
import boto3
import pandas as pd

# Create sample data
data = {
    'customer_id': [1, 2, 3],
    'name': ['Alice', 'Bob', 'Charlie'],
    'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com']
}

df = pd.DataFrame(data)

# Save locally
df.to_csv('customers.csv', index=False)

# Upload to S3
s3 = boto3.client('s3')
s3.upload_file('customers.csv', 'my-data-lake', 'customers/2024/05/customers.csv')

print("✓ File uploaded successfully!")

# Verify by listing files
response = s3.list_objects_v2(Bucket='my-data-lake', Prefix='customers/')
if response.get('Contents'):
    for obj in response['Contents']:
        print(f"Found: {obj['Key']}")
```

---

## Chapter 5: Understanding IAM & Permissions

### 5.1 What is IAM?

**IAM = Identity and Access Management**

It's like security in a company:
- **Employees**: Users with specific permissions
- **Departments**: Groups of users with similar access
- **Job titles**: Roles defining what you can do
- **Rules**: Policies controlling what you can access

### 5.2 IAM Concepts

```
AWS Account
│
├── Users (Individual people)
│   ├── Alice (Data Engineer)
│   └── Bob (Data Scientist)
│
├── Groups (Teams)
│   ├── DataTeam
│   │   ├── Alice
│   │   └── Bob
│   └── AnalyticsTeam
│
└── Roles (Job descriptions)
    ├── ReadS3Only
    │   └── Can read S3 files
    ├── ReadWriteS3
    │   └── Can read and write S3 files
    └── AdminAccess
        └── Can do everything
```

### 5.3 Permissions (Policies)

**A policy is a list of what you can do:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-data-lake/*",
        "arn:aws:s3:::my-data-lake"
      ]
    }
  ]
}
```

**Translation:**
- Effect: Allow this action
- Action: I can read files (GetObject) and list bucket contents (ListBucket)
- Resource: Only on the "my-data-lake" bucket

### 5.4 Principle of Least Privilege

**Important Security Rule:**

```
DON'T:   Give users all permissions (admin)
DO:      Give users ONLY what they need

Example:
❌ BAD:  "You're a data engineer, you're an admin"
✅ GOOD: "You're a data engineer, you can:
         - Read data from S3
         - Read from RDS database
         - Write to S3 (output folder only)
         - Run Glue jobs (your team's jobs only)"
```

### **Exercise 5.1: Create an IAM Identity with Limited Permissions**

**Problem:**
Create an IAM identity policy that can only read from a specific S3 bucket. In production, prefer attaching this
permission to a role or group instead of creating long-lived IAM user access keys.

**Solution:**

```python
import boto3
import json

iam = boto3.client('iam')

# Step 1: Create IAM user for the exercise
user_name = 'data-analyst-user'
iam.create_user(UserName=user_name)
print(f"✓ User {user_name} created")

# Step 2: Create a policy (permission document)
policy_doc = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::my-data-lake/*",
                "arn:aws:s3:::my-data-lake"
            ]
        }
    ]
}

# Step 4: Attach policy to user
iam.put_user_policy(
    UserName=user_name,
    PolicyName='ReadOnlyS3Policy',
    PolicyDocument=json.dumps(policy_doc)
)

print(f"✓ Permission policy attached to {user_name}")
```

---

# PART 2: DATA PLATFORMS AND PROCESSING

## Chapter 6: AWS Glue - The Data Catalog

### 6.1 What is Glue?

**Glue = Data Organization Tool**

Imagine your data is like a library:
- **Glue = Librarian** that catalogs all books
- **Data Catalog = Library card system** (shows what data you have)
- **Glue Jobs = Helpers** that process data

### 6.2 How Glue Works

```
Raw Data (in S3)
    ↓
Glue Crawler (Discovers structure)
    ↓
Glue Catalog (Records metadata)
    ↓
You can query with Athena/Spark
```

### 6.3 Using Glue with Python

These table definitions illustrate metadata registration over existing S3 data. The shown LazySimpleSerDe is for simple
delimited records, not general quoted CSV. Match the SerDe, delimiter, header handling, and column types to the actual
files. Register partitions separately when applicable; creating a table does not validate or rewrite the source data.

```python
import boto3

glue = boto3.client('glue')

# Create a database (like creating a folder)
glue.create_database(
    DatabaseInput={
        'Name': 'my_database',
        'Description': 'Database for customer data'
    }
)

# Create a table (like organizing a spreadsheet)
glue.create_table(
    DatabaseName='my_database',
    TableInput={
        'Name': 'customers',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'customer_id', 'Type': 'bigint'},
                {'Name': 'name', 'Type': 'string'},
                {'Name': 'email', 'Type': 'string'},
                {'Name': 'age', 'Type': 'int'}
            ],
            'Location': 's3://my-data-lake/customers/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe'
            }
        }
    }
)

print("✓ Database and table created!")
```

### **Exercise 6.1: Create a Glue Catalog for CSV Data**

**Problem:**
Create a Glue database and table for customer CSV files in S3.

**Solution:**

```python
import boto3
import json

glue = boto3.client('glue')

# Step 1: Create database
database_name = 'retail_data'
glue.create_database(
    DatabaseInput={
        'Name': database_name,
        'Description': 'Retail company data'
    }
)
print(f"✓ Database '{database_name}' created")

# Step 2: Create table schema
glue.create_table(
    DatabaseName=database_name,
    TableInput={
        'Name': 'customers',
        'StorageDescriptor': {
            'Columns': [
                {'Name': 'customer_id', 'Type': 'int'},
                {'Name': 'first_name', 'Type': 'string'},
                {'Name': 'last_name', 'Type': 'string'},
                {'Name': 'email', 'Type': 'string'},
                {'Name': 'signup_date', 'Type': 'date'}
            ],
            'Location': 's3://retail-data-lake/customers/',
            'InputFormat': 'org.apache.hadoop.mapred.TextInputFormat',
            'OutputFormat': 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat',
            'SerdeInfo': {
                'SerializationLibrary': 'org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe',
                'Parameters': {'field.delim': ','}
            }
        }
    }
)
print(f"✓ Table 'customers' created in '{database_name}'")

# Step 3: Query to verify
tables = glue.get_tables(DatabaseName=database_name)
print(f"✓ Database has {len(tables['TableList'])} table(s)")
```

---

## Chapter 7: PySpark Basics

### 7.1 What is Spark?

**Spark = Fast Data Processing Engine**

Think of it like:
- **SQL**: A query language; modern database engines also use parallel and vectorized processing.
- **Spark**: A distributed engine that executes SQL and DataFrame operations across partitions.

### 7.2 Spark Architecture

```
┌─────────────────────────────────────────┐
│           Spark Application             │
├─────────────────────────────────────────┤
│  Driver (Coordinator)                   │
│  - Plans the work                       │
│  - Sends tasks to workers               │
├─────────────────────────────────────────┤
│  Executors (Workers) - Running in parallel
│  ├─ Executor 1: Processing data        │
│  ├─ Executor 2: Processing data        │
│  └─ Executor 3: Processing data        │
└─────────────────────────────────────────┘
```

### 7.3 Creating a Spark Session

```python
from pyspark.sql import SparkSession

# Create Spark session
spark = SparkSession.builder \
    .appName("MyDataEngineering") \
    .getOrCreate()

print(f"Spark version: {spark.version}")
print(f"App name: {spark.sparkContext.appName}")
```

### 7.4 Working with DataFrames

**DataFrame = Table in Spark (like Excel spreadsheet)**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("DataDemo").getOrCreate()

# Create a sample DataFrame
data = [
    ("Alice", 25, "engineer"),
    ("Bob", 30, "analyst"),
    ("Charlie", 28, "engineer")
]

columns = ["name", "age", "role"]

df = spark.createDataFrame(data, columns)

# Display data
df.show()
# Output:
# +-------+---+----------+
# |   name|age|      role|
# +-------+---+----------+
# |  Alice| 25|  engineer|
# |    Bob| 30|   analyst|
# |Charlie| 28|  engineer|
# +-------+---+----------+

# Get information
df.printSchema()
# Output:
# root
#  |-- name: string (nullable = true)
#  |-- age: long (nullable = true)
#  |-- role: string (nullable = true)

# Count rows
print(f"Total rows: {df.count()}")  # 3
```

### 7.5 Basic Operations

```python
# Filter: Keep only engineers
engineers = df.filter(df.role == "engineer")
engineers.show()

# Select: Choose specific columns
names_ages = df.select("name", "age")
names_ages.show()

# OrderBy: Sort data
sorted_df = df.orderBy("age", ascending=False)
sorted_df.show()

# GroupBy: Aggregate data
by_role = df.groupBy("role").count()
by_role.show()
# Output:
# +----------+-----+
# |      role|count|
# +----------+-----+
# |   analyst|    1|
# |  engineer|    2|
# +----------+-----+
```

### **Exercise 7.1: Create and Process a DataFrame**

**Problem:**
Create a sales DataFrame and find total sales by product.

**Solution:**

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("SalesAnalysis").getOrCreate()

# Create sample sales data
sales_data = [
    ("Laptop", 1200, "2024-01-01"),
    ("Mouse", 25, "2024-01-02"),
    ("Laptop", 1200, "2024-01-03"),
    ("Keyboard", 75, "2024-01-04"),
    ("Mouse", 25, "2024-01-05")
]

columns = ["product", "price", "date"]

df = spark.createDataFrame(sales_data, columns)

print("=== All Sales ===")
df.show()

print("\n=== Total Sales by Product ===")
sales_by_product = df.groupBy("product") \
    .agg({"price": "sum"}) \
    .withColumnRenamed("sum(price)", "total_sales") \
    .orderBy("total_sales", ascending=False)

sales_by_product.show()
# Output:
# +--------+------------+
# | product| total_sales|
# +--------+------------+
# |  Laptop|        2400|
# |   Mouse|          50|
# |Keyboard|          75|
# +--------+------------+

print("\n=== Number of Sales per Product ===")
sales_count = df.groupBy("product").count()
sales_count.show()
```

---

## Chapter 8: ETL Pipelines

### 8.1 What is ETL?

**ETL = Extract, Transform, Load**

```
[SOURCE DATA]
    ↓
EXTRACT: Read from source (database, API, CSV)
    ↓
TRANSFORM: Clean, modify, combine data
    ↓
LOAD: Write to destination (warehouse, data lake)
    ↓
[DESTINATION - Ready for analysis]
```

### 8.2 Customer ETL

The exercise below demonstrates filtering, name cleanup, deduplication, and Parquet output. The
[end-to-end Spark exercise](#exercise-1-build-end-to-end-pipeline) extends this with aggregation and notification.

### 8.3 Error Handling in Pipelines

```python
def run_etl_pipeline(input_path, output_path):
    """
    ETL pipeline with error handling
    """
    try:
        spark = SparkSession.builder.appName("ETLPipeline").getOrCreate()

        # Extract
        print(f"Extracting from {input_path}...")
        df = spark.read.csv(input_path, header=True)

        # Transform
        print("Transforming data...")
        df_clean = df.filter(df.id.isNotNull())

        # Load
        print(f"Loading to {output_path}...")
        df_clean.write.mode("overwrite").parquet(output_path)

        print("✓ Pipeline completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Error in pipeline: {str(e)}")
        return False
```

### **Exercise 8.1: Build a Customer ETL Pipeline**

**Problem:**
Create an ETL pipeline that:
1. Reads customer data from CSV
2. Removes records with missing email
3. Converts names to uppercase
4. Saves as Parquet

**Solution:**

```python
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, upper, trim

spark = SparkSession.builder.appName("CustomerETL").getOrCreate()

# === EXTRACT ===
print("Step 1: Extracting data...")
raw_df = spark.read \
    .option("header", "true") \
    .csv("customers_raw.csv")

print(f"Raw data: {raw_df.count()} rows")

# === TRANSFORM ===
print("\nStep 2: Transforming data...")

clean_df = raw_df \
    .filter(col("email").isNotNull()) \
    .filter(col("email") != "") \
    .withColumn("first_name", upper(trim(col("first_name")))) \
    .withColumn("last_name", upper(trim(col("last_name")))) \
    .dropDuplicates(["email"]) \
    .select("customer_id", "first_name", "last_name", "email", "age")

print(f"Clean data: {clean_df.count()} rows")
clean_df.show(5)

# === LOAD ===
print("\nStep 3: Loading data...")
clean_df.write \
    .mode("overwrite") \
    .parquet("customers_processed.parquet")

print("✓ Pipeline completed!")
```

---

## Chapter 9: AWS Lambda - Serverless Computing

Lambda runs event-driven code without administering the underlying servers. Choose it when work fits the runtime,
memory, and duration limits; use distributed processing for workloads that need it. For deployment/invocation mechanics,
use the [local Lambda exercise](learn.md#lambda-serverless-functions). The S3 handler below illustrates file processing.

### **Exercise 9.1: Create a Lambda Function that Processes S3 Files**

**Problem:**
Create a Lambda function that:
1. Triggers when CSV file is uploaded to S3
2. Counts the number of rows
3. Logs the result

**Solution:**

```python
# lambda_function.py
import json
import boto3
import csv
from io import StringIO

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
    Triggered by S3 upload event
    Counts CSV rows and logs result
    """

    try:
        # Extract bucket and file info from event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']

        print(f"Processing: s3://{bucket}/{key}")

        # Get file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')

        # Count rows
        reader = csv.reader(StringIO(content))
        row_count = sum(1 for _ in reader) - 1  # -1 for header

        # Log result
        result = {
            'bucket': bucket,
            'file': key,
            'row_count': row_count,
            'status': 'success'
        }

        print(json.dumps(result))

        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }

    except Exception as e:
        error_result = {
            'status': 'error',
            'error': str(e)
        }
        print(json.dumps(error_result))

        return {
            'statusCode': 500,
            'body': json.dumps(error_result)
        }

# To deploy:
# 1. Zip this file: zip lambda.zip lambda_function.py
# 2. Create IAM role with S3 permissions
# 3. Create Lambda function with a currently supported Python runtime
# 4. Upload zip file
# 5. Set S3 trigger on upload event
```

---

## Chapter 10: Orchestrating Workflows with Step Functions

### 10.1 What is Step Functions?

**Step Functions = Workflow Orchestrator**

It's like a manager coordinating multiple workers:

```
Step 1: Extract data (Lambda)
    ↓
Step 2: Process data (EMR/Glue)
    ↓
Step 3: Load data (S3/Database)
    ↓
Step 4: Notify completion (SNS)
```

### 10.2 Simple Workflow Example

Use a Standard workflow for Glue `.sync` integration. Create the referenced Lambda, Glue job, SNS topic, and execution
role first. See AWS's [Glue integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-glue.html) and
[SNS integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-sns.html).

```json
{
  "Comment": "Data processing workflow",
  "StartAt": "ExtractData",
  "States": {
    "ExtractData": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:us-east-1:123456789012:function:extract",
      "Next": "ProcessData"
    },
    "ProcessData": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {
        "JobName": "data-processing-job"
      },
      "Next": "NotifySuccess"
    },
    "NotifySuccess": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {"TopicArn": "arn:aws:sns:us-east-1:123456789012:data-alerts", "Message": "Pipeline complete"},
      "End": true
    }
  }
}
```

### 10.3 Error Handling in Workflows

```json
{
  "StartAt": "ProcessData",
  "States": {
    "ProcessData": {
      "Type": "Task",
      "Resource": "arn:aws:states:::glue:startJobRun.sync",
      "Parameters": {"JobName": "data-processing-job"},
      "Retry": [
        {
          "ErrorEquals": ["States.ALL"],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2.0
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "HandleError"
        }
      ],
      "Next": "Success"
    },
    "HandleError": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sns:publish",
      "Parameters": {"TopicArn": "arn:aws:sns:us-east-1:123456789012:data-alerts", "Message": "Pipeline failed"},
      "End": true
    },
    "Success": {
      "Type": "Pass",
      "End": true
    }
  }
}
```

### Practice: Workflow Failure Handling

Adapt the preceding workflow to retry transient job failures, publish a failure alert, and record the execution result.
Create the referenced jobs/topics/role before running; a Pass state's value is not itself an external log event.

## Chapter 11: EMR - Big Data Processing

### 11.1 What is EMR?

**EMR = Elastic MapReduce**

It's a cluster of computers working together:

```
┌────────────────────────────────────────┐
│         EMR Cluster                    │
├────────────────────────────────────────┤
│  Primary Node (Cluster Services)             │
│  - Hosts cluster management services   │
│  - Spark driver plans application work │
├────────────────────────────────────────┤
│  Worker Nodes (Running in parallel)   │
│  ├─ Worker 1: Processing data         │
│  ├─ Worker 2: Processing data         │
│  └─ Worker 3: Processing data         │
└────────────────────────────────────────┘
```

### 11.2 When to Use EMR

Choose by operational needs, supported runtime/libraries, integrations, startup latency, and measured cost/performance.
Both Glue and EMR can process large data; there is no 100 GB dividing line. Glue provides managed ETL jobs and catalog
integration. EMR offers EC2, EKS, and Serverless deployment choices with different levels of runtime control.


### 11.3 Creating an EMR Cluster

This EC2 example requires an existing subnet, service role, EC2 instance profile, and a supported release label set in
your environment. The release label identifies the EMR distribution, not just Spark. The Spark driver location depends
on client versus cluster deploy mode; it is not always the primary node.
See [RunJobFlow](https://docs.aws.amazon.com/emr/latest/APIReference/API_RunJobFlow.html).

```python
import os
import boto3

emr = boto3.client('emr')

# Create cluster
response = emr.run_job_flow(
    Name='MyDataProcessingCluster',
    ReleaseLabel=os.environ['EMR_RELEASE_LABEL'],
    ServiceRole=os.environ['EMR_SERVICE_ROLE'],
    JobFlowRole=os.environ['EMR_EC2_INSTANCE_PROFILE'],
    Instances={
        'MasterInstanceType': 'm5.xlarge',
        'SlaveInstanceType': 'm5.xlarge',
        'InstanceCount': 3,  # 1 primary + 2 core nodes
        'Ec2SubnetId': os.environ['EMR_SUBNET_ID'],
        'KeepJobFlowAliveWhenNoSteps': True
    },
    Applications=[
        {'Name': 'Spark'},
        {'Name': 'Hadoop'},
        {'Name': 'Hive'}
    ]
)

cluster_id = response['JobFlowId']
print(f"✓ Cluster requested: {cluster_id}")
# Wait for the cluster to be ready before submitting work.
emr.get_waiter('cluster_running').wait(ClusterId=cluster_id)
# After the submitted work completes, terminate an EC2 lab cluster explicitly:
# emr.terminate_job_flows(JobFlowIds=[cluster_id])
```

### 11.4 Submitting Spark Jobs to EMR

```python
# Create Spark script
spark_script = """
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("DataProcessing").getOrCreate()

# Read data
df = spark.read.parquet("s3://my-bucket/input/data.parquet")

# Process
result = df.filter(df.age > 25).groupBy("department").count()

# Write result
result.write.parquet("s3://my-bucket/output/result.parquet")

print("✓ Job completed successfully!")
"""

# Save script
with open('process_data.py', 'w') as f:
    f.write(spark_script)

# Upload to S3
s3 = boto3.client('s3')
s3.upload_file('process_data.py', 'my-bucket', 'scripts/process_data.py')

# Submit job to EMR
emr = boto3.client('emr')
emr.add_job_flow_steps(
    JobFlowId='j-xxxxx',
    Steps=[
        {
            'Name': 'ProcessData',
            'ActionOnFailure': 'CONTINUE',
            'HadoopJarStep': {
                'Jar': 'command-runner.jar',
                'Args': ['spark-submit', '--master', 'yarn', '--deploy-mode', 'cluster',
                         's3://my-bucket/scripts/process_data.py']
            }
        }
    ]
)

print("✓ Job submitted to EMR!")
```

### **Exercise 11.1: Process Large Dataset with EMR**

**Problem:**
Write a Spark job that processes 1GB dataset:
1. Read data from S3
2. Filter records
3. Aggregate by category
4. Write results

**Solution:**

```python
# emr_job.py
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg

def main():
    """Process sales data"""

    spark = SparkSession.builder \
        .appName("SalesAnalysis") \
        .getOrCreate()

    print("Starting sales analysis...")

    # === EXTRACT ===
    df = spark.read \
        .option("header", "true") \
        .csv("s3://data-lake/sales/raw/*.csv")

    print(f"Raw records: {df.count()}")

    # === TRANSFORM ===
    # Filter valid records
    clean_df = df.filter(
        (col("amount") > 0) & \
        (col("date").isNotNull())
    )

    # Aggregate by product
    summary = clean_df.groupBy("product") \
        .agg(
            count("*").alias("total_sales"),
            avg("amount").alias("avg_amount")
        ) \
        .orderBy("total_sales", ascending=False)

    print(f"Clean records: {clean_df.count()}")
    summary.show()

    # === LOAD ===
    summary.write \
        .mode("overwrite") \
        .parquet("s3://data-lake/sales/summary/")

    print("✓ Analysis complete!")

if __name__ == "__main__":
    main()
```

---

## Chapter 12: Advanced Spark Optimization

### 12.1 Common Performance Issues

```
Problem: Job is slow
Diagnosis:
1. Check Spark UI (web interface)
2. Look for data skew (uneven distribution)
3. Check for inefficient joins
4. Look for too many small files
```

### 12.2 Optimization Techniques

#### Partitioning

```python
# ❌ SLOW: Read entire dataset
df = spark.read.parquet("s3://data-lake/sales/")

# ✅ FAST: Read only data you need (partition pruning)
df = spark.read.parquet("s3://data-lake/sales/year=2024/month=05/")
df = df.filter(col("day") > 10)
```

#### Caching

```python
# If you use data multiple times, cache it
df = spark.read.parquet("data.parquet")

# Cache in memory (fast access)
df.cache()

# Use it multiple times
result1 = df.filter(df.age > 25).count()
result2 = df.filter(df.salary > 50000).count()

# Remove from cache
df.unpersist()
```

#### Bucketing For Joins

In Spark's V1 bucketing API, write catalog tables with `saveAsTable`; `bucketBy(...).parquet(path)` is unsupported.
Both tables must have compatible bucket metadata, and Spark must choose a plan that uses it. Inspect `explain()` rather
than assuming every join avoids a shuffle. These table names must be disposable lab names.

```python
orders = spark.read.parquet("s3://my-bucket/orders/")
customers = spark.read.parquet("s3://my-bucket/customers/")
orders.write.format("parquet").bucketBy(16, "customer_id").mode("overwrite").saveAsTable("lab_orders_bucketed")
customers.write.format("parquet").bucketBy(16, "customer_id").mode("overwrite").saveAsTable("lab_customers_bucketed")
result = spark.table("lab_orders_bucketed").join(spark.table("lab_customers_bucketed"), "customer_id")
result.explain()
```

See the [Spark bucketBy API](https://spark.apache.org/docs/latest/api/python/reference/pyspark.sql/api/pyspark.sql.DataFrameWriter.bucketBy.html).

#### AQE, Skew, And Output Layout

AQE is enabled by default in upstream Spark 3.2 and later; verify runtime overrides. It can adjust eligible joins using
shuffle statistics. Random repartitioning balances downstream work but cannot by itself split a hot business key in a
later keyed shuffle. Use broadcast, AQE skew handling, or a correct salting/partial-aggregation strategy as appropriate.
Choose output partition counts from measured data/file sizes instead of a fixed magic number. A cache is lazy and is
useful for reused results; it is not a guarantee that every partition fits in memory.

### **Exercise 12.1: Optimize a Slow Query**

**Problem:**
This query is slow. Optimize it.

```python
# ❌ SLOW version
df1 = spark.read.parquet("s3://bucket/large_dataset/")
df2 = spark.read.parquet("s3://bucket/lookup/")

result = df1.join(df2, "id")  # Slow join
result = result.filter(col("amount") > 1000)

result.write.parquet("output/")
```

**Solution:**

```python
# ✅ OPTIMIZED version
from pyspark.sql.functions import col, broadcast

# Read only needed columns
df1 = spark.read.parquet("s3://bucket/large_dataset/") \
    .select("id", "amount", "date")

# If df2 is small, broadcast it
df2 = spark.read.parquet("s3://bucket/lookup/") \
    .select("id", "category")

# Filter first (reduce data before join)
df1_filtered = df1.filter(col("amount") > 1000)

# Join with broadcast
result = df1_filtered.join(broadcast(df2), "id")

# Write using the resulting partitioning; add repartition only after measuring output file sizes.
result.write.parquet("output/")

print("✓ Optimized!")
```

---

## Chapter 13: Data Governance & Lineage

### 13.1 What is Data Governance?

**Data Governance = Rules for data management**

```
Who can access what data?
├─ Data engineer: All data
├─ Analyst: Sales and marketing data only
├─ HR: Employee data only
└─ Customer: Their own data only
```

### 13.2 Data Lineage

**Data Lineage = Tracking where data comes from**

```
Database → ETL Pipeline → Data Warehouse
  ↓            ↓                  ↓
Customer     [Transform]      Dashboard
Data         [Clean Data]      Analyst
             [Aggregate]       Uses

Lineage shows: Database → Pipeline → Dashboard
```

### 13.3 Implementing Data Lineage

```python
import json
from datetime import datetime

class DataLineageTracker:
    """Track data transformations"""

    def __init__(self):
        self.lineage_log = []

    def log_transformation(self, source, operation, destination):
        """Log a data transformation"""

        event = {
            'timestamp': datetime.now().isoformat(),
            'source': source,
            'operation': operation,
            'destination': destination
        }

        self.lineage_log.append(event)
        print(f"✓ Logged: {source} → {destination}")

    def save_lineage(self, filename):
        """Save lineage to file"""

        with open(filename, 'w') as f:
            json.dump(self.lineage_log, f, indent=2)

    def get_lineage_for_table(self, table_name):
        """Get all transformations for a table"""

        return [log for log in self.lineage_log
                if log['destination'] == table_name]

# Usage
tracker = DataLineageTracker()

tracker.log_transformation(
    source="s3://raw/customers.csv",
    operation="Filter valid emails + Deduplicate",
    destination="s3://processed/customers/"
)

tracker.log_transformation(
    source="s3://processed/customers/",
    operation="Join with orders + Aggregate",
    destination="s3://analytics/customer_summary/"
)

tracker.save_lineage("lineage.json")
```

---

## Chapter 14: Real-Time Data Streaming

### 14.1 What is Real-Time Data?

**Real-Time = Data arrives continuously (not in batches)**

```
Batch Processing:          Real-Time Processing:
Data arrives → Process     Data arrives ↓
Check → Process → Output   Process immediately
             Process       Output in seconds
             Output

Example:                   Example:
Daily sales report        Live stock prices
Monthly analytics         Click-stream analysis
```

### 14.2 AWS Kinesis

**Kinesis = Real-time data streaming service**

```python
import boto3
import json
import time

kinesis = boto3.client('kinesis')

# Send data to stream
def send_event(event_data):
    response = kinesis.put_record(
        StreamName='my-stream',
        Data=json.dumps(event_data),
        PartitionKey=event_data['user_id']  # Groups related data
    )
    print(f"Sent record: {response['ShardId']}")

# Example: Send user click events
for i in range(10):
    event = {
        'user_id': f'user_{i}',
        'action': 'click',
        'timestamp': time.time()
    }
    send_event(event)
    time.sleep(1)
```

### 14.3 Consuming Stream Data

This teaching consumer reads only the first shard and has no durable checkpoint. `LATEST` starts after iterator
creation, so run the consumer before sending records if you want to observe them. Production consumers must handle
all shards, resharding, retries, checkpoints, and duplicates (for example with KCL or a managed integration).

```python
import boto3
import json
import time

kinesis = boto3.client('kinesis')

def read_stream():
    """Read data from Kinesis stream"""

    # Get shard iterator
    response = kinesis.describe_stream(StreamName='my-stream')
    shard_id = response['StreamDescription']['Shards'][0]['ShardId']

    iterator_response = kinesis.get_shard_iterator(
        StreamName='my-stream',
        ShardId=shard_id,
        ShardIteratorType='LATEST'
    )

    shard_iterator = iterator_response['ShardIterator']

    # Read records
    while shard_iterator:
        response = kinesis.get_records(
            ShardIterator=shard_iterator,
            Limit=10
        )

        for record in response['Records']:
            data = json.loads(record['Data'])
            print(f"Received: {data}")

        shard_iterator = response['NextShardIterator']
        time.sleep(1)
```

---

## Chapter 15: Multi-Account & Multi-Region Architecture

### 15.1 Multi-Account Structure

```
Organization Root
│
├─ Dev Account (Development)
│  ├─ Developers write code
│  └─ Test data only
│
├─ Staging Account (Testing)
│  ├─ Pre-production testing
│  └─ Production-like environment
│
└─ Prod Account (Production)
   ├─ Real customer data
   └─ High security
```

### 15.2 Cross-Account Access

```python
import boto3
import json

sts = boto3.client('sts')

def assume_prod_role():
    """Access data in production account from dev"""

    # Assume role in prod account
    assumed_role = sts.assume_role(
        RoleArn='arn:aws:iam::222222222222:role/prod-data-access',
        RoleSessionName='dev-session',
        ExternalId='<external-id-from-trust-policy>'  # Required only when the trust policy specifies it
    )

    credentials = assumed_role['Credentials']

    # Create S3 client with prod account credentials
    s3 = boto3.client(
        's3',
        aws_access_key_id=credentials['AccessKeyId'],
        aws_secret_access_key=credentials['SecretAccessKey'],
        aws_session_token=credentials['SessionToken']
    )

    # Now can access prod S3
    response = s3.list_objects_v2(Bucket='prod-data-lake')
    return response

print(assume_prod_role())
```

---

# PART 3: ADVANCED (Mastery)

This part covers reusable job configuration and secure runtime access to configuration values.

---

## Configuration-Driven EMR ETL


```python
# config.json
{
  "pipelines": [
    {
      "name": "customer_pipeline",
      "source": {
        "type": "s3",
        "path": "s3://raw/customers/2024/05/"
      },
      "transformations": [
        {
          "type": "filter",
          "condition": "age > 18"
        },
        {
          "type": "rename",
          "mappings": {"id": "customer_id"}
        }
      ],
      "destination": {
        "type": "s3",
        "path": "s3://processed/customers/"
      }
    }
  ]
}
```

---

## Chapter 16: AWS Systems Manager (SSM) - Configuration & Secrets

### 16.1 What is AWS Systems Manager?

**SSM = Central place to manage AWS infrastructure, configuration, and secrets**

Think of it like:
- **Key-Value Store**: Store configuration (database URLs, API keys)
- **Secrets Manager is a separate AWS service** for secrets and rotation; SSM Parameter Store also supports encrypted `SecureString` values.
- **Automation**: Run commands across multiple servers
- **Session Manager**: Secure access to EC2 instances (no SSH keys!)

### 16.2 SSM Parameter Store - Store Configuration

**Use Case**: Store database credentials, API keys, configuration values

```python
import boto3
import json

ssm = boto3.client('ssm')

# ============================================================================
# STORING CONFIGURATION IN PARAMETER STORE
# ============================================================================

# Store database connection string
ssm.put_parameter(
    Name='/myapp/database/connection_string',
    # Name: Path-like structure for organization
    Value='postgresql://<user>:<password>@db.example.com:5432/mydb',
    Type='SecureString',  # Encrypted with KMS
    # Type options:
    # - String: Plain text (not recommended for secrets)
    # - StringList: Comma-separated values
    # - SecureString: Encrypted (recommended for secrets)
    Description='Database connection string',
    Tags=[
        {'Key': 'Environment', 'Value': 'production'},
        {'Key': 'Application', 'Value': 'data-pipeline'}
    ]
)

print("✓ Parameter stored securely")

# Store S3 bucket names
ssm.put_parameter(
    Name='/myapp/s3/input_bucket',
    Value='my-data-lake-raw',
    Type='String',
    Description='Input data S3 bucket'
)

# Store configuration as JSON
config = {
    'batch_size': 1000,
    'timeout_seconds': 3600,
    'retry_count': 3,
    'max_workers': 10
}

ssm.put_parameter(
    Name='/myapp/config/processing',
    Value=json.dumps(config),
    Type='String',
    Description='Data processing configuration'
)

print("✓ Configuration parameters stored")

# ============================================================================
# RETRIEVING CONFIGURATION IN LAMBDA/GLUE
# ============================================================================

def get_database_connection():
    """Get database credentials from SSM"""
    try:
        response = ssm.get_parameter(
            Name='/myapp/database/connection_string',
            WithDecryption=True  # Decrypt if SecureString
        )
        connection_string = response['Parameter']['Value']
        return connection_string
    except ssm.exceptions.ParameterNotFound:
        print("Parameter not found!")
        return None

def get_config():
    """Get configuration from SSM"""
    response = ssm.get_parameter(Name='/myapp/config/processing')
    config_json = response['Parameter']['Value']
    config = json.loads(config_json)
    return config

# Use in Lambda handler
def lambda_handler(event, context):
    """Lambda function using SSM configuration"""

    # Fetch config from SSM; add an explicit bounded cache if repeated reads justify it.
    config = get_config()
    batch_size = config['batch_size']
    timeout = config['timeout_seconds']

    # Get database connection
    db_conn = get_database_connection()

    # Process data using configuration
    print(f"Processing with batch size: {batch_size}")

    return {
        'statusCode': 200,
        'body': 'Processing complete'
    }

# ============================================================================
# GET MULTIPLE PARAMETERS AT ONCE
# ============================================================================

def get_all_database_params():
    """Retrieve all parameters under /myapp/database/ path"""
    params = {}
    paginator = ssm.get_paginator('get_parameters_by_path')
    for page in paginator.paginate(Path='/myapp/database/', Recursive=True, WithDecryption=True):
        for param in page['Parameters']:
            # Preserve the full path so names from different subpaths do not collide.
            params[param['Name']] = param['Value']

    return params

print("Retrieved parameter names:", list(get_all_database_params()))  # Never print decrypted values.
```

### 16.3 Best Practice: Store Secrets in Glue Job

```python
# glue_job.py
# ============================================================================
# USING SSM PARAMETERS IN AWS GLUE JOB
# ============================================================================

import sys
import boto3
from awsglue.context import GlueContext
from pyspark.context import SparkContext
from awsglue.job import Job

# Initialize Glue
glueContext = GlueContext(SparkContext.getOrCreate())
job = Job(glueContext)
job.init('my-glue-job', {})

# Initialize SSM client
ssm = boto3.client('ssm')

# Get secrets from SSM Parameter Store
def get_secrets():
    """Retrieve all secrets needed for this job"""
    ssm_client = boto3.client('ssm')

    response = ssm_client.get_parameters(
        Names=[
            '/myapp/database/host',
            '/myapp/database/port',
            '/myapp/database/username',
            '/myapp/database/password',
            '/myapp/s3/output_bucket'
        ],
        WithDecryption=True
    )

    secrets = {}
    for param in response['Parameters']:
        key = param['Name'].split('/')[-1]
        secrets[key] = param['Value']

    return secrets

# Get secrets
secrets = get_secrets()

# Use secrets in Glue job
def run_etl():
    """ETL job using SSM-stored secrets"""

    # Read from RDS using SSM parameters
    rds_host = secrets['host']
    rds_port = secrets['port']
    rds_user = secrets['username']
    rds_password = secrets['password']

    connection_url = f"jdbc:postgresql://{rds_host}:{rds_port}/mydb"

    # Read from RDS
    df = glueContext.create_dynamic_frame.from_options(
        format_options={
            "url": connection_url,
            "user": rds_user,
            "password": rds_password,
            "customJdbcDriverS3Path": "s3://my-jars/postgresql.jar",
            "customJdbcDriverClassName": "org.postgresql.Driver"
        },
        connection_type="postgresql",
        format="jdbc"
    )

    # Write to S3
    output_bucket = secrets['output_bucket']
    df.write_dynamic_frame.from_options(
        frame=df,
        connection_type="s3",
        format="parquet",
        connection_options={"path": f"s3://{output_bucket}/output/"}
    )

    print("✓ ETL completed using SSM secrets")

if __name__ == "__main__":
    run_etl()
    job.commit()
```

### 16.4 EMR + SSM - Secure Cluster Configuration

Use the release, subnet, and role environment settings described in Chapter 11. This function launches a billable EC2
cluster; wait for readiness, submit work, and terminate the lab cluster after completion. Its memory settings are
illustrative and must fit the selected instance sizes.

```python
import os
import boto3
import json

ssm = boto3.client('ssm')
emr = boto3.client('emr')

# Store cluster configuration in SSM
cluster_config = {
    'spark_driver_memory': '4g',
    'spark_executor_memory': '8g',
    'spark_executor_cores': '4',
    'spark_dynamicAllocation_minExecutors': '2',
    'spark_dynamicAllocation_maxExecutors': '20'
}

ssm.put_parameter(
    Name='/myapp/emr/spark_config',
    Value=json.dumps(cluster_config),
    Type='String'
)

# Retrieve in EMR bootstrap script
def create_emr_cluster():
    """Create EMR cluster using SSM configuration"""

    # Get config from SSM
    response = ssm.get_parameter(Name='/myapp/emr/spark_config')
    spark_config = json.loads(response['Parameter']['Value'])

    # Create cluster with dynamic configuration
    cluster_response = emr.run_job_flow(
        Name='MyDataProcessingCluster',
        ReleaseLabel=os.environ['EMR_RELEASE_LABEL'],
        Applications=[{'Name': 'Spark'}],
        Instances={
            'MasterInstanceType': 'r6g.xlarge',
            'SlaveInstanceType': 'r6g.2xlarge',
            'InstanceCount': 3,
            'Ec2SubnetId': os.environ['EMR_SUBNET_ID'],
            'KeepJobFlowAliveWhenNoSteps': True
        },
        Configurations=[
            {
                'Classification': 'spark-defaults',
                'Properties': {
                    'spark.driver.memory': spark_config['spark_driver_memory'],
                    'spark.executor.memory': spark_config['spark_executor_memory'],
                    'spark.executor.cores': spark_config['spark_executor_cores']
                }
            }
        ],
        ServiceRole=os.environ['EMR_SERVICE_ROLE'],
        JobFlowRole=os.environ['EMR_EC2_INSTANCE_PROFILE']
    )

    return cluster_response['JobFlowId']
```

### 16.5 SSM + Lambda - Parameterized Functions

```python
import boto3
import os
from functools import lru_cache

ssm = boto3.client('ssm')

# Cache SSM parameters in memory (avoid repeated API calls)
@lru_cache(maxsize=100)
def get_ssm_parameter(name):
    """Get parameter from SSM with caching"""
    response = ssm.get_parameter(Name=name, WithDecryption=True)
    return response['Parameter']['Value']

def lambda_handler(event, context):
    """
    Lambda function parameterized with SSM

    Benefits:
    1. Change configuration without redeploying Lambda
    2. Keep secrets out of code
    3. Reuse same Lambda across environments
    """

    # Get parameters from SSM
    s3_bucket = get_ssm_parameter('/myapp/s3/output_bucket')
    batch_size = int(get_ssm_parameter('/myapp/config/batch_size'))
    api_key = get_ssm_parameter('/myapp/api/key')

    # Use parameters
    print(f"Processing with bucket: {s3_bucket}")
    print(f"Batch size: {batch_size}")

    # Call external API using key from SSM
    import requests
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get('https://api.example.com/data', headers=headers)

    return {
        'statusCode': 200,
        'body': f'Processed {batch_size} records'
    }
```

### 16.6 Configuration Guidelines

- Use parameter paths to separate environments and scope IAM access to the required paths.
- Use `SecureString` for sensitive parameters and authorize KMS decryption where needed. Never log decrypted values.
- Use Secrets Manager when a suitable secrets/rotation workflow is required; it is separate from SSM Parameter Store.
- Cache repeated reads only with a refresh strategy. An unbounded-lifetime cache can hide configuration changes.
- Keep larger configuration/data files in S3. Paginate parameter listings.

For interview-style Q&A, use the [AWS/Python interview handbook](../notes/aws_python_boto3_interview_handbook.md).

## End-To-End Spark Exercise

### Exercise 1: Build End-to-End Pipeline

**Problem:**
Build complete ETL pipeline:
1. Read customer CSV from S3
2. Clean data (remove nulls, duplicates)
3. Aggregate by region
4. Save as Parquet
5. Trigger notification

**Complete Solution:**

```python
# Step 1: Setup
import boto3
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, avg
import json

spark = SparkSession.builder.appName("CustomerPipeline").getOrCreate()
s3 = boto3.client('s3')
sns = boto3.client('sns')

def run_pipeline():
    """Complete ETL pipeline"""

    try:
        # === EXTRACT ===
        print("Step 1: Extracting...")
        df = spark.read \
            .option("header", "true") \
            .csv("s3://my-bucket/raw/customers.csv")

        print(f"Raw records: {df.count()}")

        # === TRANSFORM ===
        print("Step 2: Transforming...")

        clean_df = df \
            .filter(col("email").isNotNull()) \
            .filter(col("region").isNotNull()) \
            .dropDuplicates(["email"]) \
            .filter(col("age").cast("int") > 0)

        print(f"Clean records: {clean_df.count()}")

        # === AGGREGATE ===
        print("Step 3: Aggregating...")

        summary = clean_df.groupBy("region") \
            .agg(
                count("*").alias("customer_count"),
                avg("age").alias("avg_age")
            ) \
            .orderBy("customer_count", ascending=False)

        summary.show()

        # === LOAD ===
        print("Step 4: Loading...")

        summary.write \
            .mode("overwrite") \
            .parquet("s3://my-bucket/processed/customer_summary/")

        # === NOTIFY ===
        print("Step 5: Notifying...")

        message = f"✓ Pipeline complete! Processed {clean_df.count()} records"
        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:alerts',
            Subject='Pipeline Completed',
            Message=message
        )

        return True

    except Exception as e:
        error_msg = f"✗ Pipeline failed: {str(e)}"
        print(error_msg)

        sns.publish(
            TopicArn='arn:aws:sns:us-east-1:123456789012:alerts',
            Subject='Pipeline Failed',
            Message=error_msg
        )

        return False

if __name__ == "__main__":
    success = run_pipeline()
    exit(0 if success else 1)
```

---

# APPENDIX

## A: AWS Free Tier And Lab Costs

Eligibility depends on your account creation date, plan, service, and usage. The program changed for new customers on
July 15, 2025; do not rely on a fixed list of "12 months free" quotas. Check your account's current benefits and budgets
before launching EMR/Glue or other paid resources. Credits and budget alerts are not a general guarantee against charges.
See the [AWS Free Tier guide](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier.html).

## B: Setting Up Your AWS Account

**Step 1: Create AWS Account**
- Go to aws.amazon.com
- Click "Create an AWS Account"
- Review the selected account plan, payment requirements, and billing limits.

**Step 2: Configure identity**
- Enable MFA on the root user and avoid root for daily work.
- Prefer AWS IAM Identity Center/SSO for human access.
- Prefer IAM roles for workloads.
- Create IAM user access keys only when your organization explicitly requires them.

**Step 3: Configure AWS CLI**
```bash
aws configure sso --profile sandbox
aws sso login --profile sandbox
```

**Step 4: Test Connection**
```bash
aws sts get-caller-identity --profile sandbox
aws s3 ls --profile sandbox
```

## C: Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `NoCredentialsError` | No usable AWS credentials | Check the selected profile/role and refresh SSO if needed |
| `AccessDenied` | Missing permissions | Update IAM policy |
| `OutOfMemory` | Too much data | Increase memory/partitions |
| `FileNotFound` | Wrong S3 path | Check bucket/key names |

## D: Resources for Further Learning

```
Official AWS:
- AWS Training & Certification
- AWS Workshops
- AWS YouTube Channel

Community:
- Stack Overflow
- Reddit: r/aws
- Medium: AWS blogs

Practice:
- AWS workshops (free hands-on)
- YouTube tutorials
- Your own projects
```

## E: Project Ideas for Practice

**Beginner:**
1. Upload CSV to S3
2. Catalog data with Glue
3. Query with Athena

**Intermediate:**
1. Build ETL pipeline (CSV → S3 → Parquet)
2. Create Lambda trigger
3. Schedule a Step Functions execution with EventBridge Scheduler

**Advanced:**
1. Build multi-region data lake
2. Implement real-time streaming
3. Create data governance framework

---
