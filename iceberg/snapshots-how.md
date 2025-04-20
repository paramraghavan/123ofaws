# Understanding Iceberg Snapshots

## What are Snapshots?

In Apache Iceberg, snapshots are point-in-time views of your table data. They're automatically created whenever data in
the table changes through operations like:

1. **INSERT**: Adding new records
2. **UPDATE**: Modifying existing records
3. **DELETE**: Removing records
4. **MERGE**: Performing upserts
5. **Maintenance operations**: Compaction, clustering, etc.

## Who Creates Snapshots?

Snapshots are created by the processing engines that operate on the Iceberg table, such as:

- Apache Spark
- Apache Flink
- Amazon Athena
- Snowflake
- Presto/Trino

The engine creates a snapshot when a transaction is committed, regardless of which user or process initiated the
operation.

## When are Snapshots Created?

Snapshots are created automatically at these times:

1. **At the end of each transaction**: Every successfully committed data modification creates a new snapshot
2. **At regular intervals**: For streaming workloads, snapshots may be created at configured checkpoints
3. **On explicit command**: Some operations like table optimizations force a new snapshot

## How Snapshots Work

Each snapshot:

- References data files that comprise the table at that moment
- Stores metadata about the table state
- Forms part of a chain of table history
- Is identified by a unique snapshot ID
- Has a timestamp when it was created

## Example Snapshot Lifecycle

```
1. Create table (Snapshot #1)
2. Insert initial data (Snapshot #2)
3. Update some records (Snapshot #3)
4. Run compaction operation (Snapshot #4)
5. Delete some records (Snapshot #5)
```

Each operation creates a new snapshot, and old snapshots remain until explicitly expired.

## Why Expire Old Snapshots?

Over time, this chain of snapshots grows and can:

- Consume significant metadata storage
- Slow down table operations
- Keep references to data files that could otherwise be deleted
- Increase the cost of metadata management

Regularly expiring old snapshots maintains performance while still keeping enough history for time travel and rollback
operations.