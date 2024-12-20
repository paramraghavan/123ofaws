import boto3
import sqlite3
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
        self.conn = sqlite3.connect(':memory:')

        # Create the metadata table
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_name TEXT,
                year INTEGER,
                month INTEGER,
                day INTEGER,
                file_name TEXT,
                full_path TEXT
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
        Load metadata from S3 bucket into SQLite

        Args:
            prefix (str): S3 prefix to start listing from
        """
        paginator = self.s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                metadata = self.parse_s3_path(obj['Key'])
                if metadata:
                    self.conn.execute('''
                        INSERT INTO file_metadata 
                        (job_name, year, month, day, file_name, full_path)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        metadata['job_name'],
                        metadata['year'],
                        metadata['month'],
                        metadata['day'],
                        metadata['file_name'],
                        metadata['full_path']
                    ))

        self.conn.commit()

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
        cursor = self.conn.execute('''
            SELECT full_path
            FROM file_metadata
            WHERE job_name = ? AND year = ?
        ''', (job_name, year))

        files = cursor.fetchall()

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

        # Load into SQLite
        combined_df.to_sql(table_name, self.conn, if_exists='replace', index=False)

        return combined_df

    def query(self, sql: str) -> pd.DataFrame:
        """
        Execute SQL query on the in-memory database

        Args:
            sql (str): SQL query to execute

        Returns:
            pandas DataFrame with query results
        """
        return pd.read_sql_query(sql, self.conn)


# Example usage
if __name__ == "__main__":
    # Initialize loader
    loader = S3DataLoader('your-bucket-name')

    # Load metadata
    loader.load_metadata()

    # Load specific job data
    df = loader.load_data('example-job', 2024)

    # Example query
    result = loader.query("""
        SELECT job_name, year, COUNT(*) as file_count
        FROM file_metadata
        GROUP BY job_name, year
        ORDER BY year DESC, job_name
    """)
    print(result)
