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

With Iceberg, you have multiple options to build a catalog with AWS. The most common is using AWS Glue as the Catalog implementation, where an Iceberg namespace is stored as a Glue Database, an Iceberg table is stored as a Glue Table, and every Iceberg table version is stored as a Glue TableVersion. Apache
Options include:
* AWS Glue Data Catalog (recommended for AWS integration)
* DynamoDB catalog (for high throughput applications)
* JDBC catalog with AWS RDS
