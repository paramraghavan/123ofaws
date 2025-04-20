# Does iceberg use CPU and memory for database related overhead/work

Unlike traditional database systems like AWS RDS PostgreSQL or even serverless query engines like Amazon Athena, Apache
Iceberg follows a different architectural approach regarding computational resource usage.

## How Iceberg Uses Computational Resources

Iceberg is **not** a database engine itself, but rather a table format. This means:

1. **No Dedicated Resources**: Iceberg doesn't maintain its own persistent CPU or memory resources. It doesn't run as a
   server or service like PostgreSQL does.

2. **Processing Engine Dependent**: The computational resources needed for Iceberg operations depend entirely on the
   processing engine you're using (Spark, Flink, Trino, etc.).

3. **Metadata Operations**: Iceberg does have some overhead for metadata management, but these operations are executed
   by your processing engine, not by Iceberg itself.

## Resource Usage Comparison

| System           | Resource Model          | CPU/Memory Usage   | When Resources Are Used          |
|------------------|-------------------------|--------------------|----------------------------------|
| PostgreSQL (RDS) | Dedicated server        | Continuous         | Always running, even when idle   |
| Athena           | Serverless query engine | Per-query          | Only during active queries       |
| Iceberg          | Table format            | Embedded in engine | Only when accessed via an engine |

## What This Means in Practice

When you work with Iceberg:

1. Your processing engine (like Spark) loads the Iceberg libraries and does all the actual computation
2. When idle, there is no CPU or memory being used by Iceberg
3. There are no dedicated "Iceberg servers" running in your infrastructure
4. You don't have database connection overhead as with traditional databases

This approach gives you the benefits of a sophisticated table format with ACID transactions, schema evolution, and
partition evolution, without the operational overhead of maintaining a separate database system.

Note that some operations in Iceberg (like table maintenance or complex metadata operations) can require
significant resources from your processing engine, but these are used on-demand rather than continuously.

# Transactions

Yes, Apache Iceberg with S3 fully supports transactional updates and concurrency control. 
Here's how it works:

## Transactional Updates with Iceberg/S3

Iceberg provides true ACID (Atomicity, Consistency, Isolation, Durability) transactions on S3, enabling:

1. **UPDATE/DELETE/MERGE Operations**: You can issue standard SQL commands to modify data:
   ```sql
   -- Example update
   UPDATE iceberg_catalog.my_database.my_table
   SET status = 'completed'
   WHERE order_id = 1234
   ```

2. **Optimistic Concurrency Control**: Iceberg uses optimistic locking to manage concurrent operations:
    - Each operation checks if the table has changed since it started
    - If no conflict exists, changes are committed
    - If conflicts are detected, the operation can be retried

3. **Locking Mechanisms**: Iceberg offers several locking implementations:

    - **AWS DynamoDB Lock Manager**: For high-concurrency environments
   ```python
   .config("spark.sql.catalog.my_catalog.lock-impl", "org.apache.iceberg.aws.dynamodb.DynamoDbLockManager")
   .config("spark.sql.catalog.my_catalog.lock.table", "iceberg_locks")
   ```

    - **In-memory locks**: Simpler but only works within a single application
    - **Optimistic locking**: Default approach using metadata versioning

4. **Transaction Isolation**: Iceberg ensures snapshot isolation, meaning:
    - Readers always see a consistent snapshot
    - Writers don't block readers
    - Multiple concurrent writers can operate without corruption

5. **Atomicity**: Table changes are atomic - either fully applied or not at all, preventing partial updates

## Example PySpark Code for Transactional Updates

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder
.appName("Iceberg Transactions")
.config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
.config("spark.sql.catalog.my_catalog", "org.apache.iceberg.spark.SparkCatalog")
.config("spark.sql.catalog.my_catalog.type", "hadoop")
.config("spark.sql.catalog.my_catalog.warehouse", "s3://your-bucket/warehouse")
.config("spark.sql.catalog.my_catalog.lock-impl", "org.apache.iceberg.aws.dynamodb.DynamoDbLockManager")
.config("spark.sql.catalog.my_catalog.lock.table", "iceberg_locks")
.getOrCreate()

# Execute an UPDATE transaction
spark.sql("""
UPDATE my_catalog.my_database.my_table
SET value = 'new_value'
WHERE id = 1
""")

# Execute a MERGE transaction (upsert)
spark.sql("""
MERGE INTO my_catalog.my_database.target t
USING my_catalog.my_database.source s
ON t.id = s.id
WHEN MATCHED THEN UPDATE SET t.value = s.value
WHEN NOT MATCHED THEN INSERT (id, value) VALUES (s.id, s.value)
""")
```

Iceberg's transactional capabilities make it suitable for data warehousing and analytics workloads that require reliable
concurrent operations on S3 data.


