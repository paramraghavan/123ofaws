Here's a full walkthrough of what the script does and the decisions made.

---

## Pipeline stages

**Stage 1 — Date validation.** Before making any API calls, it checks your requested range against the 455-day
CloudWatch retention limit and warns you immediately if part of the range is gone. If the entire range is outside the
window it raises an error rather than returning silently empty data.

**Stage 2 — CloudWatch BucketSizeBytes.** For every bucket × every storage type (14 combinations covering Standard, IA,
Glacier, Intelligent Tiering, Deep Archive and their staging variants), it calls `get_metric_statistics` with
`Period=86400` — one datapoint per day. Results are averaged across the date range to produce a representative GB-month
figure. If a bucket has fewer than 50% of the expected daily datapoints, it logs a warning so you know the average is
based on thin data.

**Stage 3 — Non-current versions.** Uses `list_object_versions` filtered to `IsLatest=False` to find objects that
teams "deleted" but which are still being billed in versioned buckets. This is separate from CloudWatch because
CloudWatch *includes* these bytes in its total but doesn't tell you which prefix or team they belong to. The scan
attributes them correctly via prefix matching.

**Stage 4 — Incomplete multipart uploads.** Calls `list_multipart_uploads` then `list_parts` on each upload to sum the
bytes of uploaded-but-never-completed parts. These are completely invisible to CloudWatch and can silently accumulate to
significant cost on platforms with many concurrent writers.

**Stage 5 — Pricing and tagging.** Same Pricing API fetch and tag resolution used by the other scripts in the suite, so
all reports are consistent.

---

## Usage

```bash
# Standard run — Jan to Mar 2026
python s3_chargeback_cloudwatch.py --start 2026-01-01 --end 2026-03-31

# Fast run — skip version and MPU scans (use for a quick estimate)
python s3_chargeback_cloudwatch.py --start 2026-01-01 --end 2026-03-31 --skip-versions

# Debug — shows per-bucket per-storage-type progress
python s3_chargeback_cloudwatch.py --start 2026-01-01 --end 2026-03-31 --debug
```

## Outputs

| File                            | Contents                                                                                                                         |
|---------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `chargeback_summary_*.csv`      | Total cost per team                                                                                                              |
| `chargeback_detail_*.csv`       | Cost per bucket per team, with `source` column showing `CloudWatch BucketSizeBytes`, `Non-current versions`, or `Incomplete MPU` |
| `chargeback_untagged_*.csv`     | Buckets with no team tag                                                                                                         |
| `chargeback_cw_raw_*.csv`       | Every raw CloudWatch datapoint — useful for spotting gaps or thin coverage                                                       |
| `chargeback_prefix_sizes_*.csv` | Prefix split audit (only if `shared_buckets` is configured)                                                                      |

## Permissions needed

```bash
# Quick check before running
python check_permissions.py --method lens   # covers s3 + pricing
# Plus these two which the checker doesn't cover yet:
aws cloudwatch get-metric-statistics --namespace AWS/S3 ...
aws s3api list-object-versions --bucket your-bucket
```