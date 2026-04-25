## Fallback option comparison

---

### History depth

| Option             | 3 months             | 6 months          | 12 months         | Beyond 12 months                                                    |
|--------------------|----------------------|-------------------|-------------------|---------------------------------------------------------------------|
| CloudWatch metrics | ✅                    | ✅                 | ✅                 | ✅ up to 455 days (~15 months), then gone forever                    |
| S3 Inventory       | ✅ if enabled then    | ✅ if enabled then | ✅ if enabled then | ✅ indefinitely — files stay in your S3 bucket until you delete them |
| S3 List Objects    | ❌ current state only | ❌                 | ❌                 | ❌ — zero history, always a live snapshot                            |

**The critical implication:** if you're reading this and Storage Lens is not set up, your window to capture historical
data is closing. CloudWatch deletes metrics older than 455 days with no recovery. S3 List Objects has no history at
all — it shows you what exists *right now*, not what existed in January.

---

### Overall accuracy vs your actual AWS bill

| Option             | Storage charges | Request fees | Data transfer | Accuracy vs bill |
|--------------------|-----------------|--------------|---------------|------------------|
| CloudWatch metrics | ~92%            | ❌            | ❌             | ~80–87%          |
| S3 Inventory       | ~90%            | ❌            | ❌             | ~80–87%          |
| S3 List Objects    | ~75–82%         | ❌            | ❌             | ~68–78%          |

All three miss request fees (GET, PUT, LIST) and data transfer costs. For most storage-heavy workloads those are 8–15%
of the total S3 bill — tolerable for chargeback estimates, but worth disclosing to teams.

---

### Glacier and cold storage tiers

| Scenario                                           | CloudWatch                                   | S3 Inventory                        | S3 List Objects                     |
|----------------------------------------------------|----------------------------------------------|-------------------------------------|-------------------------------------|
| Detects objects in Glacier                         | ✅ via `GlacierStorage` StorageType dimension | ✅ `StorageClass=GLACIER` per object | ✅ `StorageClass=GLACIER` per object |
| Detects Deep Archive                               | ✅ via `DeepArchiveStorage` dimension         | ✅                                   | ✅                                   |
| Detects Glacier Instant Retrieval                  | ✅ via `GlacierInstantStorage`                | ✅                                   | ✅                                   |
| Early deletion fee (deleted before 90-day minimum) | ❌                                            | ❌                                   | ❌                                   |
| Glacier retrieval charges                          | ❌                                            | ❌                                   | ❌                                   |

**Early deletion fees explained.** Glacier Flexible Retrieval has a 90-day minimum storage commitment. Deep Archive has
180 days. If a team deletes a Glacier object on day 30, AWS still bills for the remaining 60 days. None of the three
fallback options capture this — it only appears in CUR. For teams actively archiving and rotating data, this gap can be
meaningful ($0.0036/GB × remaining days × volume deleted early).

---

### Deleted-but-not-purged objects (versioned buckets)

This is the biggest hidden accuracy gap across all three options and is worth understanding in detail.

When S3 versioning is enabled and a user "deletes" an object, AWS does not remove the data. It writes a **delete marker
** and marks that version as non-current. The previous versions remain in the bucket and continue to be billed. Teams
often don't realise they are paying for data they believe they deleted months ago.

| Scenario                                    | CloudWatch                                                                          | S3 Inventory                                                            | S3 List Objects                                                                                   |
|---------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| Non-current versions (deleted but retained) | ✅ included in `BucketSizeBytes` — CloudWatch counts all bytes including non-current | ✅ only if you enable **"Include all versions"** in the inventory config | ❌ `list_objects_v2` skips non-current versions entirely — you need `list_object_versions` instead |
| Delete markers                              | ❌ zero bytes, not counted anywhere                                                  | ✅ visible as entries with `IsDeleteMarker=true`                         | ❌ not returned by `list_objects_v2`                                                               |
| Incomplete multipart uploads                | ❌ not included in CloudWatch metrics                                                | ❌ inventory does not list in-progress uploads                           | ❌ not returned by `list_objects_v2`                                                               |

**Incomplete multipart uploads** are a separate hidden cost. When a multipart upload starts but never completes — due to
a client crash, a bug, or an abandoned job — the parts are stored and billed by the byte. None of the three fallbacks
surface this. The only way to see them is `list_multipart_uploads`. On large-scale platforms with many concurrent
writers, this can quietly accumulate to hundreds of GB.

To fix the S3 List Objects approach for versioned buckets, replace `list_objects_v2` with `list_object_versions`:

```python
def fetch_list_objects_sizes_with_versions(bucket: str) -> dict[str, int]:
    """
    Sum bytes for ALL versions including non-current (deleted-but-retained) objects.
    Also separately sums incomplete multipart uploads.
    Returns {storage_class: total_bytes}.
    """
    s3 = aws_client("s3")
    class_bytes: dict[str, int] = {}

    # ── Current + non-current object versions ────────────────────
    paginator = s3.get_paginator("list_object_versions")
    try:
        for page in paginator.paginate(Bucket=bucket):
            # Versions = current + non-current (not delete markers)
            for obj in page.get("Versions", []):
                sc = obj.get("StorageClass", "STANDARD")
                class_bytes[sc] = class_bytes.get(sc, 0) + obj["Size"]
    except Exception as exc:
        log.warning("list_object_versions failed for %s: %s — falling back", bucket, exc)
        # Bucket may not be versioned; fall back to list_objects_v2
        for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket):
            for obj in page.get("Contents", []):
                sc = obj.get("StorageClass", "STANDARD")
                class_bytes[sc] = class_bytes.get(sc, 0) + obj["Size"]

    # ── Incomplete multipart uploads ──────────────────────────────
    mpu_bytes = 0
    try:
        mpu_paginator = s3.get_paginator("list_multipart_uploads")
        for page in mpu_paginator.paginate(Bucket=bucket):
            for upload in page.get("Uploads", []):
                upload_id = upload["UploadId"]
                key = upload["Key"]
                parts_resp = s3.list_parts(
                    Bucket=bucket, Key=key, UploadId=upload_id
                )
                for part in parts_resp.get("Parts", []):
                    mpu_bytes += part["Size"]
    except Exception as exc:
        log.debug("Could not list multipart uploads for %s: %s", bucket, exc)

    if mpu_bytes:
        class_bytes["IncompleteMultipartUpload"] = mpu_bytes
        log.info("  %s: %.2f GB in incomplete multipart uploads", bucket, mpu_bytes / (1024 ** 3))

    return class_bytes
```

---

### Summary recommendation by scenario

| Your situation                                  | Best option                                                                              |
|-------------------------------------------------|------------------------------------------------------------------------------------------|
| Need Jan–Mar 2026 data right now                | CloudWatch — data is still within 455-day window                                         |
| Need data older than 15 months                  | Only CUR (if it was enabled then) — all three fallbacks are blind beyond their retention |
| Buckets have heavy Glacier usage with deletions | CUR only — early deletion fees are invisible to all fallbacks                            |
| Versioned buckets with lots of "deleted" data   | CloudWatch (counts everything) or Inventory with all-versions enabled                    |
| Buckets with many concurrent writers            | Add the `list_multipart_uploads` check — CloudWatch and Inventory both miss this         |
| No history needed, just current month estimate  | Any of the three work; List Objects is simplest                                          |