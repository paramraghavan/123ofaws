# Understanding and Using S3 ETags - Complete Guide

> **Master ETags for Upload Verification**: Learn when and how to use ETags effectively for verifying S3 uploads and detecting file changes.

---

## Table of Contents

1. [What is an ETag? (Beginner)](#what-is-an-etag-beginner)
2. [The Mental Model (Sticks in Your Mind)](#the-mental-model-sticks-in-your-mind)
3. [Two Critical Differences](#two-critical-differences)
4. [Reading ETags from S3](#reading-etags-from-s3)
5. [Real-World Use Cases](#real-world-use-cases)
6. [The ETag Trap (Multipart Gotcha)](#the-etag-trap-multipart-gotcha)
7. [When to Use ETags (Decision Tree)](#when-to-use-etags-decision-tree)
8. [Production Best Practices](#production-best-practices)
9. [All Scenarios Explained](#all-scenarios-explained)

---

## What is an ETag? (Beginner)

### Simple Explanation

**ETag** (Entity Tag) is S3's way of saying "here's a fingerprint of this object." It's a hash value that uniquely identifies the content of a file.

**Key idea**: If you upload the same file twice, the ETag should be the same. If the file changes, the ETag changes.

```
Your File (document.pdf)
    ↓
S3 calculates fingerprint
    ↓
ETag: "5d41402abc4b2a76b9719d911017c592"
    ↓
"Your file's fingerprint is this unique code"
```

---

## The Mental Model (Sticks in Your Mind!)

Think of ETags like a **security seal on an envelope**:

```
When you mail a letter:
├─ Envelope seal = Proves envelope hasn't been opened
├─ If seal broken = Someone tampered with it
├─ If seal intact = Original content unchanged

When you upload to S3:
├─ ETag = Fingerprint/seal of file content
├─ You store original ETag somewhere
├─ Later: Compare ETag to see if file changed
├─ Match? = File is unchanged ✓
├─ Different? = File has changed ⚠️
```

**Important caveat**: The seal only works for small, simple uploads. Large uploads (multipart) have a different kind of seal.

---

## Two Critical Differences

This is where most developers get confused. There are **two different types of ETags**:

### Type 1: Simple Upload (Small Files)

**How it works:**
```
File: report.pdf (5 MB)
    ↓
Upload via put_object (single, simple upload)
    ↓
ETag = MD5 hash of the file
    ↓
Example: "5d41402abc4b2a76b9719d911017c592"
```

**What this means:**
- ETag is literally the MD5 checksum of your file
- You can calculate MD5 locally and compare
- Perfect for verification

**Example:**
```python
import hashlib

# Local file MD5
local_md5 = hashlib.md5(open('report.pdf', 'rb').read()).hexdigest()
# Output: "5d41402abc4b2a76b9719d911017c592"

# S3 ETag
s3_etag = s3.head_object(Bucket='my-bucket', Key='report.pdf')['ETag'].strip('"')
# Output: "5d41402abc4b2a76b9719d911017c592"

# Compare
if local_md5 == s3_etag:
    print("✓ File is intact!")
```

---

### Type 2: Multipart Upload (Large Files)

**How it works:**
```
File: large-archive.zip (500 MB)
    ↓
Too big for single upload → Split into parts
    ↓
Part 1 (100 MB) → MD5-A
Part 2 (100 MB) → MD5-B
Part 3 (100 MB) → MD5-C
Part 4 (100 MB) → MD5-D
Part 5 (100 MB) → MD5-E
    ↓
ETag = MD5(A+B+C+D+E) + "-5"
    ↓
Example: "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"
                                         ↑
                                    5 parts
```

**What this means:**
- ETag is NOT the MD5 of the file
- It's the MD5 of the concatenated part hashes, plus the part count
- You CANNOT verify with a simple MD5 comparison
- The hyphen + number tells you how many parts

**Why this matters:**
```python
import hashlib

# You calculate local MD5
local_md5 = hashlib.md5(open('large-archive.zip', 'rb').read()).hexdigest()
# Output: "abc123def456xyz789..."

# S3 returns ETag for multipart upload
s3_etag = s3.head_object(Bucket='my-bucket', Key='large-archive.zip')['ETag'].strip('"')
# Output: "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"

# Compare
if local_md5 == s3_etag:
    print("✓ File is intact!")
else:
    print("✗ Mismatch!")  # ← This ALWAYS happens with multipart!
    # Not because upload failed - because ETag format is different!
```

---

## Reading ETags from S3

### Quick Example (30 seconds)

```python
import boto3

s3 = boto3.client('s3')

# Get object metadata (fast, no download)
response = s3.head_object(Bucket='my-bucket', Key='document.pdf')

# Extract ETag
etag = response['ETag'].strip('"')  # Remove quotes S3 adds
print(f"ETag: {etag}")

# Detect upload type
if '-' in etag:
    parts = etag.split('-')[1]
    print(f"✓ Multipart upload ({parts} parts)")
else:
    print(f"✓ Simple upload (ETag is MD5)")
```

### Key Points

- ✅ Use `head_object()` - Gets metadata without downloading
- ✅ Fast and cheap (no data transfer)
- ⚠️ S3 returns ETag with quotes: `"5d41402abc4b2a76b9719d911017c592"`
- ✅ Strip quotes before comparing: `.strip('"')`
- ✅ Detect multipart by looking for hyphen: `if '-' in etag`

---

## Real-World Use Cases

### Use Case 1: Verify Simple Upload ✓ (Works!)

For small files uploaded with `put_object()` or `upload_file()`:

```python
def verify_simple_upload(bucket, key, local_file):
    """Verify small file upload using MD5"""
    import hashlib
    s3 = boto3.client('s3')

    # Step 1: Calculate local file MD5
    md5_hash = hashlib.md5()
    with open(local_file, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)
    local_md5 = md5_hash.hexdigest()

    # Step 2: Get S3 ETag
    response = s3.head_object(Bucket=bucket, Key=key)
    s3_etag = response['ETag'].strip('"')

    # Step 3: Compare
    if s3_etag == local_md5:
        print(f"✓ Upload verified!")
        return True
    else:
        print(f"✗ Upload mismatch!")
        print(f"  Local: {local_md5}")
        print(f"  S3:    {s3_etag}")
        return False

# Usage
verify_simple_upload('my-bucket', 'documents/report.pdf', 'report.pdf')
```

**When to use this:**
- Files < 100 MB
- Simple single-part upload
- You need to verify integrity immediately after upload

---

### Use Case 2: Detect File Changes Over Time

```python
def check_if_changed(bucket, key, last_known_etag):
    """Did the file change since we last checked?"""
    s3 = boto3.client('s3')

    # Get current ETag
    response = s3.head_object(Bucket=bucket, Key=key)
    current_etag = response['ETag'].strip('"')

    # Compare with stored ETag
    if current_etag != last_known_etag:
        print(f"⚠️  File has changed!")
        print(f"  Was: {last_known_etag}")
        print(f"  Now: {current_etag}")
        return True
    else:
        print(f"✓ File unchanged")
        return False

# Usage
previous_etag = "5d41402abc4b2a76b9719d911017c592"
changed = check_if_changed('my-bucket', 'config.json', previous_etag)
```

**When to use this:**
- Detect if configuration files changed
- Monitor if data was modified
- Cache invalidation checks
- Works for ANY upload type (simple or multipart)

---

### Use Case 3: Track Upload Status with Database

```python
import boto3
from datetime import datetime

def track_upload(bucket, key, local_file):
    """Upload file and store metadata in DynamoDB"""
    s3 = boto3.client('s3')
    dynamodb = boto3.resource('dynamodb')

    # Step 1: Upload file
    print(f"Uploading {local_file}...")
    s3.upload_file(local_file, bucket, key)

    # Step 2: Get metadata
    response = s3.head_object(Bucket=bucket, Key=key)

    # Step 3: Store in database
    upload_info = {
        'bucket': bucket,
        'key': key,
        'etag': response['ETag'].strip('"'),
        'size': response['ContentLength'],
        'last_modified': response['LastModified'].isoformat(),
        'timestamp': datetime.utcnow().isoformat()
    }

    table = dynamodb.Table('UploadTracking')
    table.put_item(Item=upload_info)

    print(f"✓ Upload tracked")
    print(f"  ETag: {upload_info['etag']}")
    print(f"  Size: {upload_info['size']} bytes")

# Usage
track_upload('my-bucket', 'documents/report.pdf', 'report.pdf')
```

**When to use this:**
- Need audit trail of uploads
- Track which version of file is in S3
- Monitor upload frequency
- Works for all upload types

---

## The ETag Trap (Multipart Gotcha)

### The Problem Most Developers Hit

```python
# Developer's logic:
# "I'll calculate MD5 locally, compare with S3 ETag, easy!"

import hashlib

local_file = 'large-archive.zip'  # 500 MB file

# Calculate local MD5
with open(local_file, 'rb') as f:
    local_md5 = hashlib.md5(f.read()).hexdigest()

print(f"Local MD5:  {local_md5}")
# Output: "a7c6e6fc8b3e5f9d2c1b0a9f8e7d6c5b"

# Get S3 ETag
response = s3.head_object(Bucket='bucket', Key='archive.zip')
s3_etag = response['ETag'].strip('"')

print(f"S3 ETag:    {s3_etag}")
# Output: "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"

# Developer tries to compare:
if local_md5 == s3_etag:
    print("✓ Upload OK")
else:
    print("✗ Upload FAILED!")  # ← WRONG! Upload actually succeeded!
```

### Why It Fails

Because S3 automatically split the 500 MB file into 5 parts (multipart upload):

```
What developer calculated:  MD5 of entire file
What S3 stored:            MD5(concat of part hashes) + "-5"

Different formats = Different results
NOT a real mismatch = False alarm!
```

### The Solution

**Option 1: Accept the limitation**
- Just check if object exists in S3
- Trust S3's integrity checks
- For large files, multipart is reliable

**Option 2: Store custom metadata**
- Upload file with custom metadata containing MD5
- Later, verify using metadata
- Most reliable approach

```python
def upload_with_metadata(bucket, key, local_file):
    """Upload with custom MD5 in metadata"""
    import hashlib
    s3 = boto3.client('s3')

    # Calculate MD5
    with open(local_file, 'rb') as f:
        local_md5 = hashlib.md5(f.read()).hexdigest()

    # Upload with metadata
    s3.upload_file(
        local_file,
        bucket,
        key,
        ExtraArgs={
            'Metadata': {
                'original-md5': local_md5,
                'uploaded-by': 'verification-system'
            }
        }
    )

    # Later, verify using metadata
    response = s3.head_object(Bucket=bucket, Key=key)
    stored_md5 = response['Metadata'].get('original-md5')

    if stored_md5 == local_md5:
        print("✓ Upload verified!")
    else:
        print("✗ Upload mismatch!")

# Usage
upload_with_metadata('my-bucket', 'archive.zip', 'large-archive.zip')
```

---

## When to Use ETags (Decision Tree)

```
Do you need to verify a file upload?
│
├─ YES, small file (<100 MB)
│  └─ Upload: put_object() or upload_file()
│     └─ Can verify with local MD5 vs ETag ✓
│     └─ Use: Simple comparison works
│
├─ YES, large file (>100 MB)
│  └─ S3 uses multipart automatically
│     └─ ETag ≠ local MD5 ✗
│     └─ Use: Store custom metadata instead
│
├─ Detect if file changed?
│  └─ YES
│     └─ ETag works for any size ✓
│     └─ Store old ETag, compare later
│
└─ Just want to know if file exists?
   └─ YES
      └─ ETag proves it's there ✓
      └─ No comparison needed
```

---

## Production Best Practices

### ✅ DO: Store Custom Metadata for Verification

```python
def robust_upload(bucket, key, local_file):
    """Production-grade upload with verification"""
    import hashlib
    import os
    s3 = boto3.client('s3')

    # Calculate file hash
    with open(local_file, 'rb') as f:
        md5_hash = hashlib.md5(f.read()).hexdigest()

    file_size = os.path.getsize(local_file)

    # Upload with metadata
    s3.upload_file(
        local_file,
        bucket,
        key,
        ExtraArgs={
            'Metadata': {
                'original-md5': md5_hash,
                'original-size': str(file_size),
            }
        }
    )

    # Verify immediately
    response = s3.head_object(Bucket=bucket, Key=key)

    size_match = response['ContentLength'] == file_size
    md5_match = response['Metadata'].get('original-md5') == md5_hash

    if size_match and md5_match:
        print(f"✓ Upload verified for {key}")
        return True
    else:
        print(f"✗ Upload verification failed!")
        return False
```

### ✅ DO: Check File Size

Always verify file size - it's more reliable than ETag:

```python
def verify_by_size(bucket, key, expected_size):
    """Simple size verification"""
    s3 = boto3.client('s3')

    response = s3.head_object(Bucket=bucket, Key=key)

    if response['ContentLength'] == expected_size:
        print("✓ File size matches")
        return True
    else:
        print(f"✗ Size mismatch!")
        print(f"  Expected: {expected_size} bytes")
        print(f"  Got: {response['ContentLength']} bytes")
        return False
```

### ✅ DO: Use Version IDs for Tracking Changes

```python
def track_with_version_id(bucket, key):
    """Use Version ID for tracking (requires versioning enabled)"""
    s3 = boto3.client('s3')

    response = s3.head_object(Bucket=bucket, Key=key)

    # Version ID is unique for each object version
    version_id = response['VersionId']

    return {
        'key': key,
        'version_id': version_id,  # Unique per upload
        'etag': response['ETag'].strip('"'),
        'last_modified': response['LastModified']
    }
```

### ❌ DON'T: Assume ETag = MD5 for Large Files

```python
# ❌ WRONG - This will fail silently!
local_md5 = calculate_md5(large_file)
s3_etag = get_s3_etag(bucket, key)

if local_md5 == s3_etag:
    print("Upload OK")  # False negative for multipart!
```

### ❌ DON'T: Ignore the Hyphen in ETag

```python
# ❌ WRONG - Doesn't detect multipart
etag = "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"
md5_value = etag  # Includes the "-5"!

# ✅ CORRECT
etag = "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"
is_multipart = '-' in etag
```

---

## All Scenarios Explained

### Scenario 1: Simple Upload (5 MB file)

```
File: report.pdf (5 MB)
Upload method: s3.put_object() or s3.upload_file()
Size: < multipart threshold (default 5 MB for upload_file)
ETag: "5d41402abc4b2a76b9719d911017c592"
      └─ This is MD5(file)
Verification: ✓ Can compare local MD5 to ETag
```

### Scenario 2: Multipart Upload (500 MB file)

```
File: large-archive.zip (500 MB)
Upload method: s3.upload_file() (auto-multipart for large files)
Parts: 5 parts of 100 MB each
ETag: "9bbf7a3cf63a10e6f3c1e2ce6b8c8f7d-5"
      └─ MD5(MD5-1+MD5-2+MD5-3+MD5-4+MD5-5) + "-5"
      └─ NOT the file's MD5
Verification: ✗ Can't use simple MD5 comparison
            ✓ Use size or custom metadata instead
```

### Scenario 3: Encrypted Upload (SSE-C)

```
File: sensitive-data.txt (encrypted with your key)
Upload method: s3.put_object(..., SSECustomerAlgorithm='AES256')
ETag: "hash-that-includes-encryption-info"
      └─ NOT simple MD5
      └─ Different from unencrypted version
Verification: ✗ Don't compare ETags across encryption changes
            ✓ Use custom metadata or Version IDs
```

### Scenario 4: Cross-Region Replication

```
File: data.json (replicated to another region)
Original ETag: "5d41402abc4b2a76b9719d911017c592"
Replicated ETag: "5d41402abc4b2a76b9719d911017c592"
Verification: ✓ Same ETag = data is identical
```

---

## Summary Table

| Situation | ETag Useful? | What to Use |
|-----------|------|----------|
| **Verify simple upload** | ✓ Yes | Compare local MD5 to ETag |
| **Verify large upload** | ✗ No | Check size + custom metadata |
| **Detect file changed** | ✓ Yes | Store old ETag, compare new |
| **Monitor uploads** | ✓ Yes | Track ETag in database |
| **Encrypted files** | ✗ No | Use custom metadata |
| **CloudFront cache** | ✓ Yes | Use for cache keys |
| **Cross-region verify** | ✓ Yes | ETag stays same if content same |

---

## Key Takeaways

| Concept | Remember |
|---------|----------|
| **ETag = Fingerprint** | Unique to file content, same file = same ETag |
| **Simple upload** | ETag is MD5 hash of file ✓ |
| **Multipart upload** | ETag is NOT file's MD5 ✗ |
| **Detect by format** | Hyphen in ETag? = Multipart (e.g., "hash-5") |
| **Best verification** | Use size + custom metadata, not ETag alone |
| **ETag never changes** | For same object (unless object changes) |
| **head_object()** | Gets ETag without downloading (fast!) |
| **Strip quotes** | S3 returns ETag with `"`, use `.strip('"')` |

---

## Common Gotchas Summary

```
GOTCHA 1: "ETag should match my local MD5"
REALITY: Only true for simple uploads < 100 MB
SOLUTION: Check file size instead, or store custom metadata

GOTCHA 2: "ETag proves upload succeeded"
REALITY: ETag just proves file is in S3, not that it's correct
SOLUTION: Also verify size and content with metadata

GOTCHA 3: "I can calculate S3 multipart ETag locally"
REALITY: Multipart ETag has complex calculation that varies by part size
SOLUTION: Don't bother - use custom metadata or size checks

GOTCHA 4: "ETag changes when I encrypt the file"
REALITY: Encryption can affect ETag for some operations
SOLUTION: Store original metadata before encryption
```

---

## See Also

- `read_etag_of_s3object.py` - Production Python implementation
- AWS S3 Docs - [Checking Object Integrity](https://docs.aws.amazon.com/AmazonS3/latest/userguide/checking-object-integrity.html)
- `copy-large-file-between-s3-buckets.md` - DataSync multipart handling

---

**Last Updated:** 2026-05-28
**Level:** Beginner to Intermediate
