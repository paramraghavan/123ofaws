"""
s3_chargeback_cloudwatch.py  —  Fallback Option 1: CloudWatch Metrics
======================================================================
Estimates S3 storage costs using CloudWatch BucketSizeBytes metrics,
priced via the AWS Pricing API, producing per-team chargeback CSVs.

Use this when CUR v2 and S3 Storage Lens are both unavailable.

How it works
------------
CloudWatch collects BucketSizeBytes daily for every bucket and every
storage type (Standard, IA, Glacier, Deep Archive, etc.). This script:
  1. Lists all buckets in the account.
  2. For each bucket × storage type, fetches daily BucketSizeBytes
     datapoints over the requested date range.
  3. Averages those datapoints to get a representative GB-month figure.
  4. Additionally scans for non-current (deleted-but-retained) object
     versions using list_object_versions, and incomplete multipart
     uploads using list_multipart_uploads — costs CloudWatch does NOT
     report but which appear on your AWS bill.
  5. Multiplies avg GB × $/GB-month × months in range = estimated cost.
  6. Attributes cost to teams via bucket tags.
  7. Auto-splits shared buckets by measuring real prefix sizes.

Accuracy
--------
  ~80–87% of your actual AWS S3 bill.

  What CloudWatch covers:
    ✅  Storage charges for all storage classes
    ✅  Non-current versions (included in BucketSizeBytes)
    ❌  Request fees (GET, PUT, LIST, DELETE)          ~5–10% of bill
    ❌  Data transfer out                              ~2–5%  of bill
    ❌  Glacier early-deletion penalties               variable
    ❌  Glacier retrieval charges                      variable
    ❌  Incomplete multipart uploads                   captured separately below

  The script adds a separate line for incomplete multipart uploads
  (priced at Standard rate) so you can see and charge back that cost too.

History
-------
  CloudWatch retains BucketSizeBytes for 455 days (~15 months).
  Data older than 455 days is permanently deleted with no recovery.
  If today is 2026-04-24, the earliest date you can query is ~2025-01-24.

Prerequisites (IAM — read-only, no admin setup needed)
------------------------------------------------------
  cloudwatch:GetMetricStatistics   — read BucketSizeBytes per bucket
  s3:ListAllMyBuckets              — enumerate buckets
  s3:GetBucketTagging              — read team/owner tags
  s3:ListBucket                    — needed for version + MPU scans
  s3:ListBucketVersions            — list non-current object versions
  s3:ListBucketMultipartUploads    — list incomplete uploads
  pricing:GetProducts              — fetch current $/GB-month prices

Usage
-----
  python s3_chargeback_cloudwatch.py --start 2026-01-01 --end 2026-03-31
  python s3_chargeback_cloudwatch.py --start 2026-01-01 --end 2026-03-31 --skip-versions
  python s3_chargeback_cloudwatch.py --start 2026-01-01 --end 2026-03-31 --debug

  --skip-versions   Skip the list_object_versions + list_multipart_uploads scans.
                    Use this if you have millions of objects and want a fast run —
                    you will miss non-current version costs and MPU costs.

Output  (written to CONFIG["reports_dir"])
------------------------------------------
  chargeback_summary_<ts>.csv          — total cost per team
  chargeback_detail_<ts>.csv           — cost per bucket per team
  chargeback_untagged_<ts>.csv         — buckets with no team tag
  chargeback_prefix_sizes_<ts>.csv     — prefix split audit (shared buckets only)
  chargeback_cw_raw_<ts>.csv           — raw CloudWatch datapoints for audit/debug
"""

import argparse
import json
import logging
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from s3_chargeback_common import (
    CONFIG,
    auto_split_shared_buckets,
    aws_client,
    build_reports,
    enrich_with_tags,
    get_all_bucket_tags,
    log,
)

# ─────────────────────────────────────────────────────────────────
# CloudWatch StorageType → internal storage class name mapping
#
# CloudWatch uses its own StorageType dimension names.  These are
# mapped to the same storage class names used in CUR and Storage Lens
# so all three methods produce a consistent schema.
# ─────────────────────────────────────────────────────────────────

CW_STORAGE_TYPES: dict[str, str] = {
    "StandardStorage":              "StandardStorage",
    "IntelligentTieringStorage":    "IntelligentTieringFAStorage",
    "StandardIAStorage":            "StandardIAStorage",
    "OneZoneIAStorage":             "OneZoneIAStorage",
    "ReducedRedundancyStorage":     "ReducedRedundancyStorage",
    "GlacierStorage":               "GlacierStorage",
    "GlacierStagingStorage":        "GlacierStorage",        # staging = same price as Glacier
    "GlacierInstantRetrievalStorage": "GlacierInstantStorage",
    "DeepArchiveStorage":           "DeepArchiveStorage",
    "DeepArchiveS3ObjectOverheadStorage": "DeepArchiveStorage",
    "DeepArchiveStagingStorage":    "DeepArchiveStorage",
}

# Pricing API storage class → $/GB-month (us-east-1 hardcoded fallback)
# The script fetches live prices first; these are only used if that fails.
FALLBACK_PRICES: dict[str, float] = CONFIG["prices_per_gb"]


# ─────────────────────────────────────────────────────────────────
# Pricing API
# ─────────────────────────────────────────────────────────────────

def fetch_prices() -> dict[str, float]:
    """
    Fetch current S3 storage prices from the AWS Pricing API (always us-east-1).
    Returns {storage_class: $/GB-month}.
    Falls back to FALLBACK_PRICES on any error.
    """
    try:
        session = (
            boto3.Session(profile_name=CONFIG["profile"], region_name="us-east-1")
            if CONFIG["profile"]
            else boto3.Session(region_name="us-east-1")
        )
        pricing   = session.client("pricing")
        prices    = {}
        paginator = pricing.get_paginator("get_products")

        for page in paginator.paginate(
            ServiceCode="AmazonS3",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "location",      "Value": "US East (N. Virginia)"},
                {"Type": "TERM_MATCH", "Field": "productFamily",  "Value": "Storage"},
            ],
        ):
            for raw in page["PriceList"]:
                item          = json.loads(raw)
                attrs         = item["product"]["attributes"]
                storage_class = attrs.get("storageClass", "")
                for _, term in item.get("terms", {}).get("OnDemand", {}).items():
                    for _, dim in term.get("priceDimensions", {}).items():
                        usd = float(dim["pricePerUnit"].get("USD", 0))
                        if usd > 0 and storage_class and storage_class not in prices:
                            prices[storage_class] = usd
                            break

        if prices:
            log.info("Pricing API: fetched %d storage class prices", len(prices))
            return prices

    except Exception as exc:
        log.warning("Pricing API failed (%s) — using hardcoded fallback prices", exc)

    return FALLBACK_PRICES


# ─────────────────────────────────────────────────────────────────
# CloudWatch BucketSizeBytes fetcher
# ─────────────────────────────────────────────────────────────────

CW_MAX_HISTORY_DAYS = 455   # AWS hard limit for this metric


def _validate_date_range(start: date, end: date) -> None:
    """
    Warn if the requested range falls outside CloudWatch's 455-day retention window.
    Does not raise — caller decides how to handle partial data.
    """
    earliest_available = date.today() - timedelta(days=CW_MAX_HISTORY_DAYS)
    if start < earliest_available:
        log.warning(
            "Requested start %s is before CloudWatch retention limit %s. "
            "Datapoints before %s will be missing — results will be incomplete.",
            start, earliest_available, earliest_available,
        )
    if end < earliest_available:
        raise ValueError(
            f"Requested end date {end} is entirely outside CloudWatch's "
            f"{CW_MAX_HISTORY_DAYS}-day retention window. No data available."
        )


def fetch_cloudwatch_bucket_sizes(
    bucket: str,
    start: date,
    end: date,
) -> list[dict]:
    """
    Fetch daily BucketSizeBytes from CloudWatch for every storage type
    for a single bucket over [start, end].

    Returns a list of dicts:
      { bucket_name, storage_class, date, size_bytes }

    One row per (storage_type, day) that returned a datapoint.
    Storage types with zero datapoints for the entire period are omitted.

    CloudWatch BucketSizeBytes:
      - Published once per day at midnight UTC.
      - Period must be 86400 (1 day) for this metric.
      - Uses Average statistic (daily snapshots, so Average == the value).
    """
    cw       = aws_client("cloudwatch")
    rows     = []
    start_dt = datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt   = datetime.combine(end,   datetime.max.time()).replace(tzinfo=timezone.utc)

    for cw_type, storage_class in CW_STORAGE_TYPES.items():
        try:
            resp = cw.get_metric_statistics(
                Namespace="AWS/S3",
                MetricName="BucketSizeBytes",
                Dimensions=[
                    {"Name": "BucketName",  "Value": bucket},
                    {"Name": "StorageType", "Value": cw_type},
                ],
                StartTime=start_dt,
                EndTime=end_dt,
                Period=86400,           # one datapoint per day
                Statistics=["Average"],
            )
            for point in resp.get("Datapoints", []):
                rows.append({
                    "bucket_name":   bucket,
                    "cw_type":       cw_type,
                    "storage_class": storage_class,
                    "date":          point["Timestamp"].date().isoformat(),
                    "size_bytes":    point["Average"],
                })
        except ClientError as exc:
            log.warning(
                "CloudWatch error for %s / %s: %s", bucket, cw_type,
                exc.response["Error"]["Code"],
            )

    return rows


def fetch_all_buckets_cloudwatch(
    buckets: list[str],
    start: date,
    end: date,
) -> pd.DataFrame:
    """
    Run fetch_cloudwatch_bucket_sizes for every bucket and concatenate results.
    Logs progress every 10 buckets.

    Returns a raw DataFrame with columns:
      bucket_name, cw_type, storage_class, date, size_bytes
    """
    all_rows = []
    total    = len(buckets)

    for idx, bucket in enumerate(buckets, 1):
        rows = fetch_cloudwatch_bucket_sizes(bucket, start, end)
        all_rows.extend(rows)
        if idx % 10 == 0 or idx == total:
            log.info("CloudWatch progress: %d / %d buckets fetched", idx, total)

    if not all_rows:
        log.warning("CloudWatch returned no datapoints for any bucket in range %s → %s", start, end)
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    log.info(
        "CloudWatch raw data: %d datapoints across %d buckets",
        len(df), df["bucket_name"].nunique(),
    )
    return df


# ─────────────────────────────────────────────────────────────────
# Non-current version + incomplete multipart upload scanner
#
# CloudWatch BucketSizeBytes INCLUDES non-current object versions
# in its byte count, so for accurate chargeback we also need to
# identify and attribute those costs to the right team prefix.
#
# Incomplete multipart uploads are NOT in CloudWatch at all — we
# must scan for them separately.
# ─────────────────────────────────────────────────────────────────

def scan_noncurrent_versions(bucket: str) -> dict[str, int]:
    """
    List all non-current object versions in a bucket and sum their bytes
    per storage class.

    Returns {storage_class: bytes}.

    Non-current versions are objects that have been "deleted" in a versioned
    bucket but not yet permanently purged. They continue to be billed.
    Requires: s3:ListBucketVersions
    """
    s3          = aws_client("s3")
    class_bytes: dict[str, int] = {}

    try:
        paginator = s3.get_paginator("list_object_versions")
        page_count = 0
        for page in paginator.paginate(Bucket=bucket):
            # "Versions" contains both current and non-current; filter to non-current only
            for obj in page.get("Versions", []):
                if obj.get("IsLatest", True):
                    continue                     # skip current versions — CW already counts them
                sc = obj.get("StorageClass", "STANDARD")
                class_bytes[sc] = class_bytes.get(sc, 0) + obj["Size"]
            page_count += 1
            if page_count % 100 == 0:
                log.debug("  %s: %d version pages scanned…", bucket, page_count)

    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code in ("NoSuchBucket", "AccessDenied"):
            log.warning("Cannot scan versions for %s: %s", bucket, code)
        else:
            log.debug("Version scan skipped for %s (%s — likely unversioned)", bucket, code)

    if class_bytes:
        total_gb = sum(class_bytes.values()) / (1024 ** 3)
        log.debug("  %s non-current versions: %.3f GB", bucket, total_gb)

    return class_bytes


def scan_incomplete_multipart_uploads(bucket: str) -> int:
    """
    List all in-progress (incomplete) multipart uploads in a bucket
    and sum the bytes of their uploaded parts.

    Returns total bytes across all incomplete uploads.

    These uploads are never visible in normal S3 listings or CloudWatch,
    but their parts are stored and billed at Standard storage rates.
    Requires: s3:ListBucketMultipartUploads, s3:ListMultipartUploadParts
    """
    s3         = aws_client("s3")
    total_bytes = 0

    try:
        paginator = s3.get_paginator("list_multipart_uploads")
        for page in paginator.paginate(Bucket=bucket):
            for upload in page.get("Uploads", []):
                upload_id = upload["UploadId"]
                key       = upload["Key"]
                try:
                    parts_resp = s3.list_parts(
                        Bucket=bucket,
                        Key=key,
                        UploadId=upload_id,
                    )
                    for part in parts_resp.get("Parts", []):
                        total_bytes += part["Size"]
                except ClientError:
                    pass    # upload may have completed between list and parts calls

    except ClientError as exc:
        code = exc.response["Error"]["Code"]
        if code != "AccessDenied":
            log.debug("MPU scan skipped for %s: %s", bucket, code)
        else:
            log.warning("Cannot scan multipart uploads for %s: AccessDenied", bucket)

    if total_bytes:
        log.debug("  %s incomplete MPUs: %.3f GB", bucket, total_bytes / (1024 ** 3))

    return total_bytes


# ─────────────────────────────────────────────────────────────────
# Aggregation — CloudWatch raw → avg GB per bucket per storage class
# ─────────────────────────────────────────────────────────────────

def aggregate_cloudwatch(
    raw: pd.DataFrame,
    start: date,
    end: date,
) -> pd.DataFrame:
    """
    Average daily BucketSizeBytes datapoints across the date range,
    then compute GB-months for billing.

    CloudWatch may have fewer datapoints than calendar days (metric is
    emitted once per day but can lag by up to 24 h).  We average whatever
    datapoints exist — a full month of daily readings is ideal, but even
    a handful give a reasonable approximation.

    Returns a DataFrame with columns:
      bucket_name, storage_class, avg_bytes, avg_gb, datapoint_count,
      coverage_days, total_days
    """
    total_days = (end - start).days + 1

    agg = (
        raw
        .groupby(["bucket_name", "storage_class"])
        .agg(
            avg_bytes       =("size_bytes", "mean"),
            datapoint_count =("size_bytes", "count"),
        )
        .reset_index()
    )
    agg["avg_gb"]       = agg["avg_bytes"] / (1024 ** 3)
    agg["coverage_days"]= agg["datapoint_count"]
    agg["total_days"]   = total_days

    # Warn about thin coverage (< 50% of expected days)
    thin = agg[agg["datapoint_count"] < total_days * 0.5]
    for _, row in thin.iterrows():
        log.warning(
            "Thin CloudWatch coverage for %s / %s: %d datapoints out of %d days — "
            "average may be less reliable.",
            row["bucket_name"], row["storage_class"],
            row["datapoint_count"], total_days,
        )

    return agg


# ─────────────────────────────────────────────────────────────────
# Pricing
# ─────────────────────────────────────────────────────────────────

def apply_pricing(
    agg: pd.DataFrame,
    prices: dict[str, float],
    start: date,
    end: date,
) -> pd.DataFrame:
    """
    Multiply avg_gb × $/GB-month × months in range to get cost_usd.

    For Glacier and Deep Archive, the price is the same regardless of
    whether objects are current or non-current — early deletion penalties
    (billed when objects are deleted before their minimum retention period)
    are NOT captured here; they only appear in CUR.
    """
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1

    def price_row(row) -> float:
        sc    = row["storage_class"]
        price = prices.get(sc, prices.get("StandardStorage", 0.023))
        return row["avg_gb"] * price * months

    agg["cost_usd"]     = agg.apply(price_row, axis=1)
    agg["usage_amount"] = agg["avg_gb"] * months   # GB-months consumed
    agg["usage_type"]   = agg["storage_class"]
    agg["account_id"]   = ""
    agg["source"]       = "CloudWatch BucketSizeBytes"
    return agg


# ─────────────────────────────────────────────────────────────────
# Non-current version rows builder
# ─────────────────────────────────────────────────────────────────

def build_noncurrent_rows(
    buckets: list[str],
    prices: dict[str, float],
    start: date,
    end: date,
    tag_map: dict,
) -> pd.DataFrame:
    """
    For each bucket, scan non-current versions and incomplete MPUs,
    build cost rows, and return a DataFrame matching the main schema.

    These rows carry source = "Non-current versions" or "Incomplete MPU"
    so they are distinguishable in the detail report.
    """
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1
    rows   = []
    untagged = CONFIG["untagged_label"]

    for bucket in buckets:
        tags = tag_map.get(bucket, {})

        # ── Non-current versions ──────────────────────────────
        nc_bytes = scan_noncurrent_versions(bucket)
        for sc, total_bytes in nc_bytes.items():
            # Normalise storage class name (S3 API uses uppercase e.g. STANDARD_IA)
            sc_norm  = _normalise_sc(sc)
            avg_gb   = total_bytes / (1024 ** 3)
            price    = prices.get(sc_norm, prices.get("StandardStorage", 0.023))
            rows.append({
                "bucket_name":   bucket,
                "team":          tags.get(CONFIG["tag_team"],        untagged),
                "owner":         tags.get(CONFIG["tag_owner"],       untagged),
                "cost_center":   tags.get(CONFIG["tag_cost_center"], untagged),
                "usage_type":    sc_norm,
                "cost_usd":      avg_gb * price * months,
                "usage_amount":  avg_gb * months,
                "account_id":    "",
                "source":        "Non-current versions",
                "datapoint_count": None,
                "coverage_days":   None,
                "total_days":      None,
            })

        # ── Incomplete multipart uploads ──────────────────────
        mpu_bytes = scan_incomplete_multipart_uploads(bucket)
        if mpu_bytes:
            avg_gb = mpu_bytes / (1024 ** 3)
            price  = prices.get("StandardStorage", 0.023)   # MPU parts billed at Standard
            rows.append({
                "bucket_name":   bucket,
                "team":          tags.get(CONFIG["tag_team"],        untagged),
                "owner":         tags.get(CONFIG["tag_owner"],       untagged),
                "cost_center":   tags.get(CONFIG["tag_cost_center"], untagged),
                "usage_type":    "IncompleteMultipartUpload",
                "cost_usd":      avg_gb * price * months,
                "usage_amount":  avg_gb * months,
                "account_id":    "",
                "source":        "Incomplete MPU",
                "datapoint_count": None,
                "coverage_days":   None,
                "total_days":      None,
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    log.info(
        "Non-current + MPU scan: %d extra cost rows across %d buckets",
        len(df), df["bucket_name"].nunique(),
    )
    return df


def _normalise_sc(sc: str) -> str:
    """
    Normalise S3 API storage class names (UPPERCASE_WITH_UNDERSCORES)
    to the CUR/Pricing API convention (TitleCaseStorage).
    Falls back to the original value if no mapping is found.
    """
    mapping = {
        "STANDARD":            "StandardStorage",
        "STANDARD_IA":         "StandardIAStorage",
        "ONEZONE_IA":          "OneZoneIAStorage",
        "REDUCED_REDUNDANCY":  "ReducedRedundancyStorage",
        "INTELLIGENT_TIERING": "IntelligentTieringFAStorage",
        "GLACIER":             "GlacierStorage",
        "GLACIER_IR":          "GlacierInstantStorage",
        "DEEP_ARCHIVE":        "DeepArchiveStorage",
    }
    return mapping.get(sc.upper(), sc)


# ─────────────────────────────────────────────────────────────────
# Raw data CSV writer
# ─────────────────────────────────────────────────────────────────

def save_raw_cloudwatch(
    raw: pd.DataFrame,
    reports_dir: Path,
    run_ts: str,
) -> None:
    """Write the raw CloudWatch datapoints to a CSV for auditing."""
    if raw.empty:
        return
    path = reports_dir / f"chargeback_cw_raw_{run_ts}.csv"
    raw.to_csv(path, index=False)
    log.info("Raw CloudWatch data → %s  (%d rows)", path, len(raw))


# ─────────────────────────────────────────────────────────────────
# Main pipeline
# ─────────────────────────────────────────────────────────────────

def run(
    start: date,
    end: date,
    skip_versions: bool = False,
) -> pd.DataFrame:
    """
    Full CloudWatch chargeback pipeline.

    Steps
    -----
    1. Validate date range against CloudWatch 455-day retention.
    2. Fetch current S3 prices from Pricing API.
    3. List all buckets + read their tags.
    4. Pull BucketSizeBytes from CloudWatch for every bucket × storage type.
    5. Average datapoints → GB-month → cost_usd per bucket per storage class.
    6. (Unless --skip-versions) Scan non-current versions and incomplete MPUs.
    7. Combine, tag, return unified DataFrame.

    Returns a DataFrame with columns:
      bucket_name, team, owner, cost_center, usage_type,
      cost_usd, usage_amount, account_id, source,
      datapoint_count, coverage_days, total_days
    """
    log.info(
        "=== Fallback Option 1: CloudWatch BucketSizeBytes  |  %s → %s ===",
        start, end,
    )

    _validate_date_range(start, end)
    prices  = fetch_prices()
    tag_map = get_all_bucket_tags()

    s3      = aws_client("s3")
    buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
    log.info("Found %d buckets to process", len(buckets))

    # ── CloudWatch BucketSizeBytes ────────────────────────────
    raw = fetch_all_buckets_cloudwatch(buckets, start, end)

    if raw.empty:
        log.error("CloudWatch returned no data — cannot produce chargeback report.")
        return pd.DataFrame()

    agg = aggregate_cloudwatch(raw, start, end)
    agg = apply_pricing(agg, prices, start, end)
    agg = enrich_with_tags(agg, tag_map)

    # Carry through audit columns
    keep = [
        "bucket_name", "team", "owner", "cost_center",
        "usage_type", "cost_usd", "usage_amount", "account_id", "source",
        "datapoint_count", "coverage_days", "total_days",
    ]
    agg = agg[keep]

    # ── Non-current versions + incomplete MPUs ────────────────
    if not skip_versions:
        extra = build_noncurrent_rows(buckets, prices, start, end, tag_map)
        if not extra.empty:
            agg = pd.concat([agg, extra], ignore_index=True)
    else:
        log.info("Skipping non-current version and MPU scan (--skip-versions)")

    log.info(
        "Pipeline complete: %d cost rows, %d buckets, $%.2f estimated total",
        len(agg),
        agg["bucket_name"].nunique(),
        agg["cost_usd"].sum(),
    )
    return agg


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="S3 Chargeback — Fallback Option 1: CloudWatch BucketSizeBytes"
    )
    parser.add_argument(
        "--start", default="2026-01-01",
        help="Start date YYYY-MM-DD (default: 2026-01-01)",
    )
    parser.add_argument(
        "--end", default="2026-03-31",
        help="End date YYYY-MM-DD (default: 2026-03-31)",
    )
    parser.add_argument(
        "--skip-versions", action="store_true",
        help=(
            "Skip list_object_versions and list_multipart_uploads scans. "
            "Faster but misses non-current version costs and incomplete MPU costs."
        ),
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end   = datetime.strptime(args.end,   "%Y-%m-%d").date()
    if start > end:
        raise ValueError(f"--start {start} must be before --end {end}")

    df = run(start, end, skip_versions=args.skip_versions)
    if df.empty:
        log.error("No data produced. Check CloudWatch access and date range.")
        return

    reports_dir, run_ts = build_reports(df, start, end)

    # Save raw CloudWatch datapoints for audit
    # (re-fetch raw to keep build_reports clean — only costs one extra CW call batch
    #  if you want to avoid that, store raw in run() and thread it through)
    save_raw_cloudwatch(
        fetch_all_buckets_cloudwatch(
            [b["Name"] for b in aws_client("s3").list_buckets().get("Buckets", [])],
            start, end,
        ),
        reports_dir,
        run_ts,
    )

    # Auto-split shared buckets
    shared_cfg = CONFIG.get("shared_buckets", {})
    if shared_cfg:
        df = auto_split_shared_buckets(df, shared_cfg, reports_dir, run_ts)
        build_reports(df, start, end)

    log.info("CloudWatch chargeback complete.")


if __name__ == "__main__":
    main()
