import os
import boto3
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from typing import Dict, List, Optional, Union


class S3DataManager:
    """
    A class to manage datasets stored in S3 buckets and run SQL queries on them.

    This class allows users to:
    - Load datasets from S3 bucket/prefix combinations
    - Register those datasets as tables with custom names
    - Run SQL queries across multiple registered tables
    - Join tables using SQL
    """

    def __init__(self, spark: Optional[SparkSession] = None):
        """
        Initialize the S3DataManager.

        Args:
            spark: Optional SparkSession. If not provided, a new one will be created.
        """
        if spark is None:
            self.spark = (SparkSession.builder
                          .appName("S3DataManager")
                          .config("spark.sql.legacy.timeParserPolicy", "LEGACY")
                          .getOrCreate())
        else:
            self.spark = spark

        self.tables: Dict[str, str] = {}  # Maps table_name -> s3_path

    def _validate_s3_path(self, bucket: str, prefix: str) -> str:
        """
        Validate and format the S3 path.

        Args:
            bucket: S3 bucket name
            prefix: S3 prefix (folder path)

        Returns:
            Formatted S3 path
        """
        # Remove trailing slash from bucket if present
        bucket = bucket.rstrip('/')

        # Ensure prefix doesn't start with / but ends with /
        prefix = prefix.strip('/')
        if prefix:
            prefix = prefix + '/'

        return f"s3a://{bucket}/{prefix}"

    def check_s3_path_exists(self, bucket: str, prefix: str) -> bool:
        """
        Check if the specified S3 path exists.

        Args:
            bucket: S3 bucket name
            prefix: S3 prefix (folder path)

        Returns:
            True if the path exists, False otherwise
        """
        s3_client = boto3.client('s3')
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=1
            )
            return 'Contents' in response
        except Exception as e:
            print(f"Error checking S3 path: {e}")
            return False

    def register_dataset(self, bucket: str, prefix: str, table_name: str,
                         format: str = "parquet", options: Dict = None) -> bool:
        """
        Register a dataset from S3 as a temporary table.

        Args:
            bucket: S3 bucket name
            prefix: S3 prefix (folder path)
            table_name: Name to register the table as
            format: Format of the data (parquet, csv, json, etc.)
            options: Additional options for reading the data

        Returns:
            True if successful, False otherwise
        """
        s3_path = self._validate_s3_path(bucket, prefix)

        # Check if the path exists
        if not self.check_s3_path_exists(bucket, prefix):
            print(f"Warning: S3 path {s3_path} may not exist or is empty")

        try:
            # Read the data with provided options
            if options is None:
                options = {}

            if format.lower() == "csv" and "header" not in options:
                options["header"] = "true"

            reader = self.spark.read.format(format)
            for key, value in options.items():
                reader = reader.option(key, value)

            df = reader.load(s3_path)

            # Register as temp table
            df.createOrReplaceTempView(table_name)

            # Store the mapping
            self.tables[table_name] = s3_path

            print(f"Successfully registered '{table_name}' from {s3_path}")
            return True

        except Exception as e:
            print(f"Error registering dataset: {e}")
            return False

    def execute_sql(self, query: str):
        """
        Execute a SQL query against the registered tables.

        Args:
            query: SQL query to execute

        Returns:
            DataFrame with query results
        """
        try:
            return self.spark.sql(query)
        except Exception as e:
            print(f"Error executing SQL query: {e}")
            return None

    def list_tables(self):
        """
        List all registered tables.

        Returns:
            Dictionary mapping table names to their S3 paths
        """
        return self.tables

    def get_table_schema(self, table_name: str):
        """
        Get the schema of a registered table.

        Args:
            table_name: Name of the registered table

        Returns:
            Schema of the table or None if the table doesn't exist
        """
        if table_name not in self.tables:
            print(f"Table '{table_name}' not found")
            return None

        try:
            return self.spark.sql(f"SELECT * FROM {table_name} LIMIT 0").schema
        except Exception as e:
            print(f"Error getting schema: {e}")
            return None

    def preview_table(self, table_name: str, limit: int = 10):
        """
        Preview the contents of a registered table.

        Args:
            table_name: Name of the registered table
            limit: Maximum number of rows to preview

        Returns:
            DataFrame with preview data or None if the table doesn't exist
        """
        if table_name not in self.tables:
            print(f"Table '{table_name}' not found")
            return None

        try:
            return self.spark.sql(f"SELECT * FROM {table_name} LIMIT {limit}")
        except Exception as e:
            print(f"Error previewing table: {e}")
            return None

    def unregister_table(self, table_name: str):
        """
        Unregister a previously registered table.

        Args:
            table_name: Name of the table to unregister

        Returns:
            True if successful, False otherwise
        """
        if table_name not in self.tables:
            print(f"Table '{table_name}' not found")
            return False

        try:
            self.spark.sql(f"DROP TABLE IF EXISTS {table_name}")
            del self.tables[table_name]
            print(f"Table '{table_name}' unregistered")
            return True
        except Exception as e:
            print(f"Error unregistering table: {e}")
            return False