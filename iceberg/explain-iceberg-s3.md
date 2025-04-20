# Apache Iceberg

Apache Iceberg is an open table format for huge analytic datasets. It was originally developed at Netflix and is now an
Apache Software Foundation project. Key features include:

- **Table format**: Designed specifically for large-scale data processing
- **Schema evolution**: Allows changing table schema without moving or rewriting data
- **Partition evolution**: Supports changing partition schemes without data rewrites
- **Time travel**: Enables querying data as it existed at specific points in time
- **ACID transactions**: Ensures data consistency even with concurrent readers and writers
- **Compatibility**: Works with processing engines like Spark, Flink, Presto, and Trino

Iceberg is often used with data stored in S3, creating a powerful combination. S3 provides the underlying object
storage, while Iceberg adds table management capabilities on top, making it easier to work with large-scale data in data
lake environments.

With Iceberg, you have multiple options to build a catalog with AWS. The most common is using AWS Glue as the Catalog
implementation, where an Iceberg namespace is stored as a Glue Database, an Iceberg table is stored as a Glue Table, and
every Iceberg table version is stored as a Glue TableVersion. Apache
Options include:

* AWS Glue Data Catalog (recommended for AWS integration)
* DynamoDB catalog (for high throughput applications)
* JDBC catalog with AWS RDS

## Does Iceberg Use Computational Resources

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

Keep in mind some operations in Iceberg (like table maintenance or complex metadata operations) can require
significant resources from your processing engine, but these are used on-demand rather than continuously.