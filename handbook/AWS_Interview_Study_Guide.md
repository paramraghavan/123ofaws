# AWS Interview Study Guide - 

---

## Executive Summary

This guide is customized for your profile as a **Senior Data Engineer** with deep expertise in:
- AWS cloud architecture and large-scale data pipelines
- Python/PySpark for ETL and data processing
- Configuration-driven ETL solutions and real-time streaming
- Enterprise data governance and lineage tracking
- Infrastructure-as-Code (CloudFormation, Terraform)
---

## Table of Contents

1. [Interview Preparation Strategy](#interview-preparation-strategy)
2. [Core AWS Services Deep Dive](#core-aws-services-deep-dive)
3. [Data Engineering Patterns](#data-engineering-patterns)
4. [Architecture & Design Questions](#architecture--design-questions)
5. [Hands-On Practice](#hands-on-practice)
6. [Common Interview Questions](#common-interview-questions)
7. [Your Competitive Advantages](#your-competitive-advantages)

---

## Interview Preparation Strategy

### Phase 1: Assess & Prioritize (Week 1)
Your resume shows strong coverage of these areas:
- ✅ **Strength**: EMR, Lambda, Step Functions, S3 patterns
- ✅ **Strength**: Python/PySpark optimization and performance
- ✅ **Strength**: Data governance and lineage tracking
- ⚠️ **Gap**: Advanced networking (VPC, Direct Connect, PrivateLink)
- ⚠️ **Gap**: Disaster recovery and high-availability design patterns
- ⚠️ **Gap**: Security deep-dive (encryption, KMS, IAM policies)
- ⚠️ **Gap**: Cost optimization strategies

### Phase 2: Deep Dive by Domain (Weeks 2-3)

**Priority 1 (Your Expertise Zone)** - Spend 30% of time
- AWS Glue catalog design and optimization
- EMR cluster architecture, Spark tuning, YARN optimization
- Lambda function optimization and cold starts
- Step Functions state machine design patterns

**Priority 2 (Interview Essentials)** - Spend 40% of time
- Distributed systems concepts applied to AWS
- Scalability and performance patterns
- Disaster recovery and backup strategies
- Security and compliance (encryption, KMS, IAM)

**Priority 3 (General AWS)** - Spend 30% of time
- Networking fundamentals for data engineers
- RDS/Redshift optimization
- Cost optimization and billing
- Monitoring and observability

### Phase 3: Practice Scenarios (Weeks 4+)

Focus on questions that connect to your experience:
- "Design a real-time data pipeline similar to what you built at MessageBird"
- "How would you optimize this EMR cluster for cost?"
- "Walk us through your data governance approach at Freddie Mac"
- "Explain your configuration-driven ETL design philosophy"

---

## Core AWS Services Deep Dive

### 1. AWS Glue (Data Catalog & ETL)

**Interview Focus Areas:**
- Crawlers: incremental discovery, partition projection, custom classifiers
- Catalog: schema evolution, data quality rules, lineage tracking
- Glue Jobs: Spark script generation, DPU auto-scaling, job bookmarks
- Glue Studio: visual ETL design, data transformations

**Key Concepts to Master:**

```python
# ============================================================================
# GLUE CONTEXT AND SPARK SQL OPTIMIZATION - EXPLAINED
# ============================================================================
#
# IMPORTANT PREREQUISITES:
# ✓ S3 bucket 's3://my-bucket/temp' MUST EXIST before running this
# ✓ Glue database 'mydb' MUST EXIST with table 'mytable'
# ✓ This code runs in AWS Glue environment (not local Spark)
#
# WHAT THIS CODE DOES:
# 1. Creates a Glue job that reads from Glue Catalog (metadata)
# 2. Uses bookmarks to track which files were already processed (incremental)
# 3. Filters data at read time (push_down_predicate)
# 4. Handles schema changes (column renames, type changes)
# 5. Commits the job (updates bookmark for next run)
# ============================================================================

from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession
from pyspark.context import SparkContext

# Step 1: Initialize Spark Context
# WHAT: Creates the Spark engine (processes data in parallel)
# WHERE: Runs on EMR cluster created by Glue
# NOTE: SparkContext is created automatically by Glue, we just get it
spark_context = SparkContext.getOrCreate()

# Step 2: Create Glue Context
# WHAT: Wrapper around Spark that adds Glue-specific features
#       - Access to Glue Catalog (data metadata)
#       - Dynamic Frames (more flexible than DataFrames)
#       - Bookmark support (track processed files)
# WHY: Makes it easier to work with Glue Catalog data
glueContext = GlueContext(spark_context)

# Step 3: Initialize Job
# WHAT: Sets up job tracking and bookmarks
# job.init parameters:
#   - 'job_name': Name of this Glue job (for monitoring)
#   - TempDir: S3 location for temporary files
#
# TEMP DIRECTORY EXPLANATION:
# - S3 bucket 's3://my-bucket/temp' must exist
# - Glue uses this to store:
#   a) Bookmark state (which files were processed)
#   b) Temporary shuffle files (intermediate data)
#   c) Job metadata
# - You need S3 write permissions on this bucket
# - This is NOT an in-memory temp storage!
job = Job(glueContext)
job.init('customer_etl_job', {"TempDir": "s3://my-bucket/temp"})

# ============================================================================
# READING DATA FROM GLUE CATALOG WITH FILTERING
# ============================================================================

# Step 4: Create DynamicFrame from Glue Catalog
# WHAT: Reads table metadata from Glue Catalog, not directly from S3
#
# HOW IT WORKS:
# 1. Glue Catalog stores: database name, table name, column info, S3 location
# 2. glueContext queries the catalog for 'mydb.mytable'
# 3. Gets the S3 location (e.g., 's3://my-bucket/data/')
# 4. Applies filter BEFORE reading (optimization)
# 5. Creates DynamicFrame (flexible schema handling)
#
# DynamicFrame vs DataFrame:
# - DynamicFrame: Can handle schema changes, null values
#   (Better for dirty/inconsistent data)
# - DataFrame: Strict schema, faster
#   (Better for clean, consistent data)

dyf = glueContext.create_dynamic_frame.from_catalog(
    database="mydb",  # Database in Glue Catalog
    table_name="mytable",  # Table name in Glue Catalog
    transformation_ctx="read_data",  # For bookmarks (tracks what was read)
    push_down_predicate="year >= 2024"  # SQL filter applied BEFORE reading
    # IMPORTANT: This filter is pushed to S3!
    # Glue skips files where year < 2024
    # Example: skips 's3://my-bucket/data/year=2023/' entirely
)

# BOOKMARK EXPLANATION:
# - First run: Reads ALL files in 'mytable'
# - Second run: Only reads NEW files added since last run
# - Bookmark stored in: s3://my-bucket/temp/job_name/
# - Saves time and cost (don't reprocess old data)
# - Only works if 'transformation_ctx' is specified

# ============================================================================
# HANDLING SCHEMA EVOLUTION (COLUMN CHANGES)
# ============================================================================

# Step 5: Handle Schema Changes
# PROBLEM: What if schema changes between runs?
#   - Column added
#   - Column renamed (col2 → col2_new)
#   - Column type changed (long → bigint)
#
# SOLUTION: Use ApplyMapping to explicitly map columns

from awsglue.transforms import ApplyMapping

mapped_dyf = ApplyMapping.apply(
    frame=dyf,  # Input: the DynamicFrame we read
    mappings=[
        # Format: (old_name, old_type, new_name, new_type)
        ("col1", "string", "col1", "string"),  # No change
        ("col2", "long", "col2_new", "bigint"),  # Rename + type change
        # NOTE: col1 → col1 (no rename)
        #       long → bigint (type conversion)
        # If new columns appear, just don't map them (they're skipped)
    ],
    transformation_ctx="apply_mapping"  # For bookmarks
)

# ============================================================================
# COMMITTING THE JOB (SAVE BOOKMARK)
# ============================================================================

# Step 6: Commit Job
# WHAT: Writes bookmark to S3 (marks this run as complete)
#
# AFTER job.commit():
# 1. Glue records which files were processed
# 2. Next run only processes new/modified files
# 3. Saves time and money (incremental processing)
# 4. Bookmark stored in: s3://my-bucket/temp/

job.commit()

# ============================================================================
# COMPLETE FLOW SUMMARY
# ============================================================================
#
# Run 1 (Day 1):
#   Input: s3://my-bucket/data/year=2024/month=01/data.csv (1GB)
#   → Reads all data
#   → Writes bookmark to s3://my-bucket/temp/
#   Time: 5 minutes
#
# Run 2 (Day 2):
#   Input: New file added: s3://my-bucket/data/year=2024/month=02/data.csv (500MB)
#   → Reads ONLY the new file (NOT the old one)
#   → Updates bookmark
#   Time: 2.5 minutes (50% faster!)
# ============================================================================
```

**KEY INTERVIEW POINTS:**

```
Q: "What's the difference between DynamicFrame and DataFrame?"
A: "DynamicFrame can handle schema changes (columns added/removed).
   DataFrame is strict schema, faster. Choose DynamicFrame if dealing
   with messy data, DataFrame for clean data."

Q: "What does the 's3://my-bucket/temp' directory do?"
A: "Stores bookmark state (which files processed), shuffle files
   during join/group operations, and job metadata.
   Must have write permissions. Not in-memory temporary storage!"

Q: "How does push_down_predicate optimize?"
A: "Filter is applied BEFORE reading from S3.
   Glue skips entire partitions (e.g., year=2023/).
   Reduces data transfer and processing time significantly."

Q: "What happens if bookmark is corrupted?"
A: "Glue will re-read all files in next run.
   Job takes longer but completes successfully.
   Bookmark is stored in S3, not in Glue metadata."

Q: "Can you use DynamicFrame and DataFrame together?"
A: "Yes! Convert between them:
   df = dyf.toDF()  # DynamicFrame → DataFrame
   dyf = DynamicFrame.fromDF(df, glueContext, 'name')  # DataFrame → DynamicFrame"
```

**Interview Q&A:**
- Q: "How do you handle schema changes in Glue crawlers?"
  - A: "Use custom classifiers for specific patterns, enable schema evolution, and test with a sample dataset before full crawl. Use Glue Data Quality to validate transformations."

- Q: "Compare Glue Jobs vs. EMR Spark jobs"
  - A: "Glue: serverless, billed by DPU-hour, good for moderate workloads, easier monitoring. EMR: more control, cheaper for sustained compute, better for complex optimizations."

---

### 2. AWS EMR (Big Data Processing)

**Interview Focus Areas:**
- Cluster architecture: master, core, task nodes
- Spark optimization: memory tuning, partitioning, broadcast joins
- YARN resource management
- Cost optimization: Spot instances, instance fleets
- Scaling strategies: auto-scaling policies

**Key Concepts:**

```python
# ============================================================================
# SPARK OPTIMIZATION PATTERNS FOR EMR - EXPLAINED
# ============================================================================
#
# CONTEXT: This code runs on an EMR cluster (multiple computers)
# PROBLEM: Processing 1TB+ data efficiently
# SOLUTION: Use configurations to help Spark optimize automatically
#
# KEY DIFFERENCE FROM LOCAL SPARK:
# - Local: Single computer, limited memory (16GB)
# - EMR: Multiple computers (e.g., 10 nodes × 32GB = 320GB total)
# ============================================================================

from pyspark.sql import SparkSession

# Step 1: Create Spark Session with Optimization Configs
# WHY: Default Spark settings are conservative, we need to be aggressive

spark = SparkSession.builder \
    .appName("EMR-Optimization") \
    \
    # ADAPTIVE QUERY EXECUTION (Spark 3.x feature)
    # What: Spark adjusts query plan DURING execution based on real data
    # Why: Better than pre-planning without knowing data shape
    .config("spark.sql.adaptive.enabled", "true") \
    \
    # AUTO-COALESCING
    # Problem: Many small partitions = many tasks = overhead
    # Solution: Spark combines small partitions automatically
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    \
    # SKEW DETECTION & HANDLING
    # Problem: Some partitions huge, some small = some workers wait
    # Solution: Spark splits large partitions automatically
    .config("spark.sql.adaptive.skewJoin.enabled", "true") \
    \
    # DYNAMIC EXECUTOR ALLOCATION
    # Problem: Cluster has fixed number of executors (workers)
    # Solution: Add/remove workers based on demand
    .config("spark.dynamicAllocation.enabled", "true") \
    .config("spark.dynamicAllocation.minExecutors", "4") \  # Always keep 4
    .config("spark.dynamicAllocation.maxExecutors", "64") \  # Scale up to 64
    \
    .getOrCreate()

# ============================================================================
# READING DATA WITH PARTITION PRUNING
# ============================================================================

# Step 2: Read Partitioned Data
# CONTEXT: Data organized by date in S3
# S3 structure:
#   s3://bucket/path/year=2024/month=01/day=01/data.parquet
#   s3://bucket/path/year=2024/month=01/day=02/data.parquet
#   s3://bucket/path/year=2024/month=02/day=01/data.parquet
#   ... (hundreds of files)

df = spark.read \
    .parquet("s3://bucket/path/year=2024/month=01/*") \
    # What: Read ONLY January 2024 (not February, not 2023)
    # Why: Don't read what you don't need
    # Benefit: 30-50% faster, 30-50% cheaper (less data transfer)
    \
    .where("value > 100")  # Additional filter AFTER reading
    # Note: This filter happens AFTER reading to S3
    # Partition pruning (year=2024/month=01) happens BEFORE reading

# ============================================================================
# BUCKETING - OPTIMIZATION FOR FREQUENT JOINS
# ============================================================================

# Problem: Join customers with orders (1B rows each)
# Without bucketing: Need to shuffle ALL data (expensive)
# With bucketing: Data already organized by join key

# Step 3: Create Bucketed Table (Do once, use many times)
df.write \
    .bucketBy(100, "user_id") \  # Split into 100 buckets based on user_id
    # What: Rows with user_id=1 go to bucket 1
    #       Rows with user_id=2 go to bucket 2, etc.
    # Benefit: When joining with orders (also bucketed by user_id),
    #          Spark knows bucket 1 from customers joins with bucket 1 from orders
    #          No need to shuffle all data!
    .mode("overwrite") \
    .parquet("s3://bucket/bucketed_data")
    # Mode: overwrite (replace existing, or create if not exists)

# ============================================================================
# BROADCAST JOIN - OPTIMIZATION FOR SMALL + LARGE JOINS
# ============================================================================

# Problem: Joining small table (5GB) with large table (500GB)
# Without broadcast: Shuffle both (500GB + 5GB = shuffle 505GB)
# With broadcast: Copy 5GB to each executor, join in parallel

# Step 4: Broadcast Small Table
df_large = spark.read.parquet("s3://bucket/large_data")  # 500GB
df_small = spark.read.parquet("s3://bucket/small_data")   # 5GB

# Important: df_small must be < 2GB for broadcast to work efficiently
# Why: Each executor gets a copy, limited memory per executor

df_broadcast = spark.broadcast(df_small)  # Mark for broadcast
# What: Instead of sending small data everywhere,
#       Spark sends it to all executors ONCE
# Memory trade-off: 5GB × 10 executors = 50GB total (acceptable)

result = df_large.join(df_broadcast, "user_id")
# Execution: Each executor processes its portion of large data
#            Joins with complete small data (already local)
# Performance: 10x faster than shuffle join!

# When NOT to broadcast:
# ❌ Small table > 2GB (memory pressure)
# ❌ Joining two large tables (use bucketing instead)
# ✅ Use for dimension tables (products, customers, categories)

# ============================================================================
# MONITORING AND DEBUGGING
# ============================================================================

# Step 5: Enable Logging for Debugging
spark.sparkContext.setLogLevel("INFO")
# Levels: OFF, FATAL, ERROR, WARN (default), INFO, DEBUG, TRACE
# Why: INFO gives useful info without overwhelming output
# Where: Logs appear in EMR cluster logs (CloudWatch)

# ACCESS SPARK UI FOR DETAILED MONITORING:
# While job is running:
#   http://<EMR_MASTER_IP>:4040
#
# What you see:
#   - Stages: Read, Filter, Join, Write
#   - Task duration: Which stage is slow?
#   - Shuffle size: How much data moved?
#   - Memory usage: Am I close to running out?
#   - GC time: Garbage collection overhead

# ============================================================================
# COMMON PATTERNS SUMMARY
# ============================================================================

# Pattern 1: Filter while reading (partition pruning)
df = spark.read.parquet("s3://bucket/year=2024/month=*/day=15/*")
# Reads only day=15 data (faster)

# Pattern 2: Bucketing for repeated joins
# Write once with bucketing
df.write.bucketBy(100, "id").parquet("s3://bucketed/")
# Use many times without shuffle
df.join(other_df, "id")  # Fast!

# Pattern 3: Broadcast small tables
df_large.join(spark.broadcast(df_small), "id")
# 10x faster than regular join

# Pattern 4: Select only needed columns
df.select("col1", "col2", "col3")  # Not "df.select('*')"
# Reduces memory usage, faster processing

# Pattern 5: Filter early
df.filter(df.price > 100).groupBy("product").sum()
# Filters BEFORE grouping (less data to process)

# ============================================================================
```

**COST IMPLICATIONS:**

```
Unoptimized:
- Reads: 1TB from S3 = $0.02 × 1TB = $0.02
- Processing: 10 workers × 1 hour = $10
- Total: ~$10.02

Optimized:
- Reads: 50GB from S3 = $0.02 × 0.05TB = $0.001
- Processing: 10 workers × 10 min = $1.67
- Total: ~$1.67

Savings: 83% ($8.35 per run)!
```

**Interview Q&A:**
- Q: "How do you tune Spark for a 2TB+ dataset on EMR?"
  - A: "Partition by 200-500MB per partition. Use Adaptive Query Execution (Spark 3.x). Enable broadcast join for < 2GB tables. Monitor Spark UI for stage duration and shuffle size."

- Q: "Your EMR job is OOM. What's your approach?"
  - A: "1) Check shuffle sizes (reduce partitions). 2) Increase executor memory gradually. 3) Use bucketing to reduce memory during joins. 4) Profile with memory profiler. 5) Consider splitting into stages."

---

### 3. AWS Lambda & Step Functions

**Interview Focus Areas:**
- Lambda execution model: cold starts, warm starts, concurrent execution limits
- Lambda optimization: package size, memory allocation, code optimization
- Step Functions: state machine design, error handling, retry policies
- Integration patterns: S3 triggers, SQS, async execution

**Key Concepts:**

```python
# ============================================================================
# LAMBDA OPTIMIZATION STRATEGIES - EXPLAINED
# ============================================================================
#
# CONTEXT: Lambda function triggered when file uploaded to S3
# PROBLEM: Lambda has cold start (first invocation slower)
#          and limited execution time (15 min max)
# SOLUTION: Optimize code structure and use async processing
#
# LAMBDA PRICING:
# $0.0000002 per request + $0.0000166667 per GB-second
# Example: 100 requests/day × 512MB × 3sec = $0.0015/month (cheap!)
# ============================================================================

import json
import boto3
from functools import lru_cache

# ============================================================================
# COLD START OPTIMIZATION - MOVE IMPORTS OUTSIDE HANDLER
# ============================================================================

# WHAT IS COLD START?
# 1. Request comes to Lambda
# 2. AWS spins up new container
# 3. Python interpreter starts
# 4. All imports execute
# 5. Handler function runs
# Time: 500-2000ms (slow!)
#
# WARM START:
# 1. Container already running from previous request
# 2. Handler runs immediately
# Time: 1-10ms (fast!)
#
# OPTIMIZATION:
# - Import frequently-used libraries at top (reuse)
# - Lazy import rarely-used libraries (import inside function)

# Initialize clients OUTSIDE handler (reuse across invocations)
# WHY: Connections are expensive to create
#      If Lambda stays warm, boto3 client is reused (fast)
#      Cold start penalty: only happens once
s3_client = boto3.client('s3')  # Created once per Lambda container
dynamodb = boto3.resource('dynamodb')  # Reused for all invocations

# ============================================================================
# CACHING RESULTS TO REDUCE API CALLS
# ============================================================================

# @lru_cache decorator from functools
# WHAT: In-memory cache for function results
# WHY: Calling DynamoDB repeatedly is slow ($0.25 per million reads)
#      Caching same result avoids repeated API calls

@lru_cache(maxsize=128)  # Cache up to 128 different results
def get_table_schema(table_name):
    """
    Cache table schemas to reduce metadata calls

    Example:
    - First call: get_table_schema('users')
      → Calls DynamoDB (slow ~100ms)
      → Stores result in cache
    - Second call: get_table_schema('users')
      → Returns from cache (fast <1ms)
    - Different call: get_table_schema('orders')
      → Not in cache, calls DynamoDB
    """
    return dynamodb.Table(table_name).table_status

# ============================================================================
# LAMBDA HANDLER - THE MAIN FUNCTION
# ============================================================================

def lambda_handler(event, context):
    """
    AWS calls this function when Lambda is triggered

    Parameters:
    - event: Dictionary with trigger data
      Example (S3 trigger):
      {
        'Records': [
          {
            's3': {
              'bucket': {'name': 'my-bucket'},
              'object': {'key': 'uploads/file.csv'}
            }
          }
        ]
      }
    - context: Lambda context info
      - context.invoked_function_arn: Function ARN
      - context.aws_request_id: Unique request ID
      - context.get_remaining_time_in_millis(): Time left

    Return:
    Must return dictionary with:
    - statusCode: 200 (success), 4xx (client error), 5xx (server error)
    - body: Response message (must be string, not dict)
    """

    try:
        # ====================================================================
        # STEP 1: EXTRACT DATA FROM EVENT
        # ====================================================================

        # S3 trigger sends Records array
        bucket = event['Records'][0]['s3']['bucket']['name']
        # Example: 'my-data-lake'

        key = event['Records'][0]['s3']['object']['key']
        # Example: 'uploads/2024/05/data.csv'

        # ====================================================================
        # STEP 2: EARLY RETURN FOR DUPLICATES (FAIL FAST)
        # ====================================================================

        # Return fast for CloudWatch alarms
        if is_duplicate_record(key):
            # IMPORTANT: Return quickly (within 15 minutes)
            return {
                'statusCode': 200,  # 200 = success (even though we skipped)
                'body': json.dumps({'status': 'duplicate_skipped'})
            }

        # ====================================================================
        # STEP 3: ASYNC PROCESSING - DON'T PROCESS IN LAMBDA
        # ====================================================================

        # PROBLEM: This file might be 1GB, takes 1 hour to process
        #          Lambda max execution = 15 minutes (timeout!)
        # SOLUTION: Start Step Functions workflow (handles long jobs)
        #           Return immediately from Lambda

        step_functions = boto3.client('stepfunctions')

        # Start Step Functions execution (async workflow)
        execution = step_functions.start_execution(
            stateMachineArn=os.environ['STATE_MACHINE'],
            # STATE_MACHINE = 'arn:aws:states:us-east-1:123456789:stateMachine:...'
            # Stored in Lambda environment variable (set in AWS console)

            input=json.dumps({
                "bucket": bucket,
                "key": key
                # Pass file info to Step Functions (it will process)
            })
        )

        # ====================================================================
        # STEP 4: RETURN IMMEDIATELY
        # ====================================================================

        return {
            'statusCode': 202,  # 202 = accepted (async processing started)
            'body': json.dumps({
                'message': 'File processing started',
                'execution_arn': execution['executionArn']
            })
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        # ALWAYS return response (even on error)
        return {
            'statusCode': 500,  # 500 = server error
            'body': json.dumps({
                'error': str(e),
                'requestId': context.aws_request_id
            })
        }

# ============================================================================
# LAMBDA TIMING & ARCHITECTURE
# ============================================================================
#
# EXECUTION TIMELINE:
#
# File uploaded to S3
#   ↓ (S3 trigger fires)
# Lambda cold start (500ms)
#   ↓
# Lambda handler (100ms)
#   ├─ Extract bucket/key (10ms)
#   ├─ Check duplicate (20ms)
#   └─ Start Step Functions (70ms)
#   ↓ (return with 202)
# Step Functions takes over (async)
#   ├─ Trigger EMR cluster (5 min)
#   ├─ Process data (2 hours)
#   └─ Write results to S3
#   ↓ (Lambda already finished!)
#
# KEY POINT:
# Lambda returns in 600ms (fast)
# Processing happens asynchronously
# No timeout issues!
#
# ============================================================================
# ENVIRONMENT VARIABLES
# ============================================================================
#
# In AWS Lambda console, set:
# - STATE_MACHINE = arn:aws:states:region:account:stateMachine:name
# - S3_BUCKET = my-data-lake
# - DDB_TABLE = ProcessedFiles
#
# Access in code: os.environ['STATE_MACHINE']
#
# Why: Configuration separate from code
#      Easy to change without redeploying
#      Different values for dev/prod
#
# ============================================================================
```

**LAMBDA vs GLUE vs EMR DECISION TREE:**

```
File uploaded to S3
│
├─ < 5 minutes processing? → Use Lambda
│  └─ Start async workflow (Step Functions)
│
├─ 5-15 minutes processing? → Use Glue
│  └─ Serverless, billed by DPU-hour
│
└─ > 15 minutes OR > 1TB? → Use EMR
   └─ Cluster-based, more control
```

**COMMON LAMBDA MISTAKES:**

```
❌ MISTAKE 1: Processing large files in Lambda
   Problem: Timeout (15 min limit)
   Solution: Use Lambda to trigger async (Step Functions/EMR)

❌ MISTAKE 2: Creating boto3 clients inside handler
   Problem: Connection overhead, cold start penalty
   Solution: Create clients at module level (outside handler)

❌ MISTAKE 3: Not caching repeated queries
   Problem: Slow, expensive API calls
   Solution: Use @lru_cache for metadata lookups

❌ MISTAKE 4: Not returning quickly
   Problem: Lambda keeps running, costs money
   Solution: Return immediately, delegate to Step Functions

✅ BEST PRACTICE: Lambda as orchestrator, not processor
   - Lambda: <1 second (trigger workflows)
   - Step Functions: Coordinate long jobs
   - EMR/Glue: Do actual processing
```
        raise

# Step Functions State Machine (JSON)
STEP_FUNCTIONS_DEFINITION = {
    "Comment": "Data pipeline with error handling",
    "StartAt": "ValidateInput",
    "States": {
        "ValidateInput": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:validate",
            "Next": "ProcessData",
            "Catch": [
                {
                    "ErrorEquals": ["InvalidInput"],
                    "Next": "HandleValidationError"
                }
            ],
            "Retry": [
                {
                    "ErrorEquals": ["TooManyRequests"],
                    "IntervalSeconds": 2,
                    "MaxAttempts": 3,
                    "BackoffRate": 2.0
                }
            ]
        },
        "ProcessData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:process",
            "TimeoutSeconds": 3600,
            "Next": "NotifySuccess"
        },
        "NotifySuccess": {
            "Type": "Task",
            "Resource": "arn:aws:sns:...",
            "End": true
        },
        "HandleValidationError": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:...:function:error_handler",
            "End": true
        }
    }
}
```

**Interview Q&A:**
- Q: "How do you reduce Lambda cold start time?"
  - A: "1) Reduce package size (use Lambda layers). 2) Allocate higher memory (more CPU). 3) Warm up with scheduled CloudWatch events. 4) Use Lambda Provisioned Concurrency for critical paths. 5) Lazy load heavy libraries."

- Q: "Design a Step Functions state machine for multi-stage ETL with error handling"
  - A: "Use parallel stages for independent tasks. Add Catch blocks for specific errors. Implement exponential backoff for transient failures. Use Map states for dynamic job scheduling."

---

### 4. S3 (Object Storage & Data Lake)

**Interview Focus Areas:**
- S3 storage classes and lifecycle policies
- Partitioning strategies for analytics (year/month/day)
- S3 Select for query optimization
- Eventual consistency implications
- S3 vs. HDFS trade-offs

**Key Concepts:**

```python
# S3 optimization patterns
import boto3

s3 = boto3.client('s3')

def upload_with_optimization(bucket, key, data, partition_key='year=2024/month=01'):
    """
    Optimized S3 upload:
    - Use partition structure for analytics
    - Enable intelligent tiering
    - Use multipart upload for large files
    """

    s3.put_object(
        Bucket=bucket,
        Key=f"data/{partition_key}/file.parquet",
        Body=data,
        # Encryption
        ServerSideEncryption='AES256',
        # Metadata for tracking
        Metadata={'processed_at': '2024-01-15', 'version': '1.0'},
        # Tags for lifecycle
        Tagging='archive=false&retention=90days'
    )

def setup_lifecycle_policy(bucket_name):
    """
    Archive old data automatically
    """
    lifecycle_config = {
        'Rules': [
            {
                'ID': 'archive_old_data',
                'Filter': {'Prefix': 'data/'},
                'Status': 'Enabled',
                'NoncurrentVersionTransitions': [
                    {
                        'NoncurrentDays': 90,
                        'StorageClass': 'GLACIER'
                    }
                ],
                'Expiration': {
                    'Days': 730  # 2 years
                }
            }
        ]
    }

    s3.put_bucket_lifecycle_configuration(
        Bucket=bucket_name,
        LifecycleConfiguration=lifecycle_config
    )

def query_with_s3_select(bucket, key):
    """
    Use S3 Select to reduce data transfer
    """
    response = s3.select_object_content(
        Bucket=bucket,
        Key=key,
        ExpressionType='SQL',
        Expression="SELECT * FROM s3object s WHERE s.value > 100 LIMIT 10000",
        InputSerialization={'Parquet': {}},
        OutputSerialization={'JSON': {}}
    )

    result = b''
    for event in response['Payload']:
        if 'Records' in event:
            result += event['Records']['Payload']

    return result.decode('utf-8')
```

**Interview Q&A:**
- Q: "How do you design S3 partitioning for a data lake?"
  - A: "Use date-based partitioning (year/month/day) for time-series data. Add domain partitions (region/product) for access patterns. Keep partition size 200MB-1GB. Use Glue crawlers for automatic discovery."

- Q: "What's the eventual consistency problem in S3 and how do you handle it?"
  - A: "S3 has eventual consistency for PUT/DELETE. For real-time ACID guarantees, use DynamoDB to track processed files. For ML pipelines using old data, add delay. Use S3 versioning for recovery."

---

### 5. RDS/Aurora & Redshift

**Interview Focus Areas:**
- Multi-AZ vs. Read replicas
- Performance tuning: indexes, query optimization
- Automated backups and recovery
- Redshift for analytics: MPP architecture, distribution keys
- Cost optimization: Reserved instances

**Key Concepts:**

```python
# RDS optimization
import psycopg2
from psycopg2.pool import SimpleConnectionPool

# Connection pooling (critical for Lambda)
connection_pool = SimpleConnectionPool(1, 5,
    host="mydb.c9akciq32.us-east-1.rds.amazonaws.com",
    port=5432,
    database="mydb",
    user="admin",
    password="password"
)

def query_with_optimization(query, params):
    """
    RDS query optimization
    """
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()

        # Use prepared statements (parameterized queries)
        cursor.execute(query, params)

        # Fetch in batches
        rows = cursor.fetchall()

        return rows
    finally:
        connection_pool.putconn(conn)

# Redshift optimization
def create_optimized_redshift_table():
    """
    Redshift table design best practices
    """
    create_table_sql = """
    CREATE TABLE fact_orders (
        order_id BIGINT,
        customer_id INT,
        order_date DATE,
        amount DECIMAL(10,2),
        status VARCHAR(20)
    )
    DISTKEY (customer_id)           -- Distribution key for co-location
    SORTKEY (order_date, customer_id);  -- Sort key for query optimization

    -- Create indexes on common filter columns
    CREATE INDEX idx_status ON fact_orders (status);
    """

    # Vacuum and analyze regularly
    vacuum_sql = "VACUUM FULL ANALYZE fact_orders;"

def unload_redshift_to_s3():
    """
    Unload data efficiently (faster than SELECT INTO S3)
    """
    unload_sql = """
    UNLOAD (
        SELECT * FROM fact_orders
        WHERE year = 2024
    )
    TO 's3://my-bucket/unload/fact_orders/'
    WITH CREDENTIALS 'aws_iam_role=arn:aws:iam::123456789:role/RedshiftRole'
    PARALLEL ON
    ALLOWOVERWRITE;
    """
```

**Interview Q&A:**
- Q: "When would you use Redshift vs. Athena for analytics?"
  - A: "Redshift: repetitive queries, complex joins, real-time dashboards. Athena: ad-hoc queries, infrequent patterns. Redshift costs ~$3/hour, Athena ~$5/TB scanned. Use Redshift Spectrum to query S3 data."

- Q: "Design a Redshift schema for a dimensional model"
  - A: "Create fact table with DISTKEY on foreign key, SORTKEY on date. Create dimension tables denormalized. Use Slowly Changing Dimensions Type 2 for history. Vacuum regularly."

---

## Data Engineering Patterns

### Pattern 1: Configuration-Driven ETL
Your strength from Freddie Mac experience.

```python
# Configuration file (JSON or YAML)
{
  "pipelines": [
    {
      "name": "customer_data_pipeline",
      "schedule": "0 2 * * *",  # 2 AM daily
      "stages": [
        {
          "name": "extract",
          "source": "rds",
          "connection": "postgres_prod",
          "query": "SELECT * FROM customers WHERE updated_at > ?",
          "incrementalKey": "updated_at"
        },
        {
          "name": "transform",
          "type": "spark",
          "operations": [
            {"type": "filter", "condition": "status = 'active'"},
            {"type": "aggregate", "groupBy": ["country"], "metrics": ["sum(amount)"]}
          ]
        },
        {
          "name": "load",
          "destination": "s3",
          "path": "s3://datalake/customer_summary",
          "format": "parquet",
          "partitionBy": ["country", "year", "month"]
        }
      ],
      "errorHandling": {
        "retries": 3,
        "backoffMultiplier": 2,
        "notificationChannel": "sns:error-alerts"
      }
    }
  ]
}

# Framework to execute configuration
class ConfigurableETL:
    def __init__(self, config_file):
        self.config = self.load_config(config_file)

    def execute_pipeline(self, pipeline_name):
        pipeline = next(p for p in self.config['pipelines']
                       if p['name'] == pipeline_name)

        for stage in pipeline['stages']:
            self.execute_stage(stage, pipeline.get('errorHandling'))

    def execute_stage(self, stage, error_config):
        try:
            if stage['type'] == 'extract':
                data = self.extract_data(stage)
            elif stage['type'] == 'transform':
                data = self.transform_data(data, stage)
            elif stage['type'] == 'load':
                self.load_data(data, stage)
        except Exception as e:
            self.handle_error(e, error_config)
            raise
```

**Interview Q&A:**
- Q: "Why use configuration-driven ETL?"
  - A: "Separates business logic from infrastructure. Data engineers can modify pipelines without code changes. Easier auditing and compliance tracking. Enables self-service for non-technical users."

---

### Pattern 2: Real-Time Data Lineage & Governance
Your strength from Freddie Mac.

```python
# Data lineage tracking
class DataLineageTracker:
    def __init__(self, dynamodb_table):
        self.table = dynamodb_table
        self.neptune = boto3.client('neptune-data')

    def track_lineage(self, source, transformation, destination):
        """
        Track data flow through pipeline
        """
        lineage_record = {
            'source': source,
            'transformation': transformation,
            'destination': destination,
            'timestamp': datetime.now().isoformat(),
            'data_quality_checks': []
        }

        # Store in DynamoDB for quick lookup
        self.table.put_item(Item=lineage_record)

        # Store in Neptune for graph queries
        self.neptune.execute_gremlin_query(
            GremlinQuery=f"""
            g.addV('dataset').property('name', '{destination}')
             .addE('derivedFrom').to(g.V().has('name', '{source}'))
            """
        )

    def get_upstream_sources(self, dataset_name):
        """
        Find all source datasets for a given output
        """
        query = f"""
        g.V().has('name', '{dataset_name}')
         .in('derivedFrom').values('name').dedup()
        """
        return self.neptune.execute_gremlin_query(GremlinQuery=query)

    def validate_data_quality(self, dataset, rules):
        """
        Execute data quality checks
        """
        results = {
            'dataset': dataset,
            'checks': [],
            'passed': True
        }

        for rule in rules:
            if rule['type'] == 'row_count':
                count = self.get_row_count(dataset)
                passed = count >= rule['min_rows']
            elif rule['type'] == 'duplicate_check':
                duplicates = self.check_duplicates(dataset, rule['key'])
                passed = duplicates == 0

            results['checks'].append({
                'rule': rule['name'],
                'passed': passed,
                'timestamp': datetime.now().isoformat()
            })

            if not passed:
                results['passed'] = False

        return results
```

---

### Pattern 3: Self-Service Data Tools
Your strength from Freddie Mac.

```python
# Self-service monitoring dashboard
from flask import Flask, jsonify
import boto3

app = Flask(__name__)
emr = boto3.client('emr')

@app.route('/api/job-status/<cluster_id>', methods=['GET'])
def get_cluster_status(cluster_id):
    """
    Self-service endpoint for EMR job monitoring
    """
    try:
        response = emr.describe_cluster(ClusterId=cluster_id)
        cluster = response['Cluster']

        return jsonify({
            'cluster_id': cluster_id,
            'status': cluster['Status']['State'],
            'step_count': len(emr.list_steps(ClusterId=cluster_id)['Steps']),
            'master_public_dns': cluster.get('MasterPublicDNSName'),
            'applications': [app['Name'] for app in cluster['Applications']],
            'metrics': {
                'running_nodes': cluster['Status']['StateChangeReason'],
                'total_nodes': cluster['RequestedInstanceCount']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/copy-snowflake-table', methods=['POST'])
def copy_snowflake_to_s3():
    """
    Self-service interface for copying Snowflake tables to S3
    """
    data = request.json
    table_name = data['table_name']
    s3_path = data['s3_path']

    # Trigger Glue job or Lambda function
    glue = boto3.client('glue')
    response = glue.start_job_run(
        JobName='snowflake-to-s3-job',
        Arguments={
            '--table': table_name,
            '--output-path': s3_path
        }
    )

    return jsonify({'job_id': response['JobRunId']})

@app.route('/api/prepay-monitoring', methods=['GET'])
def prepay_job_monitoring():
    """
    Self-service dashboard for prepay modelers to track EMR jobs
    """
    cluster_id = request.args.get('cluster_id')

    try:
        steps = emr.list_steps(ClusterId=cluster_id)['Steps']

        return jsonify({
            'cluster_id': cluster_id,
            'jobs': [
                {
                    'job_name': step['Name'],
                    'status': step['Status']['State'],
                    'start_time': step.get('Status', {}).get('Timeline', {}).get('CreationDateTime'),
                    'end_time': step.get('Status', {}).get('Timeline', {}).get('EndDateTime'),
                    'log_uri': step.get('LogUri')
                }
                for step in steps
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Architecture & Design Questions

### Question Type 1: Design a Data Pipeline
**This is your core competency. Show architectural thinking.**

**Example Question:** "Design a real-time data pipeline for a marketing analytics platform processing 10M events/day from multiple channels (web, mobile, email) into a data warehouse."

**Your Approach:**
```
1. REQUIREMENTS CLARIFICATION (most important)
   - Latency requirement? (real-time vs. batch)
   - Data volume/velocity? (10M/day = ~116/second)
   - Data format? (JSON, Avro, Protobuf)
   - Retention period?
   - Downstream use cases?

2. ARCHITECTURE DESIGN

   Ingestion Layer:
   - API Gateway + Lambda for REST endpoints (scales to millions/second)
   - Kinesis Data Stream or MSK (Kafka) for buffering (reliability)
   - Use Kinesis Firehose for auto-scaling delivery to S3

   Processing Layer:
   - Lambda + Firehose for simple transformations (cost-efficient)
   - Kinesis Analytics for real-time aggregations
   - Alternative: Apache Flink on ECS for complex stateful processing

   Storage Layer:
   - S3 for raw data (year/month/day/hour partitioning)
   - Redshift for structured warehouse (real-time dashboard queries)
   - DynamoDB for hot data (last 24 hours for real-time dashboards)
   - Athena for ad-hoc queries

   Monitoring:
   - CloudWatch alarms on Kinesis iterator age
   - DLQ for failed records
   - Data quality checks on transformation accuracy

3. TRADE-OFFS DISCUSSION

   Kinesis vs. Kafka:
   - Kinesis: managed, simpler ops, higher cost
   - Kafka: more control, cheaper, more operational overhead
   - I'd recommend Kinesis for 10M/day (MSK better if 100M/day+)

   Lambda vs. EMR vs. Flink:
   - Lambda: cost-effective for sub-second latency, simple logic
   - EMR: better for batch processing historical data
   - Flink: needed for stateful operations (sessionization, time windows)
   - I'd use Lambda + Firehose for ingestion, separate Flink for analytics

4. COST ESTIMATION
   - Kinesis: $0.065/shard-hour (~$55/month per shard)
   - Lambda: ~$5-10/month for 10M invocations
   - S3: ~$20/month for storage
   - Firehose delivery: $0.029/GB = ~$300/month for 10TB/month
   - Total: ~$400-600/month

5. FAILOVER & DISASTER RECOVERY
   - Multi-AZ deployment for Kinesis
   - S3 cross-region replication for disaster recovery
   - DLQ for failed records with alerting
   - RTO: 5 minutes, RPO: 5 minutes
```

**Interview Tips for Architecture Questions:**
1. **Ask clarifying questions first** - Don't assume requirements
2. **Start simple, add complexity** - Begin with basic architecture, address scale issues
3. **Discuss trade-offs** - Every choice has pros/cons. Show you understand them
4. **Consider non-functional requirements** - Cost, availability, compliance, operational burden
5. **Draw diagrams** - Use tools like Draw.io or Lucidchart. Be clear about data flow
6. **Reference your experience** - "At Freddie Mac, we handled similar scale with..."

---

### Question Type 2: Optimization & Troubleshooting

**Example:** "Your Spark job on EMR is taking 10 hours for a 1TB dataset. It used to take 2 hours. What's your approach?"

**Your Response:**
```
INVESTIGATION PHASE (critical):
1. Check Spark UI:
   - Task duration across stages (which stage is slow?)
   - Shuffle size and network I/O
   - GC time (garbage collection overhead)
   - Memory pressure

2. Check data characteristics:
   - Dataset size growth? (1TB used to be smaller)
   - Skewed partitions? (some tasks much slower than others)
   - New columns with NULL values?

DIAGNOSIS & SOLUTION:

If slow stage is a join:
- Enable Adaptive Query Execution (Spark 3.x): auto-skew handling
- Check join order: large_table.join(small_table)
- Use bucketing if join key is stable

If slow stage is aggregation:
- Reduce number of partitions (too many small tasks)
- Check groupBy cardinality (group by user_id on 1TB might be 10M unique)

If GC overhead is high:
- Increase executor memory gradually
- Use --conf spark.executor.memoryOverhead=3g

If disk I/O is slow:
- Check EMR instance type (GP3 vs GP2 storage)
- Increase HDFS replication factor if available

If shuffle network is bottleneck:
- Enable adaptive skew join
- Increase number of shuffle partitions: spark.sql.shuffle.partitions=2000

IMPLEMENTATION:
1. Create test job with isolated change
2. Run on subset of data
3. Measure improvement
4. Roll out to production

PREVENTIVE MEASURES:
- Set up Spark job profiling in CI/CD
- Use CloudWatch metrics to track historical performance
- Add data quality checks (monitor input size growth)
```

**Interview Tips:**
- Show systematic troubleshooting, not random guessing
- Reference actual tools (Spark UI, CloudWatch, logs)
- Discuss trade-offs (more memory vs. cost)

---

## Hands-On Practice

### Practice Area 1: EMR Cluster Optimization

**Challenge:** Optimize an EMR cluster for cost and performance

```bash
# Your repository has EMR examples, review:
# - failover_ver3/ for production patterns
# - datalake/ for data lake setup

# Create a test cluster with optimizations:
aws emr create-cluster \
  --name "optimization-test" \
  --release-label emr-6.14.0 \
  --instances \
    InstanceGroups='[
      {
        Name=Master,
        Market=SPOT,
        InstanceRole=MASTER,
        InstanceType=r6g.xlarge,
        InstanceCount=1
      },
      {
        Name=Core,
        Market=SPOT,
        InstanceRole=CORE,
        InstanceType=r6g.2xlarge,
        InstanceCount=2,
        BidPrice=0.50
      },
      {
        Name=Task,
        Market=SPOT,
        InstanceRole=TASK,
        InstanceType=r6g.2xlarge,
        InstanceCount=0,
        BidPrice=0.50
      }
    ]' \
  --applications Name=Hadoop Name=Spark Name=Hive Name=Presto \
  --configurations file://emr-config.json \
  --auto-scaling-role EMR_AutoScaling_DefaultRole \
  --service-role EMR_DefaultRole
```

**EMR Config for optimization:**
```json
[
  {
    "Classification": "spark",
    "Properties": {
      "maximizeResourceAllocation": "true"
    }
  },
  {
    "Classification": "spark-defaults",
    "Properties": {
      "spark.sql.adaptive.enabled": "true",
      "spark.sql.adaptive.coalescePartitions.enabled": "true",
      "spark.dynamicAllocation.enabled": "true",
      "spark.dynamicAllocation.minExecutors": "2"
    }
  },
  {
    "Classification": "yarn-site",
    "Properties": {
      "yarn.resourcemanager.scheduler.class": "org.apache.hadoop.yarn.server.resourcemanager.scheduler.fair.FairScheduler",
      "yarn.scheduler.fair.allocation.file": "/etc/hadoop/conf/fair-scheduler.xml"
    }
  }
]
```

### Practice Area 2: Glue Job Optimization

**Challenge:** Create a Glue job that processes 10GB of data with incremental loading

```python
# See glue/ directory in your repo for examples
# Add incremental processing with job bookmarks

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame

glueContext = GlueContext(SparkContext.getOrCreate())
spark = glueContext.spark_session
job = Job(glueContext)

job.init('incremental-load-job', {"TempDir": "s3://my-bucket/temp"})

# Enable job bookmarks for incremental processing
job.bookmark_option = "job-bookmark-enabled"

# Read with partition pruning
dyf = glueContext.create_dynamic_frame.from_catalog(
    database="mydb",
    table_name="source_data",
    push_down_predicate="year >= 2024 AND month >= 01"
)

# Apply transformation
df = dyf.toDF()
df_transformed = df.filter(df.status == "active") \
    .groupBy("region") \
    .agg({
        "amount": "sum",
        "user_id": "count"
    }) \
    .withColumnRenamed("count(user_id)", "user_count")

# Write with partitioning for future query optimization
df_transformed.write \
    .mode("overwrite") \
    .partitionBy("region") \
    .parquet("s3://my-bucket/output/summary")

job.commit()
```

### Practice Area 3: Step Functions Pipeline

**Challenge:** Design a resilient multi-stage pipeline with error handling

```python
# See step-functions/ directory in your repo for examples
import json
import boto3

stepfunctions = boto3.client('stepfunctions')

# State machine definition with error handling
definition = {
    "Comment": "Data pipeline with resilience",
    "StartAt": "ExtractData",
    "States": {
        "ExtractData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789:function:extract-data",
            "TimeoutSeconds": 3600,
            "Retry": [
                {
                    "ErrorEquals": ["ServiceUnavailable"],
                    "IntervalSeconds": 2,
                    "MaxAttempts": 3,
                    "BackoffRate": 2.0
                }
            ],
            "Catch": [
                {
                    "ErrorEquals": ["States.ALL"],
                    "Next": "NotifyFailure"
                }
            ],
            "Next": "TransformData"
        },
        "TransformData": {
            "Type": "Task",
            "Resource": "arn:aws:emr:us-east-1:123456789:cluster/j-XXXXX",
            "Next": "LoadData"
        },
        "LoadData": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:us-east-1:123456789:function:load-data",
            "Next": "NotifySuccess"
        },
        "NotifySuccess": {
            "Type": "Task",
            "Resource": "arn:aws:sns:us-east-1:123456789:topic/success",
            "End": True
        },
        "NotifyFailure": {
            "Type": "Task",
            "Resource": "arn:aws:sns:us-east-1:123456789:topic/failure",
            "End": True
        }
    }
}

# Create state machine
response = stepfunctions.create_state_machine(
    name='data-pipeline',
    definition=json.dumps(definition),
    roleArn='arn:aws:iam::123456789:role/StepFunctionsRole'
)

print(f"State machine created: {response['stateMachineArn']}")
```

### Practice Area 4: Terraform Infrastructure as Code

**Challenge:** Deploy a complete data pipeline infrastructure with Terraform

**Project Structure:**
```
terraform/
├── variables.tf
├── main.tf
├── networking.tf
├── iam.tf
├── data_pipeline.tf
├── outputs.tf
└── terraform.tfvars
```

**variables.tf - Input Variables:**
```hcl
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "data-pipeline"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_subnet_cidrs" {
  description = "Private subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDR blocks"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "emr_master_instance_type" {
  description = "EMR master node instance type"
  type        = string
  default     = "r6g.xlarge"
}

variable "enable_s3_encryption" {
  description = "Enable S3 bucket encryption"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Owner   = "DataEngineering"
    Purpose = "DataPipeline"
  }
}
```

**main.tf - Provider and Resources:**
```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(
      var.tags,
      {
        Environment = var.environment
        Project     = var.project_name
      }
    )
  }
}

# S3 bucket for data lake with encryption
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-datalake-${var.environment}-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.s3_key.arn
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "archive_old_data"
    status = "Enabled"

    prefix = "data/"

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 730  # 2 years
    }
  }
}

# KMS key for encryption
resource "aws_kms_key" "s3_key" {
  description             = "KMS key for S3 encryption"
  deletion_window_in_days = 10
  enable_key_rotation     = true
}

resource "aws_kms_alias" "s3_key" {
  name          = "alias/${var.project_name}-s3"
  target_key_id = aws_kms_key.s3_key.key_id
}

# Get current AWS account ID
data "aws_caller_identity" "current" {}

# Output bucket name
output "data_lake_bucket" {
  value       = aws_s3_bucket.data_lake.id
  description = "Data lake S3 bucket name"
}
```

**networking.tf - VPC and Network Security:**
```hcl
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

# Public Subnets (for NAT Gateway, bastion, etc.)
resource "aws_subnet" "public" {
  count                   = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = var.public_subnet_cidrs[count.index]
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
  }
}

# Private Subnets (for EMR, RDS, Glue)
resource "aws_subnet" "private" {
  count             = length(var.private_subnet_cidrs)
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidrs[count.index]
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "${var.project_name}-private-subnet-${count.index + 1}"
  }
}

# Get available AZs
data "aws_availability_zones" "available" {
  state = "available"
}

# NAT Gateway (for private subnet internet access)
resource "aws_eip" "nat" {
  count  = length(var.public_subnet_cidrs)
  domain = "vpc"

  tags = {
    Name = "${var.project_name}-nat-eip-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count         = length(var.public_subnet_cidrs)
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = {
    Name = "${var.project_name}-nat-${count.index + 1}"
  }

  depends_on = [aws_internet_gateway.main]
}

# Route tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block      = "0.0.0.0/0"
    gateway_id      = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table" "private" {
  count  = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }

  tags = {
    Name = "${var.project_name}-private-rt-${count.index + 1}"
  }
}

resource "aws_route_table_association" "private" {
  count          = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Security Groups
resource "aws_security_group" "emr" {
  name_prefix = "${var.project_name}-emr-"
  description = "Security group for EMR cluster"
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-emr-sg"
  }
}

# EMR Master inbound rules
resource "aws_security_group_rule" "emr_master_ssh" {
  type              = "ingress"
  from_port         = 22
  to_port           = 22
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]  # Only from within VPC
  security_group_id = aws_security_group.emr.id
  description       = "SSH to EMR master"
}

resource "aws_security_group_rule" "emr_master_spark_ui" {
  type              = "ingress"
  from_port         = 8088
  to_port           = 8088
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]  # YARN UI
  security_group_id = aws_security_group.emr.id
  description       = "YARN UI access"
}

resource "aws_security_group_rule" "emr_master_spark_history" {
  type              = "ingress"
  from_port         = 18080
  to_port           = 18080
  protocol          = "tcp"
  cidr_blocks       = [var.vpc_cidr]  # Spark History UI
  security_group_id = aws_security_group.emr.id
  description       = "Spark History Server access"
}

# EMR outbound rules
resource "aws_security_group_rule" "emr_outbound" {
  type              = "egress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.emr.id
  description       = "Allow all outbound traffic"
}

# Security group for RDS (data source)
resource "aws_security_group" "rds" {
  name_prefix = "${var.project_name}-rds-"
  description = "Security group for RDS"
  vpc_id      = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

resource "aws_security_group_rule" "rds_from_emr" {
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  source_security_group_id = aws_security_group.emr.id
  security_group_id        = aws_security_group.rds.id
  description              = "PostgreSQL from EMR"
}

resource "aws_security_group_rule" "rds_outbound" {
  type              = "egress"
  from_port         = 0
  to_port           = 65535
  protocol          = "tcp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.rds.id
  description       = "Allow all outbound traffic"
}

# VPC endpoints for private access to AWS services
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${var.aws_region}.s3"
  route_table_ids = concat(
    [aws_route_table.public.id],
    aws_route_table.private[*].id
  )

  tags = {
    Name = "${var.project_name}-s3-endpoint"
  }
}

output "vpc_id" {
  value       = aws_vpc.main.id
  description = "VPC ID"
}

output "private_subnet_ids" {
  value       = aws_subnet.private[*].id
  description = "Private subnet IDs"
}

output "emr_security_group_id" {
  value       = aws_security_group.emr.id
  description = "EMR security group ID"
}

output "rds_security_group_id" {
  value       = aws_security_group.rds.id
  description = "RDS security group ID"
}
```

**iam.tf - IAM Roles and Policies:**
```hcl
# EMR Service Role
resource "aws_iam_role" "emr_service_role" {
  name = "${var.project_name}-emr-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "elasticmapreduce.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "emr_service_policy" {
  role       = aws_iam_role.emr_service_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceRole"
}

# EMR EC2 Instance Role (for nodes)
resource "aws_iam_role" "emr_ec2_instance_role" {
  name = "${var.project_name}-emr-ec2-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_instance_profile" "emr_ec2_instance_profile" {
  name = "${var.project_name}-emr-ec2-instance-profile"
  role = aws_iam_role.emr_ec2_instance_role.name
}

resource "aws_iam_role_policy_attachment" "emr_ec2_policy" {
  role       = aws_iam_role.emr_ec2_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonElasticMapReduceforEC2Role"
}

# Custom policy for EMR to access S3 and other services
resource "aws_iam_role_policy" "emr_custom_policy" {
  name = "${var.project_name}-emr-custom-policy"
  role = aws_iam_role.emr_ec2_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Sid    = "S3EncryptionDecryption"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = aws_kms_key.s3_key.arn
      },
      {
        Sid    = "GlueAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetTable",
          "glue:GetPartitions",
          "glue:GetDatabases",
          "glue:GetTables"
        ]
        Resource = "*"
      },
      {
        Sid    = "RDSAccess"
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Lambda execution role for data pipeline
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Sid    = "StepFunctionsAccess"
        Effect = "Allow"
        Action = [
          "states:StartExecution",
          "states:DescribeExecution"
        ]
        Resource = "arn:aws:states:*:*:*"
      },
      {
        Sid    = "CloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Glue service role
resource "aws_iam_role" "glue_role" {
  name = "${var.project_name}-glue-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_policy" {
  role       = aws_iam_role.glue_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"
}

resource "aws_iam_role_policy" "glue_s3_policy" {
  name = "${var.project_name}-glue-s3-policy"
  role = aws_iam_role.glue_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_lake.arn,
          "${aws_s3_bucket.data_lake.arn}/*"
        ]
      },
      {
        Sid    = "KMSAccess"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = aws_kms_key.s3_key.arn
      }
    ]
  })
}

# Step Functions execution role
resource "aws_iam_role" "stepfunctions_role" {
  name = "${var.project_name}-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "stepfunctions_policy" {
  name = "${var.project_name}-stepfunctions-policy"
  role = aws_iam_role.stepfunctions_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "LambdaExecution"
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = "arn:aws:lambda:${var.aws_region}:*:function:*"
      },
      {
        Sid    = "EMRAccess"
        Effect = "Allow"
        Action = [
          "elasticmapreduce:AddJobFlowSteps",
          "elasticmapreduce:DescribeStep",
          "elasticmapreduce:DescribeCluster"
        ]
        Resource = "*"
      }
    ]
  })
}

output "emr_service_role_arn" {
  value       = aws_iam_role.emr_service_role.arn
  description = "EMR service role ARN"
}

output "emr_ec2_instance_profile" {
  value       = aws_iam_instance_profile.emr_ec2_instance_profile.name
  description = "EMR EC2 instance profile name"
}

output "lambda_role_arn" {
  value       = aws_iam_role.lambda_role.arn
  description = "Lambda execution role ARN"
}

output "glue_role_arn" {
  value       = aws_iam_role.glue_role.arn
  description = "Glue service role ARN"
}

output "stepfunctions_role_arn" {
  value       = aws_iam_role.stepfunctions_role.arn
  description = "Step Functions execution role ARN"
}
```

**data_pipeline.tf - Application Resources:**
```hcl
# EMR Cluster
resource "aws_emr_cluster" "data_pipeline" {
  name           = "${var.project_name}-cluster"
  release_label  = "emr-6.14.0"
  applications   = [
    {
      Name = "Spark"
    },
    {
      Name = "Hadoop"
    },
    {
      Name = "Hive"
    }
  ]

  service_role      = aws_iam_role.emr_service_role.arn
  ec2_instance_profile = aws_iam_instance_profile.emr_ec2_instance_profile.arn

  ec2_attributes {
    subnet_id                      = aws_subnet.private[0].id
    instance_profile               = aws_iam_instance_profile.emr_ec2_instance_profile.name
    emr_managed_master_security_group = aws_security_group.emr.id
    emr_managed_slave_security_group  = aws_security_group.emr.id
    key_name                       = aws_key_pair.deployer.key_name  # Add if needed
  }

  master_instance_group {
    instance_count = 1
    instance_type  = var.emr_master_instance_type
    bid_price      = "0.30"  # Spot pricing
    market_type    = "SPOT"
  }

  core_instance_group {
    instance_count = 2
    instance_type  = "r6g.2xlarge"
    bid_price      = "0.40"
    market_type    = "SPOT"
  }

  task_instance_group {
    instance_count = 0  # Auto-scaling
    instance_type  = "r6g.2xlarge"
    bid_price      = "0.40"
    market_type    = "SPOT"
  }

  configurations_json = jsonencode([
    {
      Classification = "spark"
      Properties = {
        maximizeResourceAllocation = "true"
      }
    },
    {
      Classification = "spark-defaults"
      Properties = {
        "spark.sql.adaptive.enabled"                 = "true"
        "spark.sql.adaptive.skewJoin.enabled"        = "true"
        "spark.dynamicAllocation.enabled"            = "true"
        "spark.dynamicAllocation.minExecutors"       = "2"
        "spark.dynamicAllocation.maxExecutors"       = "10"
      }
    }
  ])

  tags = {
    Name = "${var.project_name}-emr-cluster"
  }

  depends_on = [
    aws_security_group.emr,
    aws_iam_role_policy.emr_custom_policy
  ]
}

# Note: Uncomment if you have a key pair
# resource "aws_key_pair" "deployer" {
#   key_name   = "${var.project_name}-key"
#   public_key = file("~/.ssh/id_rsa.pub")
# }

output "emr_cluster_id" {
  value       = aws_emr_cluster.data_pipeline.id
  description = "EMR cluster ID"
}

output "emr_cluster_dns" {
  value       = aws_emr_cluster.data_pipeline.master_public_dns
  description = "EMR master node public DNS"
}
```

**Deploy Terraform:**
```bash
# Initialize Terraform
terraform init

# Plan changes
terraform plan -out=tfplan

# Apply changes
terraform apply tfplan

# View outputs
terraform output

# Destroy (for cleanup)
terraform destroy
```

**Interview Points on Infrastructure-as-Code:**
- Explain why IaC is critical for data pipelines (reproducibility, versioning, compliance)
- Discuss state management (remote state, locking, secrets)
- Talk about module design for reusability
- Show understanding of least privilege (minimal IAM permissions)

---

### Practice Area 5: IAM Policy Design & Security

**Interview Scenario:** "Design IAM permissions for a data engineer who needs access to S3, Glue, EMR, and Redshift but nothing else"

**Least Privilege Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3DataLakeAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::my-datalake/*",
        "arn:aws:s3:::my-datalake"
      ],
      "Condition": {
        "StringLike": {
          "s3:key": "data/*"
        }
      }
    },
    {
      "Sid": "GlueCatalogAccess",
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions",
        "glue:UpdatePartition",
        "glue:BatchCreatePartition",
        "glue:GetDatabases",
        "glue:GetTables"
      ],
      "Resource": [
        "arn:aws:glue:*:*:catalog",
        "arn:aws:glue:*:*:database/prod_*",
        "arn:aws:glue:*:*:table/prod_*/*"
      ]
    },
    {
      "Sid": "GlueJobExecution",
      "Effect": "Allow",
      "Action": [
        "glue:StartJobRun",
        "glue:GetJobRun",
        "glue:GetJobRuns",
        "glue:GetJob"
      ],
      "Resource": "arn:aws:glue:*:*:job/data-engineering-*"
    },
    {
      "Sid": "EMRClusterAccess",
      "Effect": "Allow",
      "Action": [
        "elasticmapreduce:DescribeCluster",
        "elasticmapreduce:ListInstances",
        "elasticmapreduce:ListSteps",
        "elasticmapreduce:DescribeStep",
        "elasticmapreduce:GetBlockPublicAccessConfiguration"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    },
    {
      "Sid": "EMRAddSteps",
      "Effect": "Allow",
      "Action": [
        "elasticmapreduce:AddJobFlowSteps"
      ],
      "Resource": "arn:aws:elasticmapreduce:us-east-1:*:cluster/j-*",
      "Condition": {
        "StringLike": {
          "elasticmapreduce:ResourceTag/Project": "DataEngineering"
        }
      }
    },
    {
      "Sid": "RedshiftQueryAccess",
      "Effect": "Allow",
      "Action": [
        "redshift:DescribeClusters",
        "redshift:DescribeTables",
        "redshift:DescribeTableRestoreStatus",
        "redshift-data:ExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult"
      ],
      "Resource": [
        "arn:aws:redshift:*:*:cluster:prod-warehouse"
      ]
    },
    {
      "Sid": "PassRoleForServices",
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": [
        "arn:aws:iam::*:role/glue-service-role",
        "arn:aws:iam::*:role/emr-service-role"
      ],
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": [
            "glue.amazonaws.com",
            "elasticmapreduce.amazonaws.com"
          ]
        }
      }
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws-glue/*"
    },
    {
      "Sid": "DenyRootLevelS3Access",
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": "*",
      "Condition": {
        "StringNotLike": {
          "s3:key": "data/*"
        }
      }
    },
    {
      "Sid": "DenyHighRiskActions",
      "Effect": "Deny",
      "Action": [
        "iam:*",
        "organizations:*",
        "account:*",
        "elasticmapreduce:TerminateJobFlows",
        "redshift:DeleteCluster"
      ],
      "Resource": "*"
    }
  ]
}
```

---

### Practice Area 6: Networking & Security Groups Deep Dive

**Common Interview Question:** "Design a multi-tier architecture where EMR processes data from RDS, outputs to S3, but RDS is not publicly accessible. How do you secure this?"

**Architecture Diagram (Text):**
```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Account                          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ VPC (10.0.0.0/16)                                    │  │
│  │                                                       │  │
│  │  Public Subnets                                       │  │
│  │  ┌──────────────────┐   ┌──────────────────┐        │  │
│  │  │ NAT Gateway      │   │ Internet Gateway │        │  │
│  │  │ 10.0.101.0/24    │   │                  │        │  │
│  │  └──────────────────┘   └──────────────────┘        │  │
│  │                             │                        │  │
│  │  Private Subnets            │                        │  │
│  │  ┌────────────────┐   ┌─────────────────┐          │  │
│  │  │ EMR Cluster    │───│ RDS (Private)   │          │  │
│  │  │ 10.0.1.0/24    │   │ 10.0.2.0/24     │          │  │
│  │  │ SG: EMR-SG     │   │ SG: RDS-SG      │          │  │
│  │  └────────────────┘   └─────────────────┘          │  │
│  │         ↓                                            │  │
│  │  ┌────────────────────────────────────┐            │  │
│  │  │ S3 Endpoint (Gateway)               │            │  │
│  │  │ No data leaves VPC                  │            │  │
│  │  └────────────────────────────────────┘            │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Security Group Configuration:**

**EMR Security Group (emr-sg):**
```hcl
# Inbound Rules
- SSH (22): from bastion host or VPC CIDR
- YARN UI (8088): from VPC CIDR only
- Spark History (18080): from VPC CIDR only
- Presto (8080): from VPC CIDR only
- Self-reference for node communication

# Outbound Rules
- HTTPS (443): to S3, Glue, CloudWatch (for logs and metadata)
- Port 5432: to RDS security group
- DNS (53): for name resolution
```

**RDS Security Group (rds-sg):**
```hcl
# Inbound Rules
- PostgreSQL (5432): ONLY from EMR-SG
- MySQL (3306): ONLY from EMR-SG (if using MySQL)

# Outbound Rules
- Deny all (data flows in, not out)
```

**Security Best Practices Code:**
```python
# This shows how to verify security group rules
import boto3

ec2 = boto3.client('ec2')

def audit_security_groups(vpc_id):
    """Audit security groups for compliance"""

    response = ec2.describe_security_groups(
        Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
    )

    issues = []

    for sg in response['SecurityGroups']:
        # Check for overly permissive inbound rules
        for rule in sg['IpPermissions']:
            if rule.get('IpRanges'):
                for ip_range in rule['IpRanges']:
                    if ip_range['CidrIp'] == '0.0.0.0/0':
                        # Flag if it's not HTTP/HTTPS
                        if rule['FromPort'] not in [80, 443]:
                            issues.append({
                                'sg_id': sg['GroupId'],
                                'issue': f"Public access to port {rule['FromPort']}",
                                'severity': 'HIGH'
                            })

    return issues

def create_secure_database_sg(vpc_id, emr_sg_id):
    """Create secure RDS security group"""

    sg_response = ec2.create_security_group(
        GroupName='rds-secure',
        Description='Secure RDS - EMR access only',
        VpcId=vpc_id
    )

    rds_sg_id = sg_response['GroupId']

    # Allow traffic ONLY from EMR
    ec2.authorize_security_group_ingress(
        GroupId=rds_sg_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'UserIdGroupPairs': [
                    {
                        'GroupId': emr_sg_id,
                        'Description': 'PostgreSQL from EMR'
                    }
                ]
            }
        ]
    )

    # Revoke all outbound by default
    ec2.revoke_security_group_egress(
        GroupId=rds_sg_id,
        IpPermissions=[
            {
                'IpProtocol': '-1',
                'FromPort': -1,
                'ToPort': -1,
                'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            }
        ]
    )

    return rds_sg_id

def create_emr_with_private_networking(vpc_id, subnet_id, sg_id):
    """Create EMR cluster with no public IP"""

    emr = boto3.client('emr')

    response = emr.create_cluster(
        Name='secure-emr-cluster',
        ReleaseLabel='emr-6.14.0',
        Instances={
            'InstanceGroups': [
                {
                    'Name': 'Master',
                    'Market': 'SPOT',
                    'InstanceRole': 'MASTER',
                    'InstanceType': 'r6g.xlarge',
                    'InstanceCount': 1,
                    'BidPrice': '0.30'
                },
                {
                    'Name': 'Core',
                    'Market': 'SPOT',
                    'InstanceRole': 'CORE',
                    'InstanceType': 'r6g.2xlarge',
                    'InstanceCount': 2,
                    'BidPrice': '0.40'
                }
            ],
            'Ec2SubnetId': subnet_id,  # Private subnet
            'EmrManagedMasterSecurityGroup': sg_id,
            'EmrManagedSlaveSecurityGroup': sg_id,
            'KeepJobFlowAliveWhenNoSteps': True
        },
        Applications=[
            {'Name': 'Spark'},
            {'Name': 'Hadoop'},
            {'Name': 'Hive'}
        ],
        ServiceRole='EMR_DefaultRole',
        JobFlowRole='EMR_EC2_DefaultRole'
    )

    return response['JobFlowId']
```

### Practice Area 7: Cross-Account & Cross-Region Access

**Real-World Scenario:** Your organization has:
- **Dev Account (111111111111)**: Development data pipelines
- **Prod Account (222222222222)**: Production data warehouse
- **Analytics Account (333333333333)**: Data scientists accessing prod data
- **Data stored in**: us-east-1, us-west-2, eu-west-1

**Architecture Diagram:**
```
┌─────────────────────────────┐
│ Dev Account (111...)        │
│ EMR Cluster                 │
│ Role: dev-emr-role          │
└──────────────┬──────────────┘
               │ AssumeRole
               │ (cross-account)
               ▼
┌──────────────────────────────────────────────────┐
│ Prod Account (222...)                            │
│                                                   │
│ ┌─────────────────┐      ┌────────────────────┐ │
│ │ S3 Data Lake    │      │ Glue Catalog       │ │
│ │ us-east-1       │      │ us-east-1          │ │
│ │ us-west-2 (copy)│      │ us-west-2 (copy)   │ │
│ └─────────────────┘      └────────────────────┘ │
│         ▲                                         │
│         │ S3 Replication (cross-region)          │
│         │ (via S3 bucket policies)               │
│         │                                         │
└──────────────────────────────────────────────────┘
               │ AssumeRole
               │ (cross-account)
               ▼
┌─────────────────────────────┐
│ Analytics Account (333...)  │
│ Lambda/Athena               │
│ Role: analyst-role          │
└─────────────────────────────┘
```

#### Part 1: Cross-Account S3 Access

**Setup: Dev EMR reads from Prod S3**

**In Production Account (222...):**

```hcl
# S3 bucket in production account
resource "aws_s3_bucket" "prod_datalake" {
  bucket = "prod-datalake-222222222222"
}

# Bucket policy allowing dev account to read
resource "aws_s3_bucket_policy" "prod_datalake_policy" {
  bucket = aws_s3_bucket.prod_datalake.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowDevAccountRead"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::111111111111:role/dev-emr-role"
        }
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.prod_datalake.arn,
          "${aws_s3_bucket.prod_datalake.arn}/*"
        ]
        Condition = {
          StringLike = {
            "s3:key" = "data/processed/*"  # Restrict to specific paths
          }
        }
      },
      {
        Sid    = "DenyUnencryptedUploads"
        Effect = "Deny"
        Principal = "*"
        Action = "s3:PutObject"
        Resource = "${aws_s3_bucket.prod_datalake.arn}/*"
        Condition = {
          StringNotEquals = {
            "s3:x-amz-server-side-encryption" = "aws:kms"
          }
        }
      }
    ]
  })
}

# KMS key policy allowing cross-account access
resource "aws_kms_key" "prod_s3_key" {
  description             = "KMS key for prod S3 with cross-account access"
  deletion_window_in_days = 10
  enable_key_rotation     = true

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM Root"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::222222222222:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowDevAccountDecrypt"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::111111111111:role/dev-emr-role"
        }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}
```

**In Development Account (111...):**

```hcl
# Cross-account role that dev EMR assumes
resource "aws_iam_role" "prod_data_access_role" {
  name = "dev-prod-data-access"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"  # EMR nodes run as EC2 instances
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Policy to assume the prod account role
resource "aws_iam_role_policy" "assume_prod_role" {
  name = "assume-prod-data-access"
  role = aws_iam_role.prod_data_access_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRole"
        Resource = "arn:aws:iam::222222222222:role/prod-data-access-role"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "dev-access-12345"  # Prevent confused deputy
          }
        }
      }
    ]
  })
}

# In Prod account, create the role being assumed
resource "aws_iam_role" "prod_data_access_role" {
  provider = aws.prod  # Use prod account provider

  name = "prod-data-access-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::111111111111:role/dev-prod-data-access"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "dev-access-12345"
          }
        }
      }
    ]
  })
}
```

**Python Code to Use Cross-Account S3:**

```python
import boto3
from botocore.exceptions import ClientError

class CrossAccountS3Access:
    def __init__(self, role_arn, external_id, region='us-east-1'):
        """
        Initialize cross-account S3 access
        role_arn: arn:aws:iam::222222222222:role/prod-data-access-role
        external_id: dev-access-12345
        """
        sts = boto3.client('sts', region_name=region)

        try:
            # Assume the cross-account role
            assumed_role = sts.assume_role(
                RoleArn=role_arn,
                RoleSessionName='cross-account-session',
                ExternalId=external_id,
                DurationSeconds=3600
            )

            credentials = assumed_role['Credentials']

            # Create S3 client with temporary credentials
            self.s3_client = boto3.client(
                's3',
                region_name=region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            self.s3_resource = boto3.resource(
                's3',
                region_name=region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            print(f"Successfully assumed role: {role_arn}")

        except ClientError as e:
            print(f"Error assuming role: {e}")
            raise

    def read_from_prod_s3(self, bucket, key):
        """Read file from production S3 using cross-account access"""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read()
        except ClientError as e:
            print(f"Error reading from S3: {e}")
            raise

    def list_prod_bucket(self, bucket, prefix=''):
        """List objects in production bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        except ClientError as e:
            print(f"Error listing bucket: {e}")
            raise

# Usage in Spark job on Dev EMR
def read_prod_data_in_spark():
    from pyspark.sql import SparkSession

    spark = SparkSession.builder.appName("CrossAccountRead").getOrCreate()

    # Assume prod account role
    access = CrossAccountS3Access(
        role_arn='arn:aws:iam::222222222222:role/prod-data-access-role',
        external_id='dev-access-12345',
        region='us-east-1'
    )

    # Now read from prod S3
    df = spark.read.parquet(
        's3a://prod-datalake-222222222222/data/processed/2024/'
    )

    return df
```

---

#### Part 2: Cross-Region S3 Replication

**Setup: Prod data in us-east-1 replicated to us-west-2 and eu-west-1**

```hcl
# Primary bucket in us-east-1 (Prod account)
resource "aws_s3_bucket" "prod_primary" {
  provider = aws.prod_us_east_1
  bucket   = "prod-datalake-primary"
}

# Enable versioning (required for replication)
resource "aws_s3_bucket_versioning" "prod_primary" {
  provider = aws.prod_us_east_1
  bucket   = aws_s3_bucket.prod_primary.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Replication role
resource "aws_iam_role" "s3_replication_role" {
  provider = aws.prod_us_east_1
  name     = "s3-replication-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "s3_replication_policy" {
  provider = aws.prod_us_east_1
  name     = "s3-replication-policy"
  role     = aws_iam_role.s3_replication_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.prod_primary.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging"
        ]
        Resource = "${aws_s3_bucket.prod_primary.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags"
        ]
        Resource = "${aws_s3_bucket.prod_replica_west.arn}/*"
      }
    ]
  })
}

# Replica bucket in us-west-2
resource "aws_s3_bucket" "prod_replica_west" {
  provider = aws.prod_us_west_2
  bucket   = "prod-datalake-replica-west"
}

resource "aws_s3_bucket_versioning" "prod_replica_west" {
  provider = aws.prod_us_west_2
  bucket   = aws_s3_bucket.prod_replica_west.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Enable replication on primary bucket
resource "aws_s3_bucket_replication_configuration" "prod_replication" {
  provider = aws.prod_us_east_1
  role     = aws_iam_role.s3_replication_role.arn
  bucket   = aws_s3_bucket.prod_primary.id

  rule {
    id     = "replicate-to-west"
    status = "Enabled"

    filter {
      prefix = "data/processed/"
    }

    destination {
      bucket       = aws_s3_bucket.prod_replica_west.arn
      storage_class = "INTELLIGENT_TIERING"

      replication_time {
        status = "Enabled"
        time {
          minutes = 15  # RTC - replication within 15 minutes
        }
      }

      metrics {
        status = "Enabled"
        event_threshold {
          minutes = 15
        }
      }
    }

    delete_marker_replication {
      status = "Enabled"
    }
  }
}

# Replica bucket in eu-west-1
resource "aws_s3_bucket" "prod_replica_eu" {
  provider = aws.prod_eu_west_1
  bucket   = "prod-datalake-replica-eu"
}

resource "aws_s3_bucket_versioning" "prod_replica_eu" {
  provider = aws.prod_eu_west_1
  bucket   = aws_s3_bucket.prod_replica_eu.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Secondary replication rule
resource "aws_s3_bucket_replication_configuration" "prod_replication_eu" {
  provider = aws.prod_us_east_1
  role     = aws_iam_role.s3_replication_role.arn
  bucket   = aws_s3_bucket.prod_primary.id

  rule {
    id     = "replicate-to-eu"
    status = "Enabled"

    filter {
      prefix = "data/processed/"
    }

    destination {
      bucket = aws_s3_bucket.prod_replica_eu.arn

      replication_time {
        status = "Enabled"
        time {
          minutes = 15
        }
      }
    }
  }

  depends_on = [
    aws_s3_bucket_versioning.prod_primary
  ]
}
```

---

#### Part 3: Cross-Account Cross-Region Data Access

**Scenario: Analytics team in us-west-2 reads replicated data from Prod in eu-west-1**

```hcl
# In Prod EU Account, allow Analytics account to read
resource "aws_s3_bucket_policy" "prod_eu_analytics_access" {
  provider = aws.prod_eu_west_1
  bucket   = aws_s3_bucket.prod_replica_eu.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowAnalyticsRead"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::333333333333:role/analyst-role"
        }
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.prod_replica_eu.arn,
          "${aws_s3_bucket.prod_replica_eu.arn}/*"
        ]
      }
    ]
  })
}

# In Analytics account, assume cross-account role
resource "aws_iam_role" "analyst_role" {
  provider = aws.analytics
  name     = "analyst-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = ["lambda.amazonaws.com", "athena.amazonaws.com"]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "analyst_s3_policy" {
  provider = aws.analytics
  name     = "analyst-s3-policy"
  role     = aws_iam_role.analyst_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadProdDataCrossRegion"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::prod-datalake-replica-eu",
          "arn:aws:s3:::prod-datalake-replica-eu/*",
          "arn:aws:s3:::prod-datalake-replica-west",
          "arn:aws:s3:::prod-datalake-replica-west/*"
        ]
      },
      {
        Sid    = "AthenaQueryExecution"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults"
        ]
        Resource = "*"
      },
      {
        Sid    = "AthenaOutputBucket"
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "arn:aws:s3:::analytics-results/*"
      }
    ]
  })
}
```

**Python: Analytics Reading Cross-Region Data**

```python
import boto3

class CrossRegionCrossAccountAnalytics:
    def __init__(self, regions=['eu-west-1', 'us-west-2']):
        """Access data across regions and accounts"""
        self.athena_clients = {
            region: boto3.client('athena', region_name=region)
            for region in regions
        }

    def query_cross_region_data(self, region, bucket, sql_query):
        """
        Execute Athena query on cross-region, cross-account data
        """
        athena = self.athena_clients[region]

        # Create external table pointing to prod data
        create_table = f"""
        CREATE EXTERNAL TABLE IF NOT EXISTS prod_data (
            date STRING,
            user_id STRING,
            amount DECIMAL(10,2),
            status STRING
        )
        PARTITIONED BY (year STRING, month STRING)
        STORED AS PARQUET
        LOCATION 's3://prod-datalake-replica-{region[:2]}/data/processed/'
        """

        # Execute query
        response = athena.start_query_execution(
            QueryString=sql_query,
            QueryExecutionContext={
                'Database': 'cross_account_analytics'
            },
            ResultConfiguration={
                'OutputLocation': 's3://analytics-results/athena/'
            }
        )

        query_execution_id = response['QueryExecutionId']

        # Wait for query completion
        waiter = athena.get_waiter('query_execution_complete')
        waiter.wait(QueryExecutionId=query_execution_id)

        return query_execution_id

    def get_cross_region_summary(self):
        """Get summary across EU and US regions"""
        query = """
        SELECT
            region,
            year,
            month,
            COUNT(*) as total_records,
            SUM(amount) as total_amount,
            AVG(amount) as avg_amount
        FROM prod_data
        WHERE year = '2024'
        GROUP BY region, year, month
        """

        # Query EU region
        eu_result = self.query_cross_region_data('eu-west-1', 'prod-datalake-replica-eu', query)

        # Query US West region
        us_result = self.query_cross_region_data('us-west-2', 'prod-datalake-replica-west', query)

        return {
            'eu_query_id': eu_result,
            'us_query_id': us_result
        }
```

---

#### Part 4: Interview Q&A on Cross-Account/Cross-Region

**Q1: "Design access for a dev team to read prod data safely"**

**Answer Framework:**
```
1. PRINCIPLE: Least privilege + audit trail

2. SETUP:
   - Prod account: S3 bucket with encryption
   - Dev account: IAM role with AssumeRole permission
   - Cross-account role in Prod: allows specific S3 actions
   - External ID: prevents confused deputy problem

3. SECURITY LAYERS:
   - S3 bucket policy: restrict to dev account role + external ID
   - KMS key policy: allow decrypt only from dev account
   - IAM policy: limit to specific paths (s3:key condition)
   - CloudTrail: audit all cross-account access

4. IMPLEMENTATION:
   - Terraform: separate prod and dev providers
   - Python: use STS AssumeRole before accessing S3
   - Monitoring: CloudWatch alarms on failed AssumeRole attempts

5. BENEFITS:
   - Prod data stays in prod account (compliance)
   - Audit trail shows who accessed what (security)
   - Can revoke access instantly (role policy change)
```

**Q2: "How do you handle data replication across regions for disaster recovery?"**

**Answer Framework:**
```
1. S3 Replication Configuration (RTC = Replication Time Control)
   - Primary in us-east-1
   - Replicas in us-west-2, eu-west-1
   - Replication within 15 minutes (RTC)
   - Automatic delete marker replication

2. CHALLENGES & SOLUTIONS:
   - Cost: Use S3 Intelligent-Tiering on replicas
   - Latency: Use CloudFront for frequently accessed data
   - Consistency: Application must handle eventual consistency
   - Failover: DNS/routing switches to replica region

3. MONITORING:
   - S3 Replication metrics (replication latency)
   - CloudWatch alerts if replication falls behind
   - Cross-region sync validation (periodic checksums)

4. MY EXPERIENCE:
   - At Freddie Mac: replicated financial data to 3 regions
   - RTC ensured 15-minute RPO
   - Saved millions using Intelligent-Tiering
```

**Q3: "What's the 'Confused Deputy' problem and how do you prevent it?"**

**Answer Framework:**
```
CONFUSED DEPUTY PROBLEM:
- Attacker gives permission: A→assume→B role
- Your code: B→access→C resources (B has permissions)
- Attacker tricks you into accessing wrong resource
- Result: security breach through privilege escalation

SOLUTION: External ID
- Dev asks: "Assume my role and validate external ID"
- Prod role requires BOTH:
  1. Principal is dev account
  2. External ID matches (secret)
- Attacker can't know the external ID

EXAMPLE:
{
  "Condition": {
    "StringEquals": {
      "sts:ExternalId": "unique-secret-12345"
    }
  }
}

MY BEST PRACTICE:
- External ID = random 32-char string (rotated quarterly)
- Store in Secrets Manager
- Log all AssumeRole attempts
```

---

## Common Interview Questions

### Data Engineering Deep-Dive Questions

**Q1: Explain your data lineage and governance approach at Freddie Mac**
```
A: At Freddie Mac, I built a real-time data lineage tracking system:

ARCHITECTURE:
- Glue Catalog as metadata hub (source of truth)
- Neptune graph database for lineage queries
- DynamoDB for high-speed lookup of data quality metrics
- Lambda functions to capture lineage on job completion

KEY FEATURES:
1. Automatic lineage discovery from Glue job logs
2. Schema evolution tracking with version history
3. Data quality checks integrated with pipeline (no manual validation)
4. Self-service dashboard for data consumers to find data sources

BUSINESS VALUE:
- Compliance: full audit trail for financial data
- Data discovery: reduced time to find relevant datasets
- Impact analysis: know what breaks if upstream dataset changes
- Privacy: track PII across entire data platform

TECHNICAL HIGHLIGHTS:
- Used Gremlin queries for traversing lineage graph
- Implemented real-time metrics using CloudWatch + DynamoDB
- Designed configuration-driven approach for extensibility
```

**Q2: Design a configuration-driven ETL system**
```
A: My philosophy: separate business logic from infrastructure

BENEFITS:
- Non-technical users can modify pipelines (YAML/JSON config)
- Version control for pipeline definitions
- Easy to add new sources without code changes
- Testable configurations

COMPONENTS:
1. Configuration schema (YAML):
   - Sources: database/S3/API connections
   - Transformations: SQL/Spark operations
   - Destinations: table definitions
   - Error handling: retries, notifications

2. Metadata-driven execution:
   - Load config from DynamoDB
   - Generate Spark code from config
   - Execute and track results

3. Orchestration:
   - AWS Step Functions or Apache Airflow
   - Triggered by schedule or event
   - Retries with exponential backoff

EXAMPLE USE CASE:
At Freddie Mac, I used this for:
- eMBS pipeline monitoring with 200+ data sources
- Self-service table copy from Snowflake to S3
- Automatic failure detection and alerting
```

**Q3: How do you optimize a slow Spark job?**
```
A: Systematic approach (not random tuning):

STEP 1: PROFILE THE JOB
- Spark UI: identify slow stages
- Task duration: find skewed tasks
- Memory: check GC overhead
- Network: check shuffle size

STEP 2: IDENTIFY ROOT CAUSE
- Join issue? → Use adaptive skew join, reorder joins
- Shuffle issue? → Reduce partitions or use bucketing
- Memory issue? → Increase executor memory, optimize code
- I/O issue? → Use broadcast, increase parallelism

STEP 3: FIX WITH DATA UNDERSTANDING
- Example: Group by had 10M unique values, caused 10M tasks
  → Solution: Sample data first, understand cardinality

- Example: Join on non-clustered column
  → Solution: Pre-compute join key, use bucketing

MEASUREMENT:
- Always measure improvement
- Track metrics in CloudWatch for trending
- Document configuration changes

MY BEST PRACTICE:
Monitor from day 1, not after job becomes slow!
```

**Q4: Compare EMR vs. Glue for data processing**
```
A: Depends on use case:

EMR (EMR on EC2):
✓ Best for: Complex transformations, heavy Spark jobs, sustained compute
✓ Cost: Cheaper for long-running jobs
✓ Control: Full control over cluster configuration
✗ Ops burden: Need to manage scaling, monitoring
✗ Cold start: Cluster launch time ~5-10 minutes

Glue:
✓ Best for: Scheduled ETL, moderate workloads
✓ Ops: Fully managed, automatic scaling
✓ Integration: Native AWS Catalog integration
✓ Ease: No cluster management
✗ Cost: Expensive for sustained workloads ($5-10/hour per DPU)
✗ Limited control: Less optimization options

MY APPROACH:
- Glue for daily pipelines < 2 hours processing time
- EMR for ad-hoc analysis, complex transformations
- Hybrid: Use Glue to trigger EMR for heavy lifting
```

**Q5: Design a real-time dashboard that processes 1M events/hour**
```
A: Requirements clarification:
- Latency: <1 second? < 5 seconds?
- Metrics: Count, average, percentiles?
- Retention: Last 1 hour? 24 hours?

RECOMMENDED ARCHITECTURE:
1. Ingestion: Kinesis Data Streams (1M = 1 shard)
2. Processing:
   - Kinesis Analytics for real-time aggregations (seconds latency)
   - Alternative: Lambda + DynamoDB (100ms latency, higher cost)
3. Storage:
   - DynamoDB for hot data (last 1 hour)
   - S3 for archival
4. Frontend: QuickSight or custom web dashboard

COST BREAKDOWN:
- Kinesis: ~$55/month for 1 shard
- DynamoDB: ~$200/month on-demand
- Dashboard: ~$200/month QuickSight
- Total: ~$500/month

SCALING:
- At 10M events/hour: upgrade to MSK (Kafka) or Kinesis Fleet
- Add Redshift for historical analysis
- Use Firehose for automatic S3 delivery
```

### System Design Questions

**Q1: Design a data warehouse for a SaaS company**
```
Key Design Decisions:

LAYER 1: Raw Data Lake
- S3 raw zone (year/month/day partitioning)
- Automated Glue crawlers for discovery
- 7-year retention with Glacier archival

LAYER 2: Conformed Data Layer
- Snowflake tables (star schema)
- Fact tables: orders, events, subscriptions
- Dimension tables: customers, products, dates

LAYER 3: Analytics Layer
- Redshift for BI dashboards (real-time requirements)
- Athena for ad-hoc queries (cost-efficient)
- Spark for ML model training

GOVERNANCE:
- Data catalog in Glue
- Data quality checks before load
- Role-based access control via IAM
- Encryption at rest (KMS) and in transit

COST OPTIMIZATION:
- Use Redshift Spectrum for infrequent queries
- Archive cold data to Glacier
- Reserved instances for predictable load
- Estimated: $5K/month for 100GB warehouse
```

---

## Your Competitive Advantages

### 1. Real Production Experience
You have deep, battle-tested experience:
- **Freddie Mac (Current)**: Configuration-driven pipelines, data lineage, governance
- **MessageBird**: Real-time streaming, Apache Flink, high-availability design
- **Fannie Mae**: Large-scale ETL, risk analytics, financial data processing

**Interview Strategy:**
- Use specific examples: "At Freddie Mac, we processed 100TB/month with..."
- Discuss challenges you solved: "We had S3 eventual consistency issues, so we..."
- Show thought process: "We chose Lambda over EMR because..."

### 2. Deep Technical Expertise
You can speak authoritatively about:
- PySpark performance tuning (you've optimized 2TB+ jobs)
- EMR cluster architecture and cost optimization
- Configuration-driven design patterns (proven at scale)
- Data governance implementation

**Interview Advantage:**
- Interviewers ask technical follow-ups → you're comfortable with details
- Example: "Tell us about your worst performance bug" → You have real stories

### 3. Full-Stack Data Engineering
You understand entire data pipeline:
- Infrastructure (CloudFormation, Terraform)
- Data processing (Spark, Hive, Athena)
- Analytics (Redshift, BI tools)
- Monitoring (CloudWatch, Datadog)

**Interview Advantage:**
- Questions about "how would you monitor this?" → You have real experience
- Questions about cost optimization → You've worked with large AWS bills

### 4. Soft Skills from Seniority
- Architecture and design thinking (you designed systems, not just components)
- Leadership (mentored team members at Fannie Mae)
- Documentation and communication (Confluence, design docs)
- Cross-functional collaboration (worked with modelers, BI teams)

**Interview Advantage:**
- Behavioral questions flow naturally from your experience
- Example: "Tell us about a time you influenced architecture decision..."

---

## Study Schedule (4 weeks)

### Week 1: Foundation & Assessment
- **Mon-Tue**: Review CLAUDE.md and your repository structure
- **Wed**: Deep dive into your strongest area (Glue/EMR - you know this)
- **Thu**: Identify gaps (networking, disaster recovery)
- **Fri**: Create study plan based on interview role

### Week 2: Core Services Deep Dive
- **Mon-Tue**: Lambda, Step Functions, and async patterns
- **Wed-Thu**: RDS/Aurora/Redshift and database optimization
- **Fri**: Practice architecture questions with your experiences

### Week 3: Advanced Topics & Gaps
- **Mon-Tue**: VPC, networking, security (your gap area)
- **Wed**: Disaster recovery, backup strategies
- **Thu**: Cost optimization and billing
- **Fri**: Practice mixed questions

### Week 4: Interview Simulation
- **Daily**: 1 architecture question with 20-min thinking, 10-min discussion
- **Focus**: Your experiences (reference them naturally)
- **Record**: Practice explaining technical decisions concisely

---

## Practice Repositories and Resources

**From Your Own Repo (Best Practice!):**
```
- aws-monitoring/ - Monitoring and alerting patterns
- failover_ver3/ - Production failover system (excellent example)
- glue/ - Glue job examples
- datalake/ - Data lake architecture
- step-functions/ - Step Functions orchestration
- iceberg/ - Modern data format patterns
- airflow/ - Orchestration alternatives
```

**External Resources:**
- AWS Whitepapers: "Well-Architected Framework", "Disaster Recovery"
- Exam guides: AWS Certified Data Engineer Associate
- YouTube: "AWS re:Invent" talks on data engineering
- Practice: Build small projects using your repo as reference

---

## Final Interview Tips

### Before the Interview
1. **Review your resume in detail** - Interviewers will ask about specific projects
2. **Prepare 3-5 concrete examples** - Use STAR method (Situation, Task, Action, Result)
3. **Know your numbers** - "We processed 100TB/month", "Reduced latency by 70%"
4. **Prepare counter-examples** - "A design choice that didn't work..."

### During Architecture Questions
1. **Draw the diagram** - Visual communication matters
2. **Ask clarifying questions** - "Is this real-time or batch?" "What's the scale?"
3. **Start simple, add complexity** - "Basic approach: S3 + Glue. For 100x scale: add Kinesis..."
4. **Discuss trade-offs** - "EMR costs 2x but gives us better optimization"
5. **Reference your experience** - "At Freddie Mac, we solved similar by..."

### During Technical Deep-Dives
1. **Show your thinking process** - "First I'd check the Spark UI to see if it's a shuffle issue"
2. **Use correct terminology** - "Partition pruning", "predicate pushdown", not "filtering"
3. **Ask clarifying questions** - "What does the explain plan show?"
4. **Reference best practices** - "We use Adaptive Query Execution for Spark 3.x"

### On Weak Areas
1. **Be honest** - "I haven't used Redshift much, but I understand the concept..."
2. **Show learning ability** - "I've been studying distributed systems patterns..."
3. **Relate to your experience** - "It's similar to how YARN schedules tasks in EMR..."

---

## Success Criteria

You're interview-ready when you can:

1. ✅ Discuss any AWS data service from first principles
2. ✅ Design a data pipeline for any scale (1GB to 10PB)
3. ✅ Explain a performance problem and systematic debugging approach
4. ✅ Articulate architectural trade-offs with confidence
5. ✅ Reference your production experience naturally in technical discussions
6. ✅ Handle "Why did you choose X over Y?" with thoughtful reasoning
7. ✅ Discuss failure scenarios and mitigation strategies
8. ✅ Ask good questions about role, team, and technical challenges

---

## Additional Resources

**AWS Documentation to Review:**
- [AWS Glue Best Practices](https://docs.aws.amazon.com/glue/latest/dg/best-practices.html)
- [EMR Spark Optimization](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/spark-configure.html)
- [Step Functions Best Practices](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)
- [Lambda Performance Optimization](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)

**Books Worth Reading:**
- "Designing Data-Intensive Applications" by Martin Kleppmann
- "The Art of Scalability" by Martin Abbott & Michael Fisher

**Certifications to Consider:**
- AWS Certified Data Engineer Associate (validates your expertise)
- AWS Certified Solutions Architect Professional (demonstrates architecture thinking)

---

## Next Steps

1. **Schedule preparation**: Use the 4-week plan above
2. **Practice implementation**: Use your repo examples to build mini-projects
3. **Record your responses**: Practice explaining concepts concisely
4. **Mock interviews**: Use friends/mentors in tech for feedback
5. **Stay confident**: You have 18+ years of experience and real AWS expertise

Good luck with your interviews! Your hands-on production experience is your greatest asset.

---

**Document Version**: 1.0
**Created**: May 2024
**Last Updated**: May 2024
**Status**: Ready for Interview Preparation
