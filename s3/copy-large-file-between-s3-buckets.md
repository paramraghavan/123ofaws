There are several effective ways to copy large datasets like 3TB of Parquet files between S3 buckets. Let me explain the
two methods you mentioned plus a few additional options:

## 1. S3DistCp (S3 Distributed Copy)

S3DistCp is an extension of Hadoop's DistCp designed specifically for copying data to/from S3. It runs on EMR clusters
and is ideal for large-scale data transfers.

**When to use:** Best for very large datasets (multi-TB), when you need data transformation during copy, or when working
with EMR/Hadoop ecosystems.

**Example:**

```bash
# Launch EMR cluster first, then run:
s3-dist-cp \
  --src s3://source-bucket/parquet-data/ \
  --dest s3://destination-bucket/parquet-data/ \
  --srcPattern .*\.parquet \
  --outputCodec gzip \
  --targetSize 1073741824  # 1GB chunks
```

**Pros:** Extremely fast for large datasets, can compress/decompress during transfer, handles large file counts well
**Cons:** Requires EMR cluster (additional cost), more complex setup

## 2. AWS DataSync

DataSync is a managed service that simplifies data transfer between AWS storage services.

**When to use:** Good for one-time migrations, scheduled transfers, or when you want a managed solution without
infrastructure overhead.

**Example:**

```bash
# Create DataSync task via CLI
aws datasync create-task \
  --source-location-arn arn:aws:datasync:region:account:location/loc-source \
  --destination-location-arn arn:aws:datasync:region:account:location/loc-dest \
  --options VerifyMode=POINT_IN_TIME_CONSISTENT,OverwriteMode=ALWAYS
```

**Setup via Console:**

1. Go to DataSync in AWS Console
2. Create source location (S3 bucket)
3. Create destination location (S3 bucket)
4. Create and configure task
5. Start execution

**Pros:** Fully managed, built-in verification, handles metadata preservation
**Cons:** Can be slower than S3DistCp for very large datasets, per-GB pricing

## 3. AWS CLI S3 Sync (Simple but Effective)

For many use cases, the standard AWS CLI is sufficient and much simpler.

**Example:**

```bash
# Basic sync
aws s3 sync s3://source-bucket/parquet-data/ s3://destination-bucket/parquet-data/ \
  --storage-class STANDARD_IA \
  --exclude "*" \
  --include "*.parquet"

# With multipart and parallelization
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 16MB

aws s3 sync s3://source-bucket/parquet-data/ s3://destination-bucket/parquet-data/
```

## 4. S3 Batch Operations

For copying with additional processing or complex selection criteria.

**Example setup:**

1. Create inventory of source bucket
2. Create S3 Batch job with COPY operation
3. Specify source and destination details

## Performance Comparison for 3TB Transfer:

- **S3DistCp:** Fastest (2-4 hours with proper EMR sizing)
- **DataSync:** Moderate (4-8 hours)
- **AWS CLI:** Moderate to slow (6-12 hours depending on configuration)
- **S3 Batch Operations:** Moderate (4-6 hours)

## Recommendation for New Users:

**Start with AWS CLI** for simplicity:

```bash
# Step 1: Configure parallel transfers
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB

# Step 2: Test with small subset first
aws s3 sync s3://source-bucket/parquet-data/year=2024/month=01/ \
  s3://destination-bucket/parquet-data/year=2024/month=01/ --dryrun

# Step 3: Run actual sync
aws s3 sync s3://source-bucket/parquet-data/ s3://destination-bucket/parquet-data/
```

**Upgrade to DataSync** if you need:

- Scheduled transfers
- Built-in verification
- Transfer reporting
- Minimal setup complexity

**Use S3DistCp** only if:

- You're already using EMR
- You need maximum speed
- You want to transform data during transfer

For your 3TB Parquet dataset, start with AWS CLI with optimized settings, then moving to DataSync if you need the
additional features or better reliability.