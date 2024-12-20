I'll help you create a Python script that can pull data from S3 and load it into an in-memory SQLite database for
querying. We'll use boto3 for S3 access and sqlite3 for the database.

This script creates a `S3DataLoader` class that:

1. Creates an in-memory SQLite database
2. Loads metadata about files in the S3 bucket into a `file_metadata` table
3. Provides methods to load actual data from specific jobs/years into separate tables
4. Allows SQL querying of the loaded data

To use this script:

```python
# Initialize the loader
loader = S3DataLoader('your-bucket-name')

# Load metadata about all files
loader.load_metadata()

# Load data for a specific job and year
df = loader.load_data('your-job-name', 2024)

# Query the data using SQL
results = loader.query("""
    SELECT *
    FROM your_job_name_2024
    WHERE some_column > 100
    LIMIT 10
""")
```

The script uses:

- `boto3` for S3 access
- `sqlite3` for the in-memory database
- `pandas` for data manipulation and easy SQL integration

Key features:

1. Parses S3 paths to extract metadata
2. Handles pagination for large S3 buckets
3. Loads data into separate tables named `{job_name}_{year}`
4. Provides a simple query interface
5. Uses type hints for better code clarity
