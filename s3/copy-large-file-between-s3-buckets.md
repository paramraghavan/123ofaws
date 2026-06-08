# Copying Large Datasets Between S3 Buckets - Complete Guide

> **Master data transfer strategies for 3TB, 30TB, or 300TB between S3 buckets**

---

## Quick Overview

Copying large datasets (100 GB+) between S3 buckets requires choosing the right tool. This guide covers all options from simplest to fastest.

```
Dataset Size                    Recommended Tool
─────────────────────────────────────────────────────────────
< 100 GB                        aws s3 sync (simplest)
100 GB - 1 TB                   aws s3 sync + optimization
1 TB - 10 TB                    AWS DataSync (managed)
10 TB+                          S3DistCp on EMR (fastest)
One-time migration              AWS DataSync (easiest)
Recurring copies                S3DistCp or cron job
```

---

## Prerequisites

Before you start, you need:

### 1. AWS Credentials & Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::source-bucket",
        "arn:aws:s3:::source-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": [
        "arn:aws:s3:::dest-bucket",
        "arn:aws:s3:::dest-bucket/*"
      ]
    }
  ]
}
```

### 2. Verify Bucket Access

```bash
# Test source bucket read access
aws s3 ls s3://source-bucket/ --recursive | head -5

# Test destination bucket write access
aws s3 cp /tmp/test.txt s3://dest-bucket/test.txt
```

### 3. Check Bucket Regions

```bash
# Check source bucket region
aws s3api get-bucket-location --bucket source-bucket
# Output: { "LocationConstraint": "us-east-2" }

# Check destination bucket region
aws s3api get-bucket-location --bucket dest-bucket
# Output: { "LocationConstraint": "us-east-1" }
```

---

## Decision Tree: Which Method to Use?

```
START: Copy large dataset between S3 buckets
│
├─ Is this a one-time migration?
│  ├─ YES → Use AWS DataSync (managed, easy)
│  └─ NO → Continue...
│
├─ How much data?
│  ├─ < 100 GB → Use aws s3 sync (simplest)
│  ├─ 100 GB - 10 TB → Use aws s3 sync + optimization
│  │                    OR AWS DataSync (slower but managed)
│  └─ > 10 TB → Use S3DistCp on EMR (fastest)
│
├─ Need data transformation during copy?
│  ├─ YES → Use S3DistCp (compression, filtering, aggregation)
│  └─ NO → See above
│
├─ Already have EMR cluster running?
│  ├─ YES → Use S3DistCp (no extra cost)
│  └─ NO → Weigh cost vs. time
│
└─ End: Choose tool and implement
```

---

## Method 1: AWS CLI s3 sync (Simplest)

### When to Use

✅ **Best for:**
- 100 GB - 1 TB datasets
- Developers who want simplicity
- One-time or periodic syncs
- Testing before big transfers

❌ **Not ideal for:**
- Very large datasets (10 TB+) - too slow
- Frequent large transfers
- Complex filtering needs

### Basic Usage

```bash
# Simple sync (copies only new/changed files)
aws s3 sync s3://source-bucket/data/ s3://dest-bucket/data/
```

**What this does:**
```
Comparison Phase:
├─ S3 lists all files in source: /data/file1.parquet, /data/file2.parquet, ...
├─ S3 lists all files in dest: /data/file1.parquet, /data/file2.parquet, ...
└─ Identifies differences

Transfer Phase:
├─ Copy /data/file3.parquet (new in source)
├─ Copy /data/file5.parquet (updated in source)
└─ Skip /data/file1.parquet (already in dest)
```

### Optimized Configuration

For better performance, optimize parallelization and multipart settings:

```bash
# Step 1: Configure for parallel transfers (only for this session)
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 16MB

# Step 2: Test with a small subset first (dry run)
aws s3 sync s3://source-bucket/data/year=2024/month=01/ \
  s3://dest-bucket/data/year=2024/month=01/ \
  --dryrun

# Step 3: If dry run looks good, remove --dryrun
aws s3 sync s3://source-bucket/data/year=2024/month=01/ \
  s3://dest-bucket/data/year=2024/month=01/
```

### Advanced Examples

**Example 1: Filter by file type**

```bash
aws s3 sync s3://source-bucket/data/ s3://dest-bucket/data/ \
  --include "*.parquet" \
  --exclude "*" \
  --storage-class STANDARD_IA
```

**Example 2: Exclude certain patterns**

```bash
aws s3 sync s3://source-bucket/data/ s3://dest-bucket/data/ \
  --exclude "*.tmp" \
  --exclude "*.log" \
  --exclude ".git/*"
```

**Example 3: Copy with specific storage class**

```bash
# Store in cheaper tier
aws s3 sync s3://source-bucket/data/ s3://dest-bucket/data/ \
  --storage-class INTELLIGENT_TIERING
```

**Example 4: Set ACLs and metadata**

```bash
aws s3 sync s3://source-bucket/data/ s3://dest-bucket/data/ \
  --acl public-read \
  --metadata "archive=true,date=2024-01-15"
```

### Performance Tuning

**Estimated times for 1 TB dataset:**
- Default config: 8-12 hours
- With optimization: 3-5 hours

**What affects speed:**
- Network bandwidth (bottleneck for large files)
- Number of files (many small files = slower)
- Concurrent requests (20 is good for most cases)
- Multipart threshold (64 MB is good for most files)

---

## Method 2: AWS DataSync (Managed)

### What is AWS DataSync?

**AWS DataSync** is a managed service that **automatically copies data** between AWS storage services. Think of it as:

```
Your Manual Work:
├─ Write S3 sync script
├─ Configure parallelization
├─ Monitor progress
├─ Handle failures
├─ Verify integrity
└─ Wait 8+ hours

AWS DataSync (Managed):
├─ Point & click setup
├─ Automatic optimization
├─ Built-in monitoring
├─ Auto-retry on failure
├─ Built-in verification
└─ Done! (Usually faster)
```

**Key concept:** DataSync handles the heavy lifting so you don't have to write and manage scripts.

### How DataSync Works (Architecture)

```
┌─────────────────────────────────────────────────────┐
│ YOUR SETUP                                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│ Source S3 Bucket              Destination S3 Bucket │
│ ├─ file1.parquet              ├─ file1.parquet     │
│ ├─ file2.parquet              ├─ file2.parquet     │
│ └─ file3.parquet (NEW)        └─ (NEW file3)       │
│        ▲                              ▲             │
│        │                              │             │
│        └──────────┬───────────────────┘             │
│                   │                                 │
│          ┌────────▼────────┐                        │
│          │ AWS DataSync    │                        │
│          │                 │                        │
│          │ • Lists files   │                        │
│          │ • Compares      │                        │
│          │ • Transfers     │                        │
│          │ • Verifies      │                        │
│          │ • Retries       │                        │
│          └────────┬────────┘                        │
│                   │                                 │
│          AWS-Managed Service                        │
│          (You don't manage servers)                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### When to Use

✅ **Best for:**
- **One-time data migrations** (move data from old to new bucket)
- **Scheduled recurring transfers** (daily/weekly syncs)
- **Users who prefer managed services** (no script management)
- **Need built-in verification** (checksums automatically checked)
- **Complex transfer rules** (filtering, transformation)
- **Production systems** (enterprise support available)

❌ **Not ideal for:**
- **Super cheap copies** (if you have EMR running, S3DistCp is cheaper)
- **Speed-critical** (usually slower than S3DistCp for very large datasets)
- **One-off small files** (overkill for < 10 GB)
- **Immediate transfer needed** (takes time to set up)

### Real-World Scenarios

**Scenario 1: One-time migration**
```
Company restructuring:
├─ Old bucket: legacy-data-prod (3 TB)
├─ New bucket: analytics-2024 (empty)
├─ Action: Migrate everything
├─ Frequency: Once
├─ Best tool: DataSync (setup once, run once)
└─ Time: ~2 hours + setup
```

**Scenario 2: Scheduled daily sync**
```
Log aggregation:
├─ Source: application-logs-us-east-1
├─ Dest: analytics-us-west-2
├─ Action: Copy daily logs
├─ Frequency: Every 23:00 UTC
├─ Best tool: DataSync (schedule it once)
└─ Automation: Built-in scheduling
```

**Scenario 3: Recurring backup**
```
Disaster recovery:
├─ Source: production-data
├─ Dest: disaster-recovery-backup
├─ Action: Backup every week
├─ Frequency: Every Sunday 02:00
├─ Best tool: DataSync (handles scheduling)
└─ Verification: Automatic checksums
```

### Cost Comparison (Detailed)

```
Scenario: Copy 1 TB of data

OPTION 1: AWS CLI s3 sync
├─ EC2 instance (t3.large): 12 hours × $0.0832/hr = $0.99
├─ Data transfer (1 TB): 1000 GB × $0.02 = $20
├─ Your time: 2 hours @ $50/hr = $100 (opportunity cost)
└─ TOTAL: ~$121 (+ your time)

OPTION 2: AWS DataSync
├─ DataSync pricing: 1 TB × $0.0125 = $12.50
├─ S3 storage (source+dest): ~$0.046
├─ Data transfer: Included in DataSync price
├─ Your time: 15 minutes (one-time setup)
└─ TOTAL: ~$13 (includes everything)

OPTION 3: S3DistCp on EMR
├─ EMR cluster (8 nodes × 4 hours): ~$4
├─ EMR job: ~$1
├─ Data transfer: ~$20
├─ Your time: 3 hours = $150
└─ TOTAL: ~$175 (setup + monitoring)

WINNER FOR THIS SCENARIO: AWS DataSync!
```

### Cost Comparison (Matrix)

| Transfer Size | aws s3 sync | DataSync | S3DistCp |
|---|---|---|---|
| 100 GB | $2 | $1.25 | N/A (overkill) |
| 1 TB | $20 | $12.50 | $25 |
| 10 TB | $200 | $125 | $250 |
| 100 TB | $2,000 | $1,250 | $2,500 |

**Note:** DataSync is consistently cheaper for large transfers!

### Setup Steps (Two Approaches)

#### Approach 1: AWS Console (Recommended for Beginners)

**Most developers prefer the console - it's visual and easier.**

**Step 1: Create Source Location**

```
1. Go to AWS DataSync Console
2. Left menu: Click "Locations"
3. Click "Create location"
4. Choose "Amazon S3"
5. Fill in:
   ├─ Bucket name: source-bucket
   ├─ Folder: /data/
   ├─ Storage class: STANDARD
   └─ IAM role: DataSyncRole (auto-created)
6. Click "Create location"
```

**What you'll see:**
```
✓ Location created: source-bucket
  └─ ARN: arn:aws:datasync:us-east-1:123456789012:location/s3/abc123
```

**Step 2: Create Destination Location**

```
1. Repeat Step 1 but with destination details:
   ├─ Bucket name: dest-bucket
   ├─ Folder: /data/
   ├─ Storage class: STANDARD_IA (cheaper tier)
   └─ IAM role: DataSyncRole (same role)
2. Click "Create location"
```

**Step 3: Create Task**

```
1. Left menu: Click "Tasks"
2. Click "Create task"
3. Configure:
   ├─ Source location: source-bucket (from Step 1)
   ├─ Destination location: dest-bucket (from Step 2)
   └─ Default options (OK for most uses)
4. Click "Create"
```

**Step 4: Review Transfer Options**

Before running, review:
```
Verification Mode:     POINT_IN_TIME_CONSISTENT ✓
├─ Checks file integrity
├─ Compares file sizes & timestamps
└─ Recommended for data integrity

Overwrite Mode:        ALWAYS ✓
├─ Overwrites existing files
├─ Good for migrations
└─ Choose SKIP if you want to preserve old files

Preserve Deleted Files: NO
├─ Doesn't delete destination files
├─ Good for incremental syncs
└─ Good for safety (keep old backup)
```

**Step 5: Start Transfer**

```
1. Click on your task
2. Click "Start"
3. Confirm: "Start task execution"
4. Watch progress in real-time!
   ├─ Files copied: 1,234 / 5,678
   ├─ Data transferred: 234 GB / 1 TB
   ├─ Speed: 45 MB/s
   └─ Time remaining: ~3 hours
```

**Step 6: Monitor Progress**

```
While running:
├─ Files copied counter updates live
├─ Speed shows current MB/s
├─ Estimated time remaining
└─ Can view detailed logs

After completion:
├─ Status: SUCCESS ✓
├─ Files copied: 5,678
├─ Data transferred: 1 TB
├─ Verification: PASSED
└─ Duration: 2 hours 47 minutes
```

---

#### Approach 2: AWS CLI (Scripting & Automation)

**For automation, recurring syncs, or pipeline integration.**

**Step 1: Create source location**

```bash
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::source-bucket \
  --subdirectory /data/ \
  --s3-storage-class STANDARD \
  --region us-east-1

# Returns: "LocationArn": "arn:aws:datasync:us-east-1:123456789012:location/s3/..."
# Save this ARN!
```

**Step 2: Create destination location**

```bash
aws datasync create-location-s3 \
  --s3-bucket-arn arn:aws:s3:::dest-bucket \
  --subdirectory /data/ \
  --s3-storage-class STANDARD_IA \
  --region us-east-1

# Save destination ARN!
```

**Step 3: Create task**

```bash
aws datasync create-task \
  --source-location-arn arn:aws:datasync:us-east-1:123456789012:location/s3/source \
  --destination-location-arn arn:aws:datasync:us-east-1:123456789012:location/s3/dest \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=ALWAYS,\
    PreserveDeletedFiles=false \
  --region us-east-1

# Returns: "TaskArn": "arn:aws:datasync:us-east-1:123456789012:task/..."
# Save this Task ARN!
```

**Step 4: Start execution**

```bash
# Replace with your task ARN from Step 3
TASK_ARN="arn:aws:datasync:us-east-1:123456789012:task/task-abc123"

aws datasync start-task-execution \
  --task-arn $TASK_ARN \
  --region us-east-1

# Returns: "TaskExecutionArn": "arn:aws:datasync:us-east-1:123456789012:task-execution/..."
# This tracks THIS specific run
```

**Step 5: Monitor progress (polling)**

```bash
# Check current status every 30 seconds
EXECUTION_ARN="arn:aws:datasync:us-east-1:123456789012:task-execution/..."

while true; do
  aws datasync describe-task-execution \
    --task-execution-arn $EXECUTION_ARN \
    --region us-east-1 \
    --query 'TaskExecutionStatus' \
    --output text

  # If status is SUCCESS or FAILURE, exit loop
  # Otherwise wait and check again
  sleep 30
done
```

**Step 6: Get full results**

```bash
aws datasync describe-task-execution \
  --task-execution-arn $EXECUTION_ARN \
  --region us-east-1

# Shows:
# {
#   "Status": "SUCCESS",
#   "FilesTransferred": 5678,
#   "DataTransferred": 1099511627776,  # bytes (1 TB)
#   "StartTime": "2024-01-15T10:00:00Z",
#   "EndTime": "2024-01-15T12:47:30Z"
# }
```

---

### Common DataSync Options Explained

```
VerifyMode: POINT_IN_TIME_CONSISTENT (Recommended)
├─ Verifies every file was transferred correctly
├─ Checks file size, modification time, and checksum
├─ Takes extra time but ensures data integrity
└─ Best for: Important data migrations

VerifyMode: NONE
├─ Skips verification (faster)
├─ Assumes transfer was successful
└─ Best for: Repeated syncs where data is usually same

OverwriteMode: ALWAYS
├─ Overwrites files that already exist at destination
├─ Good for: Fresh migrations, replacing old data
└─ Example: Old version → New version

OverwriteMode: SKIP
├─ Never overwrites existing files
├─ Good for: Incremental backups
└─ Example: Keep destination, just add new files

PreserveDeletedFiles: true
├─ Keeps destination files that don't exist in source
├─ Good for: Backups (don't delete destination)
└─ Example: If file deleted from source, don't delete backup

PreserveDeletedFiles: false
├─ Deletes destination files not in source
├─ Good for: Exact replication
└─ Example: Make destination identical to source
```

---

### What If Source & Destination Buckets/Prefixes Already Exist?

This is a **common real-world scenario**. You have existing data in both places. DataSync handles this elegantly!

#### Scenario 1: Destination Already Has Old Data (Need to Update)

**Situation:**
```
Source Bucket:                  Destination Bucket:
├─ file1.parquet (v2)           ├─ file1.parquet (v1) ← OLD VERSION
├─ file2.parquet (v2)           ├─ file2.parquet (v1) ← OLD VERSION
├─ file3.parquet (NEW)          └─ (nothing)
└─ file4.csv (NEW)
```

**Solution: Use `OverwriteMode: ALWAYS`**

```bash
aws datasync create-task \
  --source-location-arn $SOURCE_ARN \
  --destination-location-arn $DEST_ARN \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=ALWAYS,\
    PreserveDeletedFiles=false \
  --region us-east-1
```

**Result:**
```
After DataSync runs:
├─ file1.parquet (v2) ✓ UPDATED from v1
├─ file2.parquet (v2) ✓ UPDATED from v1
├─ file3.parquet ✓ NEW
└─ file4.csv ✓ NEW
```

**How it works:**
1. DataSync lists all files in source
2. Compares with destination
3. For matching files: Compares timestamps/sizes
4. If different: Overwrites with source version
5. If new in source: Copies to destination
6. Verifies all transferred files

---

#### Scenario 2: Destination Has Extra Data (Incremental Update)

**Situation:**
```
Source Bucket:                  Destination Bucket:
├─ file1.parquet (v2)           ├─ file1.parquet (v1)
├─ file2.parquet                ├─ file2.parquet
└─ file3.parquet (NEW)          ├─ file4.parquet (from old backup)
                                └─ file5.parquet (from old backup)
```

**You want:** Keep the extra files in destination, just sync new/changed from source

**Solution: Use `OverwriteMode: ALWAYS` + `PreserveDeletedFiles: true`**

```bash
aws datasync create-task \
  --source-location-arn $SOURCE_ARN \
  --destination-location-arn $DEST_ARN \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=ALWAYS,\
    PreserveDeletedFiles=true \
  --region us-east-1
```

**Result:**
```
After DataSync runs:
├─ file1.parquet (v2) ✓ UPDATED
├─ file2.parquet ✓ VERIFIED
├─ file3.parquet ✓ COPIED (NEW)
├─ file4.parquet ✓ KEPT (preserved)
└─ file5.parquet ✓ KEPT (preserved)
```

---

#### Scenario 3: Destination Has Data You Don't Want to Overwrite

**Situation:**
```
Source Bucket (new data):       Destination Bucket (existing production):
├─ file1.parquet                ├─ file1.parquet (DO NOT OVERWRITE!)
├─ file2.parquet                ├─ file2.parquet (DO NOT OVERWRITE!)
└─ file3.parquet (NEW)          └─ (nothing)
```

**You want:** Only copy NEW files, skip existing ones

**Solution: Use `OverwriteMode: SKIP`**

```bash
aws datasync create-task \
  --source-location-arn $SOURCE_ARN \
  --destination-location-arn $DEST_ARN \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=SKIP,\
    PreserveDeletedFiles=true \
  --region us-east-1
```

**Result:**
```
After DataSync runs:
├─ file1.parquet ✓ SKIPPED (already exists)
├─ file2.parquet ✓ SKIPPED (already exists)
└─ file3.parquet ✓ COPIED (NEW)
```

---

#### Scenario 4: Mirror Source to Destination (Delete Extra Files)

**Situation:**
```
Source Bucket (truth):          Destination Bucket (replica):
├─ file1.parquet                ├─ file1.parquet
├─ file2.parquet                ├─ file2.parquet
├─ file3.parquet (NEW)          ├─ file4.parquet (OLD - should be deleted)
                                └─ file5.parquet (OLD - should be deleted)
```

**You want:** Destination = EXACT copy of source (delete what source doesn't have)

**Solution: Use `OverwriteMode: ALWAYS` + `PreserveDeletedFiles: false`**

```bash
aws datasync create-task \
  --source-location-arn $SOURCE_ARN \
  --destination-location-arn $DEST_ARN \
  --options \
    VerifyMode=POINT_IN_TIME_CONSISTENT,\
    OverwriteMode=ALWAYS,\
    PreserveDeletedFiles=false \
  --region us-east-1
```

**Result:**
```
After DataSync runs:
├─ file1.parquet ✓ UPDATED
├─ file2.parquet ✓ UPDATED
├─ file3.parquet ✓ COPIED (NEW)
├─ file4.parquet ✓ DELETED (not in source)
└─ file5.parquet ✓ DELETED (not in source)
```

⚠️ **WARNING**: `PreserveDeletedFiles=false` DELETES files from destination. Use with caution!

---

### Quick Decision Table: Existing Data Scenarios

| Scenario | OverwriteMode | PreserveDeletedFiles | Result |
|----------|---|---|---|
| **Update old versions** | `ALWAYS` | `false` | Overwrite old files + delete extra |
| **Add new files only** | `SKIP` | `true` | Keep destination, add new files |
| **Update + keep extra** | `ALWAYS` | `true` | Overwrite matches + keep destination extras |
| **Make exact copy** | `ALWAYS` | `false` | Destination = exact mirror of source |
| **Backup only new** | `SKIP` | `true` | Never overwrite, safe incremental |

---

### Common Questions About Existing Data

**Q: Will DataSync fail if destination exists?**
A: No! DataSync is designed to work with existing destinations. It will compare and sync intelligently based on your options.

**Q: Can I run DataSync multiple times on the same source/dest?**
A: Yes! Each run will:
   - Skip files that match
   - Update files that changed
   - Copy new files
   - Optionally delete removed files

**Q: What if a file exists in both but with different content?**
A: DataSync compares:
   1. File size
   2. Last modified timestamp
   3. If OverwriteMode=ALWAYS → Overwrites with source version
   4. If OverwriteMode=SKIP → Keeps destination version
   5. Verification mode confirms transfer was successful

**Q: Is it safe to run DataSync on production data?**
A: Yes, with precautions:
   - Always test on small dataset first
   - Use `OverwriteMode=SKIP` if unsure
   - Enable verification (`POINT_IN_TIME_CONSISTENT`)
   - Have backups before `PreserveDeletedFiles=false`

**Q: What about file permissions and metadata?**
A: DataSync preserves:
   - ✓ File size
   - ✓ Last modified date
   - ✓ ACLs (if source has them)
   - ✓ Object metadata/tags
   - ✓ Encryption settings (if using KMS)

---

### Advantages of DataSync

✅ **Automatic optimization** - DataSync figures out the best parallelization
✅ **Built-in verification** - Checksums are automatic
✅ **Scheduling** - Run transfers on a schedule (daily, weekly, etc.)
✅ **Monitoring** - Detailed metrics and logs
✅ **Retry logic** - Automatically retries failed files
✅ **Managed service** - AWS handles all the infrastructure
✅ **Cross-region** - Works across AWS regions seamlessly
✅ **Incremental** - Can update only changed files
✅ **Professional support** - Enterprise support available

### Disadvantages of DataSync

❌ **Setup time** - Takes 15-20 minutes to configure first time
❌ **Cost** - Not cheapest for small datasets
❌ **Speed** - Slower than S3DistCp for very large transfers
❌ **Learning curve** - Concepts like "locations" and "tasks" to understand

### Advantages

✅ Built-in verification (checksums)
✅ Can preserve file metadata
✅ Handles encryption
✅ Simple one-time setup
✅ Can schedule recurring transfers

---

## Method 3: S3DistCp on EMR (Fastest)

### When to Use

✅ **Best for:**
- Very large datasets (10 TB+)
- Need maximum speed
- Data transformation during transfer
- Already using EMR

❌ **Not ideal for:**
- One-time copies (setup takes time)
- Small datasets
- Users unfamiliar with EMR

### How S3DistCp Works

```
EMR Cluster
├─ Node 1: Copy chunk1 (parallel)
├─ Node 2: Copy chunk2 (parallel)
├─ Node 3: Copy chunk3 (parallel)
└─ Node 4: Copy chunk4 (parallel)

Result: 4x faster than single-threaded sync!
```

### Setup Steps

**Step 1: Create EMR cluster**

```bash
aws emr create-cluster \
  --name "S3 Copy Cluster" \
  --release-label emr-6.10.0 \
  --instances InstanceGroups='[
    {InstanceGroupType: MASTER, InstanceCount: 1, InstanceType: m5.xlarge},
    {InstanceGroupType: CORE, InstanceCount: 4, InstanceType: m5.xlarge}
  ]' \
  --log-uri s3://your-bucket/emr-logs/ \
  --service-role EMR_DefaultRole \
  --ec2-attributes InstanceProfile=EMR_EC2_DefaultRole
```

**Step 2: SSH into master node**

```bash
# Get master public DNS
aws emr describe-cluster --cluster-id j-xxxxx --query 'Cluster.MasterPublicDnsName'

# SSH to cluster
ssh -i /path/to/key.pem hadoop@master-dns
```

**Step 3: Run s3-dist-cp**

```bash
# Basic copy
s3-dist-cp \
  --src s3://source-bucket/data/ \
  --dest s3://dest-bucket/data/

# With optimization
s3-dist-cp \
  --src s3://source-bucket/data/ \
  --dest s3://dest-bucket/data/ \
  --srcPattern '.*\.parquet' \
  --targetSize 1024 \
  --outputCodec gzip \
  --groupBy '(.*)_(\d+)' \
  --groupBySize 1024
```

### Key Parameters

| Parameter | Example | Meaning |
|-----------|---------|---------|
| `--src` | `s3://bucket/data/` | Source location |
| `--dest` | `s3://bucket/data/` | Destination location |
| `--srcPattern` | `.*\.parquet` | Only copy matching files (regex) |
| `--targetSize` | `1024` | Target file size in MB after grouping |
| `--outputCodec` | `gzip` | Compression (gzip, lzo, snappy, none) |
| `--groupBy` | `(.*)` | Group files matching pattern |
| `--numMappers` | `10` | Number of parallel mappers |

### Performance

**Estimated times for different dataset sizes:**

```
Dataset      Cluster       Time
─────────────────────────────────────
100 GB       2x m5.xlarge  30 mins
1 TB         4x m5.xlarge  2 hours
10 TB        8x m5.xlarge  3-4 hours
100 TB       16x m5.xlarge 4-5 hours
```

### Cost Analysis

```
Copy 10 TB with S3DistCp:

Cluster cost:
├─ 8 m5.xlarge nodes
├─ Run time: 4 hours
├─ Hourly: 8 × $0.192 = $1.536/hr
└─ Total: $1.536 × 4 = $6.14

Data transfer:
├─ 10 TB out of S3: 10,000 GB × $0.02 = $200
└─ Total: $200.14

vs. AWS DataSync:
├─ 10 TB × $0.0125 = $125
└─ Total: $125

Verdict: DataSync is cheaper unless you already have EMR!
```

---

## Method 4: S3 Batch Operations

### When to Use

✅ **Best for:**
- Complex copy operations (with conditions)
- Applying transformations
- Managing metadata changes
- Large-scale operations

### Setup Steps

**Step 1: Create inventory of source bucket**

```bash
aws s3api put-bucket-inventory-configuration \
  --bucket source-bucket \
  --id daily-inventory \
  --inventory-configuration '{
    "Destination": {
      "S3BucketDestination": {
        "AccountId": "123456789012",
        "Bucket": "arn:aws:s3:::inventory-bucket",
        "Prefix": "inventory/",
        "Format": "CSV"
      }
    },
    "IsEnabled": true,
    "Filter": {"Prefix": "data/"},
    "Frequency": "Daily",
    "IncludedObjectVersions": "Current",
    "Id": "daily-inventory"
  }'
```

**Step 2: Create S3 Batch Operations job**

```bash
aws s3control create-job \
  --account-id 123456789012 \
  --operation LambdaInvoke \
  --manifest '{
    "Spec": {
      "Format": "S3BatchOperations_CSV_20180820"
    },
    "Location": {
      "ObjectArn": "arn:aws:s3:::inventory-bucket/inventory/manifest.json"
    }
  }' \
  --priority 10 \
  --user-arguments Key1=Value1
```

---

## Troubleshooting & Common Errors

### Error 1: Cross-Region Access Fails (HTTP 301)

**Error message:**
```
software.amazon.awssdk.services.s3.model: the bucket you are attempting
to access must be addressed using specified endpoint. Status code 301
```

**Cause:** Source and destination buckets are in different regions, and the tool is using wrong endpoint

**Solution 1: For aws s3 sync**

```bash
# Explicitly specify regions
aws s3 sync s3://source-bucket/ s3://dest-bucket/ \
  --source-region us-east-2 \
  --region us-east-1
```

**Solution 2: For S3DistCp**

```bash
# Set regional endpoint
s3-dist-cp \
  --src s3://source-bucket/ \
  --dest s3://dest-bucket/ \
  --s3Endpoint s3.us-east-2.amazonaws.com
```

**Solution 3: Verify regions first**

```bash
# Check source
aws s3api get-bucket-location --bucket source-bucket
# Output: us-east-2

# Check destination
aws s3api get-bucket-location --bucket dest-bucket
# Output: us-east-1
```

---

### Error 2: "Initialization of all collectors failed" (EMR)

**Cause:** EMR cluster doesn't have enough YARN resources

**Solution 1: Reduce parallelism**

```bash
# Use fewer mappers
s3-dist-cp \
  --src s3://source-bucket/data/ \
  --dest s3://dest-bucket/data/ \
  --numMappers 1
```

**Solution 2: Check available resources**

```bash
# SSH to EMR master, then run:
yarn node -list -all
yarn application -list

# View detailed logs
yarn logs -applicationId application_1234567890_0001
```

**Solution 3: Resize cluster**

```bash
aws emr add-instance-groups \
  --cluster-id j-xxxxx \
  --instance-groups 'InstanceGroupType=CORE,InstanceCount=4,InstanceType=m5.xlarge'
```

---

### Error 3: Permission Denied During Copy

**Error message:**
```
AccessDenied: Access Denied
```

**Cause:** IAM role doesn't have S3 permissions

**Solution: Add permissions to IAM role**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::source-bucket",
        "arn:aws:s3:::source-bucket/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:GetObject"
      ],
      "Resource": [
        "arn:aws:s3:::dest-bucket",
        "arn:aws:s3:::dest-bucket/*"
      ]
    }
  ]
}
```

---

### Error 4: Timeout During Large Transfer

**Cause:** Transfer takes too long, connection times out

**Solution 1: For aws s3 sync - increase timeout**

```bash
# Set custom timeout in AWS CLI config
aws configure set s3.max_bandwidth 100MB/s

# Then run sync
aws s3 sync s3://source-bucket/ s3://dest-bucket/
```

**Solution 2: For EMR - use longer timeouts**

```bash
s3-dist-cp \
  --src s3://source-bucket/data/ \
  --dest s3://dest-bucket/data/ \
  --taskTimeout 3600000 \
  --socketTimeout 300000
```

**Solution 3: Run in background with nohup**

```bash
# For aws s3 sync
nohup aws s3 sync s3://source-bucket/ s3://dest-bucket/ > sync.log 2>&1 &

# Check progress
tail -f sync.log
```

---

### Error 5: Bucket Not Found

**Error message:**
```
NoSuchBucket: The specified bucket does not exist
```

**Solution: Verify bucket names**

```bash
# List your buckets
aws s3 ls

# Check specific bucket exists
aws s3api head-bucket --bucket source-bucket
```

---

## Best Practices & Tips

### ✅ Do This

**1. Always test with a small subset first**

```bash
# Copy just one day's data to verify
aws s3 sync s3://source-bucket/data/2024-01-15/ \
  s3://dest-bucket/data/2024-01-15/ \
  --dryrun

# If dry run looks good:
aws s3 sync s3://source-bucket/data/2024-01-15/ \
  s3://dest-bucket/data/2024-01-15/
```

**2. Monitor bandwidth usage**

```bash
# While sync is running (in another terminal)
watch -n 1 'aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name NumberOfObjects \
  --dimensions Name=BucketName,Value=dest-bucket'
```

**3. Use storage classes to save money**

```bash
# Archive old data to cheaper tier
aws s3 sync s3://source-bucket/archive/ s3://dest-bucket/archive/ \
  --storage-class GLACIER
```

**4. Verify transfer integrity**

```bash
# Count files in source
aws s3 ls s3://source-bucket/data/ --recursive | wc -l

# Count files in destination
aws s3 ls s3://dest-bucket/data/ --recursive | wc -l

# Should be equal!
```

### ❌ Don't Do This

**1. Don't use --delete without verification**

```bash
# ❌ DANGEROUS: Deletes files in destination not in source
aws s3 sync s3://source-bucket/ s3://dest-bucket/ --delete

# ✅ SAFER: Copy without deleting
aws s3 sync s3://source-bucket/ s3://dest-bucket/
```

**2. Don't ignore dry-run**

```bash
# ❌ Wrong: Run without testing first
aws s3 sync s3://source-bucket/ s3://dest-bucket/

# ✅ Right: Always test first
aws s3 sync s3://source-bucket/ s3://dest-bucket/ --dryrun
```

**3. Don't copy without parallelization**

```bash
# ❌ Slow: Default settings
aws s3 sync s3://source-bucket/ s3://dest-bucket/

# ✅ Fast: Optimized settings
aws configure set default.s3.max_concurrent_requests 20
aws s3 sync s3://source-bucket/ s3://dest-bucket/
```

---

## Comparison Table

| Feature | aws s3 sync | DataSync | S3DistCp | S3 Batch |
|---------|------------|----------|----------|----------|
| **Setup complexity** | ⭐ Simple | ⭐⭐ Medium | ⭐⭐⭐ Complex | ⭐⭐⭐ Complex |
| **Speed** | ⭐⭐ Moderate | ⭐⭐ Moderate | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐ Good |
| **Cost** | $ Low | $$ Medium | $ Low* | $$$ High |
| **Data verification** | ❌ Manual | ✅ Built-in | ❌ Manual | ✅ Built-in |
| **Best for 1 TB** | ✅ Yes | ✅ Yes | ❌ Overkill | ❌ Overkill |
| **Best for 100 TB** | ❌ Slow | ❌ Slow | ✅ Perfect | ✅ Good |
| **Recurring copies** | ✅ Easy | ✅ Yes | ✅ Yes | ❌ No |

*Cost low if EMR already running

---

## Summary & Recommendations

### For Small Datasets (< 100 GB)
```
→ Use: aws s3 sync
→ Time: < 1 hour
→ Cost: < $10
```

### For Medium Datasets (100 GB - 10 TB)
```
→ Use: aws s3 sync + optimization OR AWS DataSync
→ Time: 2-8 hours
→ Cost: $5-50
```

### For Large Datasets (10 TB+)
```
→ Use: S3DistCp on EMR
→ Time: 2-5 hours
→ Cost: $5-200 (depending on cluster size)
```

### For One-Time Migrations
```
→ Use: AWS DataSync
→ Time: Varies
→ Cost: Fixed per GB
```

---

## Next Steps

1. **Identify your dataset size** - Determine if you have GB, TB, or PB of data
2. **Choose the right tool** - Use decision tree above
3. **Test with sample** - Always use --dryrun first
4. **Configure optimally** - Set parallel threads, multipart settings
5. **Monitor progress** - Watch logs and metrics
6. **Verify transfer** - Count files, check integrity
7. **Cleanup** - Delete source if needed

---

## See Also

- [aws s3 sync Documentation](https://docs.aws.amazon.com/cli/latest/reference/s3/sync.html)
- [AWS DataSync Documentation](https://docs.aws.amazon.com/datasync/)
- [S3DistCp Guide](https://docs.aws.amazon.com/emr/latest/ReleaseGuide/UsingEMRs3DistCp.html)
- [S3 Batch Operations](https://docs.aws.amazon.com/AmazonS3/latest/userguide/batch-ops.html)

