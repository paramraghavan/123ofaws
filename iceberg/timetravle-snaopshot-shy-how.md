# Time Travel Queries in Apache Iceberg

## What is Time Travel?

Time travel is one of Apache Iceberg's most powerful features, allowing you to query data as it existed at a specific
point in time using snapshots that are automatically created during table modifications.

## Why We Need Time Travel

Time travel capabilities serve several critical purposes:

1. **Auditing and Compliance**: Review exactly what data existed at any point in time for regulatory requirements

2. **Debugging and Validation**: Diagnose issues by comparing table states before and after problematic operations

3. **Reproducible Analysis**: Ensure consistent results by querying a stable dataset, even as the current table data
   changes

4. **Recovery**: Recover from accidental data modifications or deletions without restoring from backups

5. **Historical Analysis**: Compare current data with historical data to identify trends and patterns

## How Time Travel Works in Iceberg

Iceberg implements time travel through its snapshot architecture:

1. **Snapshot Creation**: Every write operation creates a new snapshot (table version)

2. **Metadata Tracking**: Each snapshot maintains references to the exact set of data files that comprised the table at
   that moment

3. **Versioning**: Snapshots are tracked in metadata files with timestamps and snapshot IDs

4. **Query Execution**: Time travel queries use metadata to determine which files to read, ignoring newer ones

## Time Travel Query Syntax

There are two main ways to specify point-in-time queries:

### 1. By Timestamp

```sql
-- Query data as of a specific timestamp
SELECT * FROM my_table FOR TIMESTAMP AS OF '2023-12-15 14:30:00.000'

-- Query data as of yesterday
SELECT * FROM my_table FOR TIMESTAMP AS OF (TIMESTAMP 'yesterday')
```

### 2. By Snapshot ID

```sql
-- Query data as of a specific snapshot ID
SELECT * FROM my_table FOR VERSION AS OF 8674362523846
```

## Example Explained

The code you shared:

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

This query:

1. Identifies what "yesterday" means based on the current date
2. Looks up the nearest snapshot that existed before or at that timestamp
3. Scans only the data files that were part of the table at that time
4. Further filters the result by the partition fields `year = 2024 AND month = 12`
5. Returns and displays the results

## Performance Considerations

Time travel queries are efficient because:

- They only read the files needed for that snapshot
- They leverage the same partition pruning as current queries
- Metadata operations quickly identify the relevant snapshot

However, keeping many snapshots increases metadata size, which is why snapshot expiration is an important maintenance
operation.