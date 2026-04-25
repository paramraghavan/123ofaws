Good question. If Storage Lens is not enabled, you have three fallback options depending on what access you do have.

---

## Option 1 — CloudWatch metrics (most common fallback)

CloudWatch stores `BucketSizeBytes` for every bucket, updated daily, with up to 455 days of history. No admin setup
needed — it's on by default.

```bash
# Verify the metric exists for a bucket before writing the script
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name BucketSizeBytes \
  --dimensions Name=BucketName,Value=your-bucket Name=StorageType,Value=StandardStorage \
  --start-time 2026-01-01T00:00:00Z \
  --end-time   2026-03-31T00:00:00Z \
  --period 86400 \
  --statistics Average
```

If that returns datapoints, you're good. Add this function to `s3_chargeback_lens.py` as a drop-in replacement for
`fetch_lens_exports`:

```python
from datetime import timezone


def fetch_cloudwatch_sizes(start: date, end: date) -> pd.DataFrame:
    """
    Pull BucketSizeBytes from CloudWatch for every bucket and storage type.
    Returns a DataFrame with columns: bucket_name, storage_class, average_storage_bytes.
    Requires: cloudwatch:GetMetricStatistics, s3:ListAllMyBuckets.
    """
    s3 = aws_client("s3")
    cw = aws_client("cloudwatch")

    # CloudWatch storage type → Storage Lens storage class name mapping
    STORAGE_TYPES = {
        "StandardStorage": "StandardStorage",
        "IntelligentTieringStorage": "IntelligentTieringFAStorage",
        "StandardIAStorage": "StandardIAStorage",
        "OneZoneIAStorage": "OneZoneIAStorage",
        "GlacierStorage": "GlacierStorage",
        "GlacierInstantStorage": "GlacierInstantStorage",
        "DeepArchiveStorage": "DeepArchiveStorage",
    }

    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(end, datetime.max.time()).replace(tzinfo=timezone.utc)

    buckets = s3.list_buckets().get("Buckets", [])
    rows = []

    for b in buckets:
        bucket = b["Name"]
        for cw_type, storage_class in STORAGE_TYPES.items():
            try:
                resp = cw.get_metric_statistics(
                    Namespace="AWS/S3",
                    MetricName="BucketSizeBytes",
                    Dimensions=[
                        {"Name": "BucketName", "Value": bucket},
                        {"Name": "StorageType", "Value": cw_type},
                    ],
                    StartTime=start_dt,
                    EndTime=end_dt,
                    Period=86400,  # one datapoint per day
                    Statistics=["Average"],
                )
                points = resp.get("Datapoints", [])
                if not points:
                    continue

                avg_bytes = sum(p["Average"] for p in points) / len(points)
                rows.append({
                    "bucket_name": bucket,
                    "storage_class": storage_class,
                    "average_storage_bytes": avg_bytes,
                })
                log.debug("%s / %s  →  %.2f GB", bucket, cw_type, avg_bytes / (1024 ** 3))

            except Exception as exc:
                log.warning("CloudWatch error for %s/%s: %s", bucket, cw_type, exc)

    if not rows:
        log.warning("CloudWatch returned no BucketSizeBytes datapoints")
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    log.info("CloudWatch: collected %d bucket/storage-class rows for %d buckets",
             len(df), df["bucket_name"].nunique())
    return df
```

Then in `run()` replace the `fetch_lens_exports` call with `fetch_cloudwatch_sizes`:

```python
def run(start: date, end: date) -> pd.DataFrame:
    ...
    raw = fetch_cloudwatch_sizes(start, end)  # ← swap this line
    ...
```

**Accuracy: ~88–92%** — same limitation as Storage Lens: storage costs only, no request or transfer charges.

**Permission needed:** `cloudwatch:GetMetricStatistics` — add this to your role if the checker flags it as missing.

---

## Option 2 — S3 Inventory (most accurate fallback, but slower)

S3 Inventory produces a daily or weekly CSV/ORC listing of every object with its size and storage class. It gives you
the same data as CloudWatch but at object level, so prefix-based splits are exact rather than estimated.

The catch is it needs an admin to enable it per bucket, and the first report takes 24 hours to appear. If you can get
your admin to enable it, the data lands in a bucket you can read.

```bash
# Check if inventory is already configured on a bucket
aws s3api list-bucket-inventory-configurations --bucket your-bucket
```

If it returns configurations, the data is already being collected — ask your admin for read access to the destination
bucket.

---

## Option 3 — S3 List Objects directly (no setup, but slow)

If CloudWatch also isn't available, you can measure bucket sizes the brute-force way using the same
`measure_prefix_sizes_gb` function already in `s3_chargeback_common.py` — just run it against the whole bucket instead
of a prefix:

```python
def fetch_list_objects_sizes(start: date, end: date) -> pd.DataFrame:
    """
    Measure bucket sizes by listing every object via s3:ListObjectsV2.
    No CloudWatch or Storage Lens needed.
    Slow for large buckets — 1M objects ≈ 5 min per bucket.
    Storage class is read from each object's StorageClass field.
    Requires: s3:ListBucket on every bucket.
    """
    s3 = aws_client("s3")
    buckets = s3.list_buckets().get("Buckets", [])
    rows = []

    for b in buckets:
        bucket = b["Name"]
        class_bytes: dict[str, int] = {}
        page_count = 0
        paginator = s3.get_paginator("list_objects_v2")

        try:
            for page in paginator.paginate(Bucket=bucket):
                for obj in page.get("Contents", []):
                    sc = obj.get("StorageClass", "STANDARD")
                    class_bytes[sc] = class_bytes.get(sc, 0) + obj["Size"]
                page_count += 1
                if page_count % 100 == 0:
                    log.info("  %s — %d pages scanned…", bucket, page_count)
        except Exception as exc:
            log.warning("Cannot list %s: %s", bucket, exc)
            continue

        for sc, total_bytes in class_bytes.items():
            rows.append({
                "bucket_name": bucket,
                "storage_class": sc,
                "average_storage_bytes": total_bytes,
            })

    df = pd.DataFrame(rows) if rows else pd.DataFrame()
    if not df.empty:
        log.info("List Objects: sized %d buckets", df["bucket_name"].nunique())
    return df
```

**Accuracy: ~88–92%** — same as CloudWatch. Slower but requires zero setup beyond `s3:ListBucket`.

---

## Decision guide

```
Is CloudWatch returning BucketSizeBytes datapoints?
├── YES → use Option 1 (CloudWatch)  ← fastest, no setup
└── NO  →
      Is S3 Inventory already enabled?
      ├── YES → ask admin for read access to inventory bucket
      └── NO  → use Option 3 (List Objects)  ← works with any s3:ListBucket access
```

Run the permission checker first to see which options are open to you:

```bash
python check_permissions.py --method lens
```

If `cloudwatch:GetMetricStatistics` shows `PASS`, go with Option 1. If it shows `FAIL`, go straight to Option 3 — it
only needs `s3:ListBucket` which you almost certainly already have.