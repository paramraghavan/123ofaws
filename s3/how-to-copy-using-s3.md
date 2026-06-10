# S3 Copy Methods - Complete Tutorial

> **Master the right tool for each job**: Learn when to use cp vs sync vs s3api vs S3DistCp for different file transfer scenarios.

---

## Table of Contents

1. [The Mental Model](#the-mental-model-sticks-in-your-mind)
2. [Quick Decision Tree](#quick-decision-tree)
3. [Method 1: aws s3 cp (Copy Individual Files)](#method-1-aws-s3-cp-copy-individual-files)
4. [Method 2: aws s3 sync (Smart Synchronization)](#method-2-aws-s3-sync-smart-synchronization)
5. [Method 3: aws s3api (Fine-Grained Control)](#method-3-aws-s3api-fine-grained-control)
6. [Method 4: S3DistCp on EMR (Big Data)](#method-4-s3distcp-on-emr-big-data)
7. [Performance Comparison](#performance-comparison)
8. [Real-World Scenarios](#real-world-scenarios)

---

## The Mental Model (Sticks in Your Mind!)

Think of S3 copy tools like **different types of movers**:

```
Moving your data to S3:

aws s3 cp      = Single truck driver
                 ├─ Good for: Moving one box
                 ├─ Speed: Moderate
                 └─ Cost: Low

aws s3 sync    = Smart movers with checklist
                 ├─ Good for: Moving house (only pack what's changed)
                 ├─ Speed: Moderate
                 └─ Cost: Low

aws s3api      = Professional moving company
                 ├─ Good for: Complex moves (climate control, insurance)
                 ├─ Speed: Depends on setup
                 └─ Cost: Medium

S3DistCp       = Convoy of trucks (Big rig fleet)
                 ├─ Good for: Moving entire warehouses
                 ├─ Speed: FAST (parallel)
                 └─ Cost: EMR cluster cost
```

**Key concept**: Different tools for different scale:
- **Small** (1-10 GB) → `cp`
- **Medium** (10 GB - 1 TB) → `sync`
- **Large & Complex** (1-10 TB) → `s3api` or EMR
- **Massive** (10+ TB) → `S3DistCp`

---

## Quick Decision Tree

```
How much data to copy?

├─ Single file or small folder?
│  └─ Use: aws s3 cp
│     └─ $ aws s3 cp ./file.txt s3://bucket/

├─ Entire directory (first time)?
│  └─ Use: aws s3 cp --recursive
│     └─ $ aws s3 cp ./folder s3://bucket/folder/ --recursive

├─ Keep files in sync (incremental)?
│  └─ Use: aws s3 sync
│     └─ $ aws s3 sync ./folder s3://bucket/folder/

├─ Need multipart, encryption, metadata?
│  └─ Use: aws s3api
│     └─ $ aws s3api put-object --bucket bucket --key file.txt --body file.txt

├─ Transfer 10+ TB in Hadoop/EMR?
│  └─ Use: s3-dist-cp
│     └─ $ s3-dist-cp --src s3://src --dest s3://dest

└─ Size: 100 GB - 10 TB (not EMR)?
   └─ Use: aws s3 sync with parallel optimization
      └─ $ aws configure && aws s3 sync (optimized)
```

---

## Method 1: aws s3 cp (Copy Individual Files)

### When to Use
- ✅ Single file transfers
- ✅ Small directories (< 100 GB)
- ✅ Simple copy operations
- ✅ One-time transfers
- ❌ Large datasets (use sync instead)
- ❌ Incremental updates (use sync instead)

### Basic Usage

**Upload file to S3:**
```bash
aws s3 cp ./report.pdf s3://my-bucket/documents/
```

**Download from S3:**
```bash
aws s3 cp s3://my-bucket/report.pdf ./
```

**Copy between S3 buckets:**
```bash
aws s3 cp s3://source-bucket/file.txt s3://dest-bucket/
```

**Copy entire directory:**
```bash
aws s3 cp ./local-folder s3://my-bucket/folder/ --recursive
```

### Common Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--recursive` | Copy entire directory | `aws s3 cp ./folder s3://bucket/ --recursive` |
| `--exclude` | Skip files matching pattern | `aws s3 cp . s3://bucket/ --recursive --exclude "*.tmp"` |
| `--include` | Only copy matching files | `aws s3 cp . s3://bucket/ --recursive --exclude "*" --include "*.jpg"` |
| `--storage-class` | Set storage tier | `aws s3 cp file.txt s3://bucket/ --storage-class GLACIER` |
| `--sse` | Enable encryption | `aws s3 cp file.txt s3://bucket/ --sse AES256` |
| `--acl` | Set permissions | `aws s3 cp file.txt s3://bucket/ --acl public-read` |

### Real-World Example

```bash
# Upload a report with encryption and metadata
aws s3 cp quarterly-report.pdf s3://company-reports/2024-q1/ \
  --sse AES256 \
  --metadata "author=john,date=2024-01-01"

# Recursively copy only images
aws s3 cp ./photos s3://photo-bucket/ \
  --recursive \
  --exclude "*" \
  --include "*.jpg" \
  --include "*.png"
```

---

## Method 2: aws s3 sync (Smart Synchronization)

### When to Use
- ✅ Keep two locations synchronized
- ✅ Incremental backups
- ✅ Deployments (only changed files)
- ✅ Website uploads (development → production)
- ✅ Datasets (only new files)
- ❌ One-time large transfers (use cp)
- ❌ Deleting files (risky without `--delete`)

### How It Works

```
aws s3 sync compares:
├─ Source files (local or S3)
├─ Destination files (S3 or local)
└─ Copies ONLY files that:
   ├─ Don't exist in destination, OR
   ├─ Are newer in source, OR
   └─ Have different size/ETag

Result: Only transfers changed files!
Benefits: Fast, cheap, perfect for updates
```

### Basic Usage

**Local to S3 (backup):**
```bash
aws s3 sync ./my-folder s3://my-bucket/folder/
```

**S3 to Local (restore):**
```bash
aws s3 sync s3://my-bucket/folder/ ./my-folder
```

**S3 to S3 (mirror buckets):**
```bash
aws s3 sync s3://source-bucket/ s3://dest-bucket/
```

### Common Options

| Option | Purpose | Example |
|--------|---------|---------|
| `--delete` | Delete destination files not in source | `aws s3 sync ./folder s3://bucket/ --delete` |
| `--exclude` | Skip files | `aws s3 sync . s3://bucket/ --exclude "*.tmp"` |
| `--include` | Only sync matching | `aws s3 sync . s3://bucket/ --exclude "*" --include "*.log"` |
| `--dryrun` | Show what would be copied | `aws s3 sync . s3://bucket/ --dryrun` |
| `--size-only` | Compare by size only (faster) | `aws s3 sync . s3://bucket/ --size-only` |

### Real-World Example

**Website deployment (dev → prod):**
```bash
# Upload only changed files to production
aws s3 sync ./website-build s3://production-website/ \
  --delete \
  --exclude ".git/*" \
  --exclude "*.tmp"

# Dry run first to see what changes
aws s3 sync ./website-build s3://production-website/ \
  --delete \
  --dryrun
```

**Incremental backup (append-only):**
```bash
# Sync new files daily, never delete
aws s3 sync ./data s3://backup-bucket/data/ \
  --exclude ".DS_Store"

# Check what changed
aws s3 sync ./data s3://backup-bucket/data/ \
  --dryrun
```

---

## Method 3: aws s3api (Fine-Grained Control)

### When to Use
- ✅ Multipart uploads (large files)
- ✅ Custom metadata
- ✅ Encryption with customer keys
- ✅ Complex configurations
- ✅ Automation scripts
- ❌ Simple one-time copies (use cp)
- ❌ Incremental syncs (use sync)

### Basic Usage

**Simple upload:**
```bash
aws s3api put-object \
  --bucket my-bucket \
  --key documents/report.pdf \
  --body ./report.pdf
```

**Upload with metadata:**
```bash
aws s3api put-object \
  --bucket my-bucket \
  --key documents/report.pdf \
  --body ./report.pdf \
  --metadata "author=john,date=2024-01-01"
```

**Download object:**
```bash
aws s3api get-object \
  --bucket my-bucket \
  --key documents/report.pdf \
  ./report.pdf
```

**Get object metadata (no download):**
```bash
aws s3api head-object \
  --bucket my-bucket \
  --key documents/report.pdf
```

### Multipart Upload (Large Files)

For files > 100 MB, use multipart:

```bash
# Step 1: Initiate multipart upload
UPLOAD_ID=$(aws s3api create-multipart-upload \
  --bucket my-bucket \
  --key large-file.zip \
  --query 'UploadId' --output text)

# Step 2: Upload parts (5 MB each minimum)
PART1=$(aws s3api upload-part \
  --bucket my-bucket \
  --key large-file.zip \
  --part-number 1 \
  --body ./part1.bin \
  --upload-id $UPLOAD_ID \
  --query 'ETag' --output text)

PART2=$(aws s3api upload-part \
  --bucket my-bucket \
  --key large-file.zip \
  --part-number 2 \
  --body ./part2.bin \
  --upload-id $UPLOAD_ID \
  --query 'ETag' --output text)

# Step 3: Complete upload
aws s3api complete-multipart-upload \
  --bucket my-bucket \
  --key large-file.zip \
  --upload-id $UPLOAD_ID \
  --multipart-upload Parts=[{ETag=$PART1,PartNumber=1},{ETag=$PART2,PartNumber=2}]
```

---

## Method 4: S3DistCp on EMR (Big Data)

### When to Use
- ✅ 10+ TB datasets
- ✅ Hadoop/Spark environments
- ✅ Need parallelization
- ✅ File transformation during copy
- ❌ Less than 10 TB (too expensive)
- ❌ Not in EMR (overhead not worth it)

### How It Works

```
EMR Cluster (8 nodes)
├─ Node 1: Copy chunk 1 (parallel)
├─ Node 2: Copy chunk 2 (parallel)
├─ Node 3: Copy chunk 3 (parallel)
├─ Node 4: Copy chunk 4 (parallel)
├─ Node 5: Copy chunk 5 (parallel)
├─ Node 6: Copy chunk 6 (parallel)
├─ Node 7: Copy chunk 7 (parallel)
└─ Node 8: Copy chunk 8 (parallel)

Result: 8x faster than single-threaded!
```

### Basic Usage

```bash
# Simple copy S3 to S3
s3-dist-cp --src s3://source-bucket/ --dest s3://dest-bucket/

# Copy with parallelization
s3-dist-cp \
  --src s3://source-bucket/ \
  --dest s3://dest-bucket/ \
  --srcPattern '.*\.parquet$' \
  --numPartitions 128

# Copy with compression
s3-dist-cp \
  --src s3://source-bucket/ \
  --dest s3://dest-bucket/ \
  --outputCodec gzip
```

---

## Performance Comparison

### Speed vs Cost vs Simplicity

| Tool | Speed | Cost | Simplicity | Best For |
|------|-------|------|-----------|----------|
| **aws s3 cp** | ⭐⭐ Moderate | ✓ Low | ⭐⭐⭐⭐⭐ Very easy | Single files, small copies |
| **aws s3 sync** | ⭐⭐ Moderate | ✓ Low | ⭐⭐⭐⭐ Easy | Incremental updates, backups |
| **aws s3api** | ⭐⭐⭐ Variable | ✓ Low | ⭐⭐ Complex | Automation, fine control |
| **S3DistCp** | ⭐⭐⭐⭐⭐ FAST | ✗ Medium | ⭐⭐ Complex | Big data (10+ TB) |

### Data Size vs Recommended Tool

```
< 100 MB      → aws s3 cp
100 MB - 1 GB → aws s3 cp or sync
1 GB - 10 GB  → aws s3 sync
10 GB - 1 TB  → aws s3 sync (optimized)
1 TB - 10 TB  → aws s3 sync (parallel) or S3DistCp
> 10 TB       → S3DistCp on EMR
```

---

## Real-World Scenarios

### Scenario 1: Website Deployment

**Situation:** Deploy website files (100 MB) to S3, only changed files

```bash
# First deployment (initial sync)
aws s3 sync ./dist s3://my-website/ \
  --delete \
  --exclude ".DS_Store" \
  --dryrun  # Check first!

# After verification, remove --dryrun
aws s3 sync ./dist s3://my-website/ \
  --delete \
  --exclude ".DS_Store"

# Daily updates (only sync changes)
aws s3 sync ./dist s3://my-website/ --delete
```

---

### Scenario 2: Daily Log Backup

**Situation:** Backup logs daily (1 GB/day), keep last 30 days

```bash
# Append-only backup (never delete, just add new)
aws s3 sync ./logs s3://log-backup/$(date +%Y-%m-%d)/ \
  --exclude "*.tmp" \
  --exclude "*.lock"

# Daily cron job
0 23 * * * aws s3 sync /var/logs s3://log-backup/$(date +\%Y-\%m-\%d)/ 2>&1 | logger
```

---

### Scenario 3: Large Dataset Migration (10+ TB)

**Situation:** Migrate 500 GB dataset to new bucket, optimize storage

```bash
# Option 1: EMR (if you have cluster)
s3-dist-cp \
  --src s3://old-bucket/data/ \
  --dest s3://new-bucket/data/ \
  --outputCodec gzip \
  --numPartitions 256

# Option 2: Optimized sync for large transfers
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.max_bandwidth 100MB/s
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 64MB

aws s3 sync s3://old-bucket/ s3://new-bucket/ \
  --storage-class STANDARD_IA \
  --dryrun

# After verification
aws s3 sync s3://old-bucket/ s3://new-bucket/ \
  --storage-class STANDARD_IA
```

---

### Scenario 4: Secure Customer File Upload

**Situation:** Allow customers to upload files (Python app)

```python
import boto3

s3 = boto3.client('s3')

def get_upload_presigned_url(customer_id, filename):
    """Generate upload URL for customer"""
    key = f'customer-uploads/{customer_id}/{filename}'

    url = s3.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': 'uploads-bucket',
            'Key': key,
            'ContentType': 'application/octet-stream'
        },
        ExpiresIn=1800  # 30 minutes
    )

    return url

# Customer uploads via presigned URL (not aws s3 cp)
# Then sync completed uploads to archive
os.system('aws s3 sync s3://uploads-bucket/completed s3://archive-bucket/')
```

---

## Pro Tips

### Tip 1: Optimize Large Transfers

```bash
# Configure for parallel transfers
aws configure set default.s3.max_concurrent_requests 20
aws configure set default.s3.multipart_threshold 64MB
aws configure set default.s3.multipart_chunksize 64MB

# Then use sync (benefits from parallel config)
aws s3 sync s3://source s3://dest --storage-class STANDARD_IA
```

### Tip 2: Always Dry Run

```bash
# See what sync WOULD do before running
aws s3 sync ./folder s3://bucket/ --delete --dryrun

# Check output, then run without --dryrun
aws s3 sync ./folder s3://bucket/ --delete
```

### Tip 3: Use Filters Wisely

```bash
# Copy only logs from today
aws s3 sync ./logs s3://backup/ \
  --exclude "*" \
  --include "*.$(date +%Y-%m-%d).log"

# Copy everything except temp files
aws s3 sync . s3://bucket/ \
  --exclude "*.tmp" \
  --exclude ".git/*" \
  --exclude "node_modules/*"
```

### Tip 4: Monitor Progress

```bash
# For large transfers, use --dryrun to estimate time
aws s3 sync s3://source s3://dest --dryrun | wc -l

# Enable debug logging
aws s3 sync s3://source s3://dest --debug
```

---

## Summary Table

| Need | Tool | Command |
|------|------|---------|
| Copy 1 file | cp | `aws s3 cp file.txt s3://bucket/` |
| Copy folder | cp | `aws s3 cp ./folder s3://bucket/ --recursive` |
| Sync changes | sync | `aws s3 sync ./folder s3://bucket/` |
| Delete old files | sync | `aws s3 sync ./folder s3://bucket/ --delete` |
| Fine control | s3api | `aws s3api put-object --bucket bucket --key key --body file` |
| Big data (EMR) | S3DistCp | `s3-dist-cp --src s3://src --dest s3://dest` |

---

**Last Updated:** 2026-05-28
**Level:** Beginner to Intermediate
