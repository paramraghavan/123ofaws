I'll explain these AWS S3 data transfer commands and their usage:

## **aws s3 cp**

A high-level command for copying files to/from S3 buckets.

**Basic Usage:**

```bash
# Upload file to S3
aws s3 cp local-file.txt s3://bucket-name/path/

# Download from S3
aws s3 cp s3://bucket-name/file.txt ./local-directory/

# Copy between S3 buckets
aws s3 cp s3://source-bucket/file.txt s3://dest-bucket/

# Recursive copy (entire directories)
aws s3 cp ./local-folder s3://bucket-name/path/ --recursive
```

**Common Options:**

- `--exclude/--include`: Filter files
- `--storage-class`: Set storage tier (STANDARD, GLACIER, etc.)
- `--acl`: Set access permissions
- `--sse`: Enable server-side encryption

## **aws s3api**

Low-level API commands providing direct access to S3 REST API operations.

**Usage Examples:**

```bash
# Create bucket
aws s3api create-bucket --bucket my-bucket --region us-east-1

# Upload with more control
aws s3api put-object --bucket my-bucket --key file.txt --body local-file.txt

# Get object metadata
aws s3api head-object --bucket my-bucket --key file.txt

# Set bucket versioning
aws s3api put-bucket-versioning --bucket my-bucket \
  --versioning-configuration Status=Enabled

# Multipart upload for large files
aws s3api create-multipart-upload --bucket my-bucket --key large-file.zip
```

**When to use:** When you need fine-grained control over S3 operations or access to features not available in high-level
commands.

## **s3-dist-cp**

An Apache Hadoop tool optimized for distributed copying of large datasets in EMR (Elastic MapReduce) clusters.

**Usage Examples:**

```bash
# Copy data from S3 to HDFS
s3-dist-cp --src s3://source-bucket/data/ --dest hdfs:///user/hadoop/data/

# Copy with file grouping
s3-dist-cp --src s3://source-bucket/ --dest s3://dest-bucket/ \
  --groupBy '.*\.([0-9]+)\..*' --targetSize 128

# Copy with compression
s3-dist-cp --src s3://source-bucket/ --dest s3://dest-bucket/ \
  --outputCodec gz

# Copy with manifest
s3-dist-cp --src s3://source-bucket/ --dest s3://dest-bucket/ \
  --outputManifest manifest.txt
```

**Key Features:**

- Parallel processing across cluster nodes
- File concatenation and splitting
- On-the-fly compression/decompression
- Pattern-based file filtering

## **aws s3 sync**

Synchronizes directories and S3 prefixes, copying only new or updated files.

**Usage Examples:**

```bash
# Sync local to S3
aws s3 sync ./local-folder s3://bucket-name/folder/

# Sync S3 to local
aws s3 sync s3://bucket-name/folder/ ./local-folder

# Sync between S3 buckets
aws s3 sync s3://source-bucket/ s3://dest-bucket/

# Delete files in destination not in source
aws s3 sync ./folder s3://bucket/folder/ --delete

# Exclude certain files
aws s3 sync . s3://bucket/ --exclude "*.tmp" --exclude ".git/*"

# Only sync files modified in last 7 days
aws s3 sync . s3://bucket/ --exclude "*" --include "*.log" \
  --size-only
```

## **When to Use Each:**

**aws s3 cp**:

- Simple one-time copies
- Single file transfers
- Basic recursive directory copies

**aws s3api**:

- Automation requiring specific API features
- Complex bucket configurations
- Programmatic access needing detailed responses
- Multipart uploads for very large files

**s3-dist-cp**:

- EMR/Hadoop environments
- Massive dataset transfers (TB/PB scale)
- When you need distributed processing
- File aggregation or splitting requirements

**aws s3 sync**:

- Backup scenarios
- Keeping directories synchronized
- Incremental updates
- Website deployment
- Only transferring changed files

Each tool serves different use cases, with `s3 cp` and `s3 sync` being most common for everyday tasks, `s3api` for
advanced operations, and `s3-dist-cp` for big data workloads in EMR clusters.