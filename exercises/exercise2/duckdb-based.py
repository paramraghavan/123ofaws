import boto3
import duckdb
import pandas as pd
from typing import List, Dict
import re
from datetime import datetime


class S3DataLoader:
    def __init__(self, bucket_name: str):
        """
        Initialize the S3 data loader with bucket name

        Args:
            bucket_name (str): Name of the S3 bucket
        """
        self.s3_client = boto3.client('s3')
        self.bucket_name = bucket_name
        self.conn = duckdb.connect(database=':memory:')

        # Create the metadata table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id BIGINT AUTO_INCREMENT,
                job_name VARCHAR,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                file_name VARCHAR,
                full_path VARCHAR,
                PRIMARY KEY(id)
            )
        ''')

    def parse_s3_path(self, s3_key: str) -> Dict:
        """
        Parse S3 key to extract metadata

        Args:
            s3_key (str): S3 key in format staging/job_name/year/month/day/file-name

        Returns:
            Dict containing parsed metadata
        """
        parts = s3_key.split('/')
        if len(parts) < 6:
            return None

        return {
            'job_name': parts[1],
            'year': int(parts[2]),
            'month': int(parts[3]),
            'day': int(parts[4]),
            'file_name': parts[5],
            'full_path': s3_key
        }

    def load_metadata(self, prefix: str = 'staging/'):
        """
        Load metadata from S3 bucket into DuckDB

        Args:
            prefix (str): S3 prefix to start listing from
        """
        metadata_list = []
        paginator = self.s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                metadata = self.parse_s3_path(obj['Key'])
                if metadata:
                    metadata_list.append(metadata)

        # Bulk insert using pandas DataFrame
        if metadata_list:
            df = pd.DataFrame(metadata_list)
            self.conn.execute("INSERT INTO file_metadata SELECT * FROM df")

    def load_data(self, job_name: str, year: int) -> pd.DataFrame:
        """
        Load data for specific job and year into a new table

        Args:
            job_name (str): Name of the job
            year (int): Year to load

        Returns:
            pandas DataFrame containing the loaded data
        """
        # Get relevant files
        files = self.conn.execute('''
            SELECT full_path
            FROM file_metadata
            WHERE job_name = ? AND year = ?
        ''', [job_name, year]).fetchall()

        # Load and concatenate all data
        dfs = []
        for file_path, in files:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            df = pd.read_csv(response['Body'])
            dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        combined_df = pd.concat(dfs, ignore_index=True)

        # Create table name
        table_name = f"{job_name}_{year}"

        # Load into DuckDB - DuckDB can efficiently handle the DataFrame directly
        self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM combined_df")

        return combined_df

    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query on the in-memory database

        Args:
            sql (str): SQL query to execute

        Returns:
            pandas DataFrame with query results
        """
        return self.conn.execute(sql).df()

    def close(self):
        """
        Close the database connection
        """
        self.conn.close()


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = S3DataLoader('your-bucket-name')

    # Load metadata
    loader.load_metadata()

    # Load specific job data
    df = loader.load_data('example-job', 2024)

    # Example query - DuckDB supports more SQL features than SQLite
    result = loader.query("""
        SELECT 
            job_name,
            year,
            COUNT(*) as file_count,
            MIN(month) as first_month,
            MAX(month) as last_month
        FROM file_metadata
        GROUP BY job_name, year
        ORDER BY year DESC, job_name
    """)
    print(result)

    # Don't forget to close the connection
    loader.close()
