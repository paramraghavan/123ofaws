# Amazon S3 Complete Tutorial for AWS Developers

> **Master S3 from fundamentals to advanced patterns** - A comprehensive guide for beginners through experienced AWS developers

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [S3 Fundamentals](#s3-fundamentals)
3. [Core Concepts](#core-concepts)
4. [Data Transfer Methods](#data-transfer-methods)
5. [Working with Objects](#working-with-objects)
6. [Security & Access](#security--access)
7. [Advanced Topics](#advanced-topics)
8. [Common Patterns & Solutions](#common-patterns--solutions)
9. [File Guide](#file-guide)

---

## Quick Start

### What is Amazon S3?

**Amazon S3 (Simple Storage Service)** is AWS's object storage service. Think of it as:

```
Your Computer's Hard Drive
├── Folders (Buckets in S3)
│   ├── File1 (Object)
│   ├── File2 (Object)
│   └── Subfolder (Prefix/Path)
│       └── File3 (Object)

Key Difference:
├── Hard Drive: Block-based (sectors, tracks)
└── S3: Object-based (entire files, no blocks)
```

### Core Storage Model

```
S3 Container
│
└─ Bucket (logical container)
   ├─ Object 1 (file + metadata)
   ├─ Object 2 (file + metadata)
   └─ Prefix/Folder/
      └─ Object 3 (file + metadata)

Important: Buckets are FLAT! "Folders" don't really exist.
S3 uses prefixes (e.g., "folder/subfolder/") that look like folders.
```

### Accessing Objects

Each object has a unique **Object Key** (path):

```
Bucket: my-data-bucket
Object Key: reports/2024/january-sales.csv

Full URL:
https://my-data-bucket.s3.amazonaws.com/reports/2024/january-sales.csv
                        └─────────────────┬───────────────────┘
                                    Bucket + Object Key
```

### Why S3?

✅ **Unlimited scalability** - Store any amount of data (petabytes)
✅ **Cost-effective** - Pay only for what you use (~$0.023/GB/month)
✅ **Durable** - 99.999999999% (11 nines) object durability
✅ **Available** - 99.99% uptime SLA
✅ **Integrates everywhere** - Lambda, EC2, Analytics, ML services
✅ **Strong consistency** - Read-after-write consistency (no eventual consistency)

---

## S3 Fundamentals

### Core Components

#### 1. Buckets

A bucket is a top-level container for objects:

| Aspect | Detail |
|--------|--------|
| **Naming** | Global (must be unique across all AWS accounts) |
| **Structure** | Flat (no nested folders, only prefixes) |
| **Per Account** | Unlimited buckets per account |
| **Access Control** | Individual per bucket |
| **Region** | Assigned at creation, cannot change |
| **Versioning** | Optional, per bucket |
| **Encryption** | Can be enabled by default |

**Creating a bucket:**

```bash
aws s3 mb s3://my-unique-bucket-name --region us-east-1
```

#### 2. Objects

An object is a file with metadata:

| Component | Description |
|-----------|-------------|
| **Object Key** | Unique identifier (path: `folder/subfolder/filename.txt`) |
| **Data** | File content (0 bytes to 5 TB) |
| **Metadata** | Headers (content type, cache control, custom metadata) |
| **Version ID** | Optional (if versioning enabled) |
| **ETag** | Hash of object content (for integrity checking) |
| **Storage Class** | STANDARD, INTELLIGENT_TIERING, GLACIER, etc. |
| **Encryption** | Server-side or client-side |

**Storing an object:**

```python
import boto3

s3 = boto3.client('s3')

# Upload a file
s3.put_object(
    Bucket='my-bucket',
    Key='documents/report.pdf',
    Body=open('report.pdf', 'rb'),
    ContentType='application/pdf'
)
```

#### 3. Prefixes (Virtual Folders)

S3 has no real folders - they're just prefixes:

```
Bucket: documents
├─ 2024/jan/report.pdf          ← Prefix: "2024/jan/"
├─ 2024/feb/report.pdf          ← Prefix: "2024/feb/"
├─ 2023/archive/old-report.pdf  ← Prefix: "2023/archive/"
└─ readme.txt                    ← No prefix (root level)
```

This is just text before the filename. S3 doesn't create actual folders!

---

## Core Concepts

### AWS Regions & Availability Zones

Understanding where your data lives:

```
AWS Region (Geographic location)
├─ Multiple Availability Zones (Independent data centers)
│  ├─ AZ1 (Physical data center)
│  ├─ AZ2 (Physical data center)
│  └─ AZ3 (Physical data center)

Example:
us-east-1 (N. Virginia) - 6 AZs
├─ us-east-1a
├─ us-east-1b
├─ us-east-1c
├─ us-east-1d
├─ us-east-1e
└─ us-east-1f
```

**Key points:**
- Buckets are created in a specific region
- Data stays in that region (for compliance/latency)
- Accessing cross-region adds latency and potential costs
- Replication can copy data to other regions

### S3 Consistency Guarantees

**Strong Read-After-Write Consistency** (as of 2020):

```
Timeline:
10:00:00 - Write object "document.pdf"
10:00:01 - Read object "document.pdf" → ✅ Get latest version immediately
```

This applies to:
- PUT (upload new object)
- PUT (overwrite existing object)
- DELETE (remove object)
- LIST operations

---

## Data Transfer Methods

### Method Comparison

| Method | Best For | Speed | Complexity | Cost |
|--------|----------|-------|------------|------|
| **aws s3 cp** | Single files, simple copies | Moderate | ⭐ Easy | Low |
| **aws s3 sync** | Sync folders, incremental | Moderate | ⭐ Easy | Low |
| **aws s3api** | Fine-grained control | Variable | ⭐⭐⭐ Complex | Low |
| **s3-dist-cp** | Multi-TB on EMR | ⭐⭐⭐ Fast | ⭐⭐ Medium | Medium |
| **DataSync** | Managed transfers | Moderate | ⭐ Easy | Medium |
| **AWS CLI (parallel)** | Medium datasets | Good | ⭐ Easy | Low |

### Quick Examples

**1. Copy single file to S3:**

```bash
aws s3 cp local-file.txt s3://my-bucket/path/
```

**2. Sync entire directory (only new/changed files):**

```bash
aws s3 sync ./local-folder s3://my-bucket/folder/
```

**3. Copy between S3 buckets:**

```bash
aws s3 sync s3://source-bucket/ s3://dest-bucket/
```

**4. For large files (3TB+), optimize:**

```bash
# Configure parallel transfers
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB

# Then run sync
aws s3 sync s3://source-bucket/ s3://dest-bucket/
```

**→ See `how-to-copy-using-s3.md` for detailed comparison**
**→ See `copy-large-file-between-s3-buckets.md` for large dataset strategies**

### DataSync: Smart Transfer for Existing Data

**AWS DataSync** is a managed service for transferring data between S3 buckets. It's especially useful when source or destination already has data.

#### When DataSync is Perfect

✅ **One-time migrations** - Move data from old bucket to new bucket
✅ **Incremental syncs** - Update only changed/new files
✅ **Existing data handling** - Works intelligently with data already present
✅ **Scheduled transfers** - Automate daily/weekly syncs
✅ **Verification needed** - Automatic checksums and integrity checking

#### DataSync with Existing Buckets/Prefixes

When both source and destination already have data, DataSync intelligently handles different scenarios:

**Scenario 1: Update Old Versions**
- Use: `OverwriteMode: ALWAYS`
- Result: New versions overwrite old ones, new files added
- Example: Migrating v1 data to v2

**Scenario 2: Keep Extra Destination Files**
- Use: `OverwriteMode: ALWAYS` + `PreserveDeletedFiles: true`
- Result: Updates matches, keeps destination extras
- Example: Incremental backups

**Scenario 3: Only Add New Files (Never Overwrite)**
- Use: `OverwriteMode: SKIP`
- Result: Copies new files, skips existing ones
- Example: Safe incremental sync

**Scenario 4: Exact Mirror (Delete Extras)**
- Use: `OverwriteMode: ALWAYS` + `PreserveDeletedFiles: false`
- Result: Destination becomes exact copy, deletes extras
- Example: Perfect synchronization

#### Quick Setup

```bash
# Create source location
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::source-bucket \
  --subdirectory /data/

# Create destination location
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::dest-bucket \
  --subdirectory /data/

# Create task with options
aws datasync create-task \
  --source-location-arn <SOURCE_ARN> \
  --destination-location-arn <DEST_ARN> \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=ALWAYS,\
    PreserveDeletedFiles=false

# Run the transfer
aws datasync start-task-execution --task-arn <TASK_ARN>
```

#### Key Benefits

✅ Automatic comparison (only transfers what's different)
✅ Built-in verification (checksums confirmed)
✅ Flexible overwrite modes (ALWAYS or SKIP)
✅ Preserve or delete destination extras (your choice)
✅ Can be scheduled for recurring syncs

**→ See `copy-large-file-between-s3-buckets.md` for complete DataSync guide with all scenarios**

---

## Working with Objects

### Reading Objects

**Option 1: Download entire file**

```python
import boto3

s3 = boto3.client('s3')

s3.download_file(
    Bucket='my-bucket',
    Key='documents/report.pdf',
    Filename='downloaded-report.pdf'
)
```

**Option 2: Get object metadata (without downloading)**

```python
response = s3.head_object(Bucket='my-bucket', Key='documents/report.pdf')

print(f"File size: {response['ContentLength']} bytes")
print(f"Last modified: {response['LastModified']}")
print(f"ETag: {response['ETag']}")  # Hash of content
```

**Option 3: Read object content directly**

```python
response = s3.get_object(Bucket='my-bucket', Key='data.json')
content = response['Body'].read()  # File content as bytes
```

### Understanding ETags

**ETag** is a hash of object content used for integrity checking:

**For simple uploads (not multipart):**
```
ETag = MD5 hash of file
Example: "5d41402abc4b2a76b9719d911017c592"
```

**For multipart uploads:**
```
ETag = MD5 of parts + "-number of parts"
Example: "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"
          └─────────────────────────────┘  └─ 5 parts
          MD5 of concatenated part ETags
```

**Check if upload succeeded:**

```python
import hashlib

def verify_upload(bucket, key, local_file):
    """Verify file was uploaded correctly"""
    s3 = boto3.client('s3')

    # Get S3 object ETag
    s3_etag = s3.head_object(Bucket=bucket, Key=key)['ETag'].strip('"')

    # Calculate local file MD5
    md5_hash = hashlib.md5()
    with open(local_file, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)

    local_etag = md5_hash.hexdigest()

    if s3_etag == local_etag:
        print("✓ Upload verified!")
    else:
        print("✗ Upload mismatch - retried!")

# Usage
verify_upload('my-bucket', 'documents/report.pdf', 'report.pdf')
```

**→ See `read_etag_of_s3object.py` for complete implementation**

### Querying Data in S3

**S3 Select** - Run SQL queries directly on S3 objects without downloading:

```python
import boto3
import json

s3 = boto3.client('s3')

# Query JSON file in S3
response = s3.select_object_content(
    Bucket='my-bucket',
    Key='data.json',
    ExpressionType='SQL',
    Expression="SELECT * FROM S3Object[*] s WHERE s.event_id = 'xcdeere'",
    InputSerialization={'JSON': {'Type': 'Document'}},
    OutputSerialization={'JSON': {}}
)

# Read results
for event in response['Payload']:
    if 'Records' in event:
        print(event['Records']['Payload'].decode('utf-8'))
```

**Supported formats:**
- JSON
- CSV
- Parquet

**Benefits:**
✅ Query without downloading entire file
✅ Filter data in S3
✅ Lower bandwidth costs
✅ Faster queries on large files

**→ See `s3-select-parse-json.md` for detailed examples**

---

## Security & Access

### Presigned URLs

**Presigned URL** = Temporary URL that grants access without AWS credentials

**Use case:** Allow users to upload/download without AWS account

```python
import boto3

s3 = boto3.client('s3')

# Generate URL for downloading (valid 1 hour)
download_url = s3.generate_presigned_url(
    'get_object',
    Params={'Bucket': 'my-bucket', 'Key': 'public-file.pdf'},
    ExpiresIn=3600  # 1 hour
)

print(f"Share this URL: {download_url}")

# Generate URL for uploading (valid 30 minutes)
upload_url = s3.generate_presigned_url(
    'put_object',
    Params={'Bucket': 'my-bucket', 'Key': 'uploads/user-file.txt'},
    ExpiresIn=1800  # 30 minutes
)

print(f"Users can upload here: {upload_url}")
```

**Key security points:**
- URL is signed with your AWS credentials
- Expires after specified time
- Can't extend expiration once created
- Maximum expiration: 7 days
- Works with any HTTP client (curl, browser, JavaScript)

**→ See `presigned_url.md` for advanced examples and CloudFormation integration**

### Access Control Methods

| Method | Scope | Use Case |
|--------|-------|----------|
| **Bucket Policies** | Entire bucket | Public access, cross-account access |
| **IAM Policies** | Users/Roles | Control who can do what |
| **ACLs** | Individual objects | Legacy, not recommended |
| **Presigned URLs** | Temporary | Public sharing, one-time access |
| **VPC Endpoints** | Private access | Access without internet |

**Example: Make bucket public (NOT RECOMMENDED for sensitive data):**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::my-bucket/*"
    }
  ]
}
```

---

## Advanced Topics

### S3 with Hadoop/Big Data

**Three file systems for Hadoop to access S3:**

| Scheme | Name | Status | Best For |
|--------|------|--------|----------|
| **s3://** | S3 Block FileSystem | ⚠️ Deprecated | Don't use |
| **s3n://** | S3 Native FileSystem | ⚠️ Legacy | Old EMR clusters |
| **s3a://** | S3A (Advanced) | ✅ Recommended | All new work |

**Why s3a?**
- ✅ Supports files up to 5 TB (vs 5 GB for s3n)
- ✅ Multipart upload support
- ✅ Better performance
- ✅ More features (encryption, consistency)
- ✅ Works with EMR, Spark, Hadoop

**Example with PySpark:**

```python
# PySpark automatically uses s3a://
df = spark.read.parquet('s3a://my-bucket/data/*.parquet')

# Or explicitly
df = spark.read.option('compression', 'snappy') \
    .parquet('s3a://my-bucket/parquet-data/')
```

### Storage Classes

Choose the right storage class for your access patterns:

| Class | Retrieval | Price | Use Case |
|-------|-----------|-------|----------|
| **STANDARD** | Immediate | Highest | Hot data, frequent access |
| **STANDARD_IA** | Immediate | Lower | Infrequent access (30-day minimum) |
| **INTELLIGENT_TIERING** | Immediate | Medium | Unknown access patterns |
| **GLACIER** | Hours | Low | Archives, rare access |
| **DEEP_ARCHIVE** | 12+ hours | Lowest | Long-term retention |

**Cost example (1 GB/month):**
```
STANDARD: $0.023
STANDARD_IA: $0.0125 + retrieval costs
GLACIER: $0.004 + $0.05 per retrieval
DEEP_ARCHIVE: $0.00099 + $0.10 per retrieval
```

**Set storage class on upload:**

```python
s3.put_object(
    Bucket='my-bucket',
    Key='archive/old-data.zip',
    Body=file_content,
    StorageClass='GLACIER'  # Archive this
)
```

### Strong Consistency (2020 Update)

✅ **All S3 operations are now strongly consistent:**

```
Old (pre-2020):
├─ PUT/DELETE: 3-6 seconds to read new version
└─ LIST: Eventually consistent (stale results possible)

Current (2020+):
├─ PUT/DELETE: Immediate read after write ✓
├─ LIST: Immediate reflection of changes ✓
└─ Overwrite: Immediate read latest ✓
```

This means:
- No eventual consistency issues
- No retry loops for "object not found"
- Simpler application code
- Perfect for real-time applications

---

## Common Patterns & Solutions

### Pattern 0: Smart Transfer with Existing Data (DataSync)

**Problem:** Both source and destination buckets already have data. How do you sync without losing data or overwriting important files?

**Solution:** Use AWS DataSync with the right options for your scenario.

| Your Need | OverwriteMode | PreserveDeletedFiles | Use Case |
|-----------|---|---|---|
| Update old versions | `ALWAYS` | `false` | Migrate v1→v2 data |
| Add new files only | `SKIP` | `true` | Safe incremental backup |
| Update + keep extras | `ALWAYS` | `true` | Incremental sync with safety |
| Perfect mirror | `ALWAYS` | `false` | Replicate destination exactly |

**Example: Update existing files but keep destination extras**

```bash
aws datasync create-task \
  --source-location-arn <SOURCE> \
  --destination-location-arn <DEST> \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=ALWAYS,\
    PreserveDeletedFiles=true
```

**Key insight:** DataSync is smart - it:
1. Lists files in both source and destination
2. Compares timestamps/sizes
3. Only transfers what's different
4. Verifies all transfers
5. Can optionally delete destination extras

**→ See `copy-large-file-between-s3-buckets.md` for detailed scenarios with examples**

---

### Pattern 1: Cross-Region Copy (with VPC Endpoints)

**Problem:** VPC endpoints don't support cross-region requests

**Solution:** Use regional endpoints explicitly

```bash
# Copy between regions
aws s3 sync s3://source-bucket/ s3://dest-bucket/ \
  --source-region us-east-2 \
  --region us-east-1
```

Or two-step process:

```bash
# Step 1: S3 to local
aws s3 sync s3://source-bucket/ /tmp/data/ \
  --endpoint-url https://s3.us-east-2.amazonaws.com

# Step 2: Local to destination region
aws s3 sync /tmp/data/ s3://dest-bucket/
```

**→ See `vpc-endpoint-notsupport-cross-regions-request.md` for 6 solutions**

### Pattern 2: Large File Upload

**For files > 100 MB, use multipart upload:**

```python
def multipart_upload(bucket, key, file_path, part_size=5*1024*1024):
    """Upload large file in parts"""
    s3 = boto3.client('s3')

    # Initiate multipart upload
    response = s3.create_multipart_upload(Bucket=bucket, Key=key)
    upload_id = response['UploadId']

    parts = []
    with open(file_path, 'rb') as f:
        part_number = 1
        while True:
            chunk = f.read(part_size)
            if not chunk:
                break

            # Upload each part
            part_response = s3.upload_part(
                Bucket=bucket,
                Key=key,
                PartNumber=part_number,
                UploadId=upload_id,
                Body=chunk
            )

            parts.append({
                'PartNumber': part_number,
                'ETag': part_response['ETag']
            })
            part_number += 1
            print(f"Uploaded part {part_number-1}")

    # Complete multipart upload
    s3.complete_multipart_upload(
        Bucket=bucket,
        Key=key,
        UploadId=upload_id,
        MultipartUpload={'Parts': parts}
    )
    print(f"✓ Upload complete: s3://{bucket}/{key}")

# Usage
multipart_upload('my-bucket', 'large-file.zip', '/path/to/large-file.zip')
```

### Pattern 3: Retry Failed Uploads

```python
import time
from botocore.exceptions import ClientError

def upload_with_retry(bucket, key, file_path, max_retries=3):
    """Upload with automatic retry"""
    s3 = boto3.client('s3')

    for attempt in range(max_retries):
        try:
            s3.upload_file(file_path, bucket, key)
            print(f"✓ Upload successful")
            return True

        except ClientError as e:
            error_code = e.response['Error']['Code']

            if error_code == 'NoSuchBucket':
                print(f"✗ Bucket doesn't exist")
                return False
            elif error_code == 'AccessDenied':
                print(f"✗ Permission denied")
                return False
            else:
                # Temporary error - retry
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retry {attempt+1}/{max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"✗ Failed after {max_retries} retries")
                    return False
```

---

## File Guide

This folder contains specialized guides for different S3 use cases:

| File | Topic | Best For |
|------|-------|----------|
| **how-to-copy-using-s3.md** | Copy methods (cp, sync, s3api, s3-dist-cp) | Choosing the right copy tool |
| **copy-large-file-between-s3-buckets.md** | Large dataset transfers, DataSync scenarios | AWS DataSync with existing buckets, EMR, CLI optimization |
| **presigned_url.md** | Temporary access URLs | Sharing files, CloudFormation integration |
| **read_etag_of_s3object.py** | Verify uploads | Upload integrity checking |
| **s3-select-parse-json.md** | Query objects with SQL | Filtering without download |
| **vpc-endpoint-notsupport-cross-regions-request.md** | Cross-region VPC issues | Troubleshooting regional access |

---

## Learning Path

### For Beginners (1-2 weeks)

1. **Week 1:**
   - Understand buckets, objects, prefixes
   - Create a bucket, upload files (AWS Console)
   - Practice with `aws s3 cp` and `aws s3 sync`

2. **Week 2:**
   - Learn IAM policies for S3
   - Generate presigned URLs
   - Practice with Python boto3

### For Intermediate Developers (2-3 weeks)

1. **Week 1:**
   - Master `aws s3api` for fine-grained control
   - Understand multipart uploads
   - Learn S3 storage classes

2. **Week 2:**
   - Implement retry logic
   - Practice with large files
   - Explore S3 Select queries

3. **Week 3:**
   - Learn bucket policies and ACLs
   - Understand versioning
   - Practice encryption options

### For Advanced Users

- Big data integrations (s3a with Spark, Hadoop)
- Cross-region replication
- Performance optimization
- Cost analysis

---

## Key Takeaways

✅ **S3 is object-based, not block-based** - Upload entire files, not sectors
✅ **Buckets are flat** - "Folders" are just prefixes
✅ **Strong consistency** - Read immediately after write
✅ **Scale infinitely** - No performance degradation with size
✅ **Integrated everywhere** - Works with Lambda, EC2, Analytics
✅ **Presigned URLs** - Secure temporary access without credentials
✅ **Choose storage class** - Save money with tiering
✅ **Verify uploads** - Use ETags for integrity checks

---

## References

- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [S3 API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/Welcome.html)
- [Boto3 S3 Guide](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [S3 Pricing Calculator](https://aws.amazon.com/s3/pricing/)

---

**Last Updated:** 2024
**Format:** Comprehensive tutorial for all AWS skill levels
