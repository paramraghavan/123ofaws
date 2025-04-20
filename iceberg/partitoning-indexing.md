# Partitioning and Performance Optimization in Apache Iceberg

Yes, Apache Iceberg tables support both partitioning and several performance optimization techniques that significantly
improve query performance.

## Partitioning in Iceberg

Iceberg supports sophisticated partitioning strategies:

1. **Standard Partitioning**: Tables can be partitioned by any column or expression
   ```sql
   CREATE TABLE my_table (
     id bigint,
     ts timestamp,
     data string
   )
   USING iceberg
   PARTITIONED BY (days(ts))
   ```

2. **Hidden Partitioning**: Unlike Hive, Iceberg doesn't require partition columns in the table schema

3. **Partition Evolution**: You can change partitioning schemes without rewriting data
   ```sql
   ALTER TABLE my_table REPLACE PARTITION FIELD days(ts) WITH months(ts)
   ```

4. **Custom Transforms**: Iceberg supports various partition transforms:
    - `year`, `month`, `day`, `hour` for time-based partitioning
    - `bucket(n)` for hash-based partitioning
    - `truncate(w)` for reducing cardinality
    - bucket(8, customer_id) is a partitioning transform that:
        - Takes the customer_id column value
        - Applies a hash function to it
        - Divides the hash result into 8 buckets (numbered 0-7)
        - Assigns each record to one of these buckets based on the hash

## Performance Optimizations

Iceberg uses several techniques to optimize query performance beyond partitioning:

1. **Metadata-Based Filtering**: Iceberg maintains statistics in metadata files that allow skipping entire data files
   without reading them

2. **Z-Order Clustering**: Iceberg supports Z-order to co-locate related data
   ```sql
   CALL catalog.system.rewrite_data_files(
     table => 'my_table',
     strategy => 'sort',
     sort_order => 'zorder(col1, col2)'
   )
   ```

3. **File Compaction**: Small files are automatically compacted to reduce file count and improve scan performance
   ```sql
   CALL catalog.system.rewrite_data_files(
     table => 'my_table', 
     strategy => 'binpack'
   )
   ```

4. **Statistics and Bloom Filters**: Iceberg maintains column statistics and can use Bloom filters for data skipping

## Performance Impact

The performance improvements from these features can be significant:

- **Partition Pruning**: Can reduce data scanned by orders of magnitude by eliminating irrelevant partitions
- **Metadata Filtering**: Can skip 90%+ of data files in many analytical workloads
- **Proper Clustering**: Can reduce query times by 2-10x for selective queries
- **File Size Optimization**: Optimized file sizes can improve scan throughput by 2-3x

Unlike traditional databases that use B-tree indexes, Iceberg relies primarily on metadata-driven filtering and
partitioning rather than traditional indexes. This approach is better suited for distributed analytics on object storage
like S3.

For optimal performance, it's important to choose the right partitioning strategy based on your query patterns and
regularly perform maintenance operations like compaction and clustering.

# Determining the Optimal Number of Buckets for Hash Partitioning

When determining the appropriate number of buckets for hash partitioning in Apache Iceberg, you need to consider several
factors to balance performance, storage, and query patterns:

## Key Factors to Consider

1. **Data Volume**
    - Larger datasets typically benefit from more buckets
    - Rule of thumb: Aim for reasonable file sizes (128MB-1GB per file)
    - Calculate: `Total Data Size / Target File Size = Approximate Bucket Count`

2. **Query Parallelism**
    - Match bucket count to available processing parallelism
    - Consider the number of executors or slots in your processing engine
    - Example: If your Spark cluster has 20 executors, ~20 buckets might be efficient

3. **File Count Management**
    - Too many buckets create too many small files (the "small files problem")
    - Too few buckets limit parallelism and create oversized files
    - Each partition will have at least one file, so buckets × other partitions = minimum file count

4. **Access Patterns**
    - More selective queries benefit from more buckets
    - Scan-heavy workloads may perform better with fewer, larger files

## Practical Guidelines

- **Starting point**: Use a power of 2 (8, 16, 32, 64)
- **For small tables** (< 10GB): 4-8 buckets is often sufficient
- **For medium tables** (10GB-100GB): 16-32 buckets typically works well
- **For large tables** (> 100GB): 64-128 buckets may be appropriate
- **For very large tables** (> 1TB): 128-512 buckets, depending on concurrency

## Examples and Calculations

For a 250GB table with a target file size of 512MB:

```
250GB / 512MB = ~500 files
```

If you have other partitioning factors (e.g., by date with 30 date partitions):

```
500 files / 30 date partitions = ~17 files per date partition
```

So approximately 16 or 32 buckets would be reasonable.

## Monitoring and Adjusting

The optimal bucket count may change over time as your dataset grows. Monitor:

1. Query performance
2. File sizes and counts
3. Scan efficiency metrics

Iceberg allows for partition evolution, so you can adjust the bucket count if needed:

```sql
ALTER TABLE my_catalog.my_db.customers 
REPLACE PARTITION FIELD bucket(8, customer_id) WITH bucket(16, customer_id)
```

# Apache Iceberg Partitioning and Optimization Examples

Here are practical examples of how to implement partitioning and performance optimization techniques with Apache Iceberg
using PySpark:

## 1. Creating a Partitioned Iceberg Table

```python
from pyspark.sql import SparkSession

# Initialize Spark with Iceberg support
spark = SparkSession.builder
.appName("Iceberg Partitioning Example")
.config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions")
.config("spark.sql.catalog.my_catalog", "org.apache.iceberg.spark.SparkCatalog")
.config("spark.sql.catalog.my_catalog.type", "hadoop")
.config("spark.sql.catalog.my_catalog.warehouse", "s3://your-bucket/warehouse")
.getOrCreate()

# Create a partitioned table - Time-based partitioning
spark.sql("""
CREATE TABLE my_catalog.my_db.sales (
  id BIGINT,
  product_id BIGINT,
  customer_id BIGINT,
  quantity INT,
  price DECIMAL(10,2),
  sale_date TIMESTAMP
)
USING iceberg
PARTITIONED BY (years(sale_date), months(sale_date))
""")

# Create a partitioned table - Hash-based partitioning
spark.sql("""
CREATE TABLE my_catalog.my_db.customers (
  customer_id BIGINT,
  name STRING,
  email STRING,
  region STRING
)
USING iceberg
PARTITIONED BY (bucket(8, customer_id))
""")

# Create a partitioned table - Combined partitioning strategy
spark.sql("""
CREATE TABLE my_catalog.my_db.events (
  event_id BIGINT,
  user_id BIGINT,
  event_type STRING,
  event_time TIMESTAMP,
  country STRING
)
USING iceberg
PARTITIONED BY (days(event_time), truncate(country, 2))
""")
```

## 2. Inserting Data and Querying

```python
# Insert sample data
spark.sql("""
INSERT INTO my_catalog.my_db.sales VALUES
  (1, 101, 1001, 5, 99.99, '2023-01-15 10:30:00'),
  (2, 102, 1002, 1, 199.99, '2023-01-20 14:45:00'),
  (3, 103, 1001, 3, 29.99, '2023-02-05 09:15:00'),
  (4, 101, 1003, 2, 99.99, '2023-03-10 16:20:00')
""")

# Query that benefits from partition pruning
spark.sql("""
SELECT sum(quantity * price) as revenue
FROM my_catalog.my_db.sales
WHERE months(sale_date) = 1  -- Only scans January data
""").show()

# This query only needs to read files from January 2023 partition
```

## 3. File Compaction to Optimize Small Files

```python
# Perform file compaction for better performance
spark.sql("""
CALL my_catalog.system.rewrite_data_files(
  table => 'my_db.sales',
  strategy => 'binpack',
  options => map('min-input-files', '5', 'target-file-size-bytes', '536870912')
)
""")
```

## 4. Sorting Data for Better Locality

```python
# Rewrite files with Z-ordering
spark.sql("""
CALL my_catalog.system.rewrite_data_files(
  table => 'my_db.sales',
  strategy => 'sort',
  sort_order => 'zorder(product_id, customer_id)'
)
""")
```

## 5. Evolving Partition Schemes

```python
# Change partitioning scheme without rewriting data
spark.sql("""
ALTER TABLE my_catalog.my_db.sales 
REPLACE PARTITION FIELD months(sale_date) WITH days(sale_date)
""")

# Adding a new partition field
spark.sql("""
ALTER TABLE my_catalog.my_db.sales 
ADD PARTITION FIELD bucket(4, product_id)
""")
```

## 6. Checking Table Metadata and Partitioning

```python
# View current table partitioning
spark.sql("""
SELECT * FROM my_catalog.my_db.sales.`__partitions`
""").show()

# View table metadata
spark.sql("""
SELECT * FROM my_catalog.my_db.sales.`__metadata`
""").show()
```

## 7. Examining Partition Performance

```python
# Create a table with execution metrics
spark.sql("""
CREATE OR REPLACE TEMPORARY VIEW query_performance AS
SELECT query_text, 
       execution_time_ms,
       data_scanned_mb,
       result_rows
FROM (VALUES 
  ('SELECT * FROM sales WHERE months(sale_date) = 1', 1250, 5.2, 10000),
  ('SELECT * FROM sales /* no partition filter */', 9800, 105.8, 200000)
) AS t(query_text, execution_time_ms, data_scanned_mb, result_rows)
""")

# Compare performance
spark.sql("""
SELECT query_text,
       execution_time_ms,
       data_scanned_mb,
       result_rows,
       ROUND(data_scanned_mb / execution_time_ms * 1000, 2) AS scan_speed_mb_sec
FROM query_performance
ORDER BY execution_time_ms
""").show(truncate=False)
```

The last example demonstrates how partitioning in Iceberg can significantly reduce query execution time by scanning only
the relevant data partitions. In this simulated case, filtering by month resulted in scanning only ~5% of the data and
executing ~8x faster.

