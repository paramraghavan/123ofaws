# Choosing the Right Partitioning Strategy and Maintenance Operations in Iceberg

The statement emphasizes two critical aspects of managing Iceberg tables effectively:

## 1. Choosing the Right Partitioning Strategy

Your partitioning strategy should be designed around your most common query patterns:

- **Time-based partitioning** (by year/month/day) works well for tables where queries typically filter by date ranges
- **Categorical partitioning** works well for commonly filtered dimensions with low cardinality (region, status,
  category)
- **Hash partitioning** works well for high-cardinality columns that are frequently used in equality filters
- **Combined strategies** can be optimal for complex query patterns

Choosing poorly can lead to:

- Over-partitioning (too many small files)
- Under-partitioning (not enough data skipping)
- Skewed partitions (some partitions much larger than others)

## 2. Regular Maintenance Operations

Iceberg tables require periodic maintenance to maintain optimal performance:

### File Compaction

Small files accumulate over time as data is ingested or updated, especially with streaming ingestion. Compaction merges
these small files into larger ones, which:

- Reduces the number of files to scan
- Improves read performance
- Decreases metadata overhead

Example compaction command:

```sql
CALL catalog.system.rewrite_data_files(
  table => 'my_db.my_table',
  strategy => 'binpack'
)
```

### Clustering/Sorting

Organizing data within files based on commonly queried columns improves locality and enables more efficient filtering:

```sql
CALL catalog.system.rewrite_data_files(
  table => 'my_db.my_table',
  strategy => 'sort',
  sort_order => 'customer_id,transaction_date DESC'
)
```

### Snapshot Expiration

Old snapshots should be expired to reclaim storage and improve metadata performance:

```sql
CALL catalog.system.expire_snapshots(
  table => 'my_db.my_table', 
  older_than => TIMESTAMP 'yesterday',
  retain_last => 5
)
```

### Orphan File Removal

After operations like snapshots expiration, orphaned files that are no longer referenced should be removed:

```sql
CALL catalog.system.remove_orphan_files(
  table => 'my_db.my_table'
)
```

These maintenance operations are essential for long-term performance as the table grows and evolves. Without them,
performance will gradually degrade due to fragmentation, increased file counts, and metadata bloat.