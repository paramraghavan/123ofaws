"""
s3_chargeback_lens.py  —  Method 2: S3 Storage Lens + Pricing API
=================================================================
Estimates S3 storage costs from Storage Lens daily export files,
priced using the AWS Pricing API, and produces per-team chargeback CSVs.

Use this when CUR v2 is not available or not yet set up.

Accuracy : ~90–95% — covers storage charges only; request and data-transfer
           costs (~5–10% of a typical S3 bill) are excluded.

Prerequisites
-------------
  Admin (one-time setup):
    • S3 Storage Lens dashboard configured with daily export to S3
    • Export bucket with a known prefix (set in CONFIG)

  Your IAM role (read-only):
    • s3:ListStorageLensConfigurations + s3:GetStorageLensConfiguration
    • s3:ListBucket + s3:GetObject on the Lens export bucket
    • s3:ListAllMyBuckets + s3:GetBucketTagging  (for tag attribution)
    • pricing:GetProducts + pricing:DescribeServices  (Pricing API, us-east-1)

Usage
-----
  python s3_chargeback_lens.py --start 2026-01-01 --end 2026-03-31
  python s3_chargeback_lens.py --start 2026-01-01 --end 2026-03-31 --debug

Output  (written to CONFIG["reports_dir"])
------
  chargeback_summary_<ts>.csv       — total cost per team
  chargeback_detail_<ts>.csv        — cost per bucket per team
  chargeback_untagged_<ts>.csv      — buckets missing a team tag
  chargeback_prefix_sizes_<ts>.csv  — prefix split audit (shared buckets only)
"""

import argparse
import io
import json
import logging
from datetime import date, datetime

import pandas as pd

from s3_chargeback_common import (
    CONFIG,
    auto_split_shared_buckets,
    aws_client,
    build_reports,
    enrich_with_tags,
    get_all_bucket_tags,
    log,
)


# ─────────────────────────────────────────────
# Pricing API
# ─────────────────────────────────────────────

def fetch_pricing_from_api() -> dict[str, float]:
    """
    Pull current S3 storage class prices from the AWS Pricing API.
    Returns {storageClass: $/GB-month} for us-east-1.

    The Pricing API endpoint is always in us-east-1 regardless of your region.
    Falls back to CONFIG["prices_per_gb"] if the API call fails.
    """
    try:
        # Pricing API is always us-east-1
        pricing   = aws_client.__func__.__globals__["get_session"]().client(
            "pricing", region_name="us-east-1"
        ) if False else __import__("boto3").Session(
            profile_name=CONFIG["profile"], region_name="us-east-1"
        ).client("pricing") if CONFIG["profile"] else __import__("boto3").client(
            "pricing", region_name="us-east-1"
        )

        prices    = {}
        paginator = pricing.get_paginator("get_products")

        for page in paginator.paginate(
            ServiceCode="AmazonS3",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "location",     "Value": "US East (N. Virginia)"},
                {"Type": "TERM_MATCH", "Field": "productFamily","Value": "Storage"},
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
            log.info("Pricing API returned %d storage class prices", len(prices))
            return prices

    except Exception as exc:
        log.warning("Pricing API call failed (%s) — using hardcoded fallback prices", exc)

    return CONFIG["prices_per_gb"]


def _pricing_client():
    """Return a Pricing API client always pointed at us-east-1."""
    import boto3
    session = (
        boto3.Session(profile_name=CONFIG["profile"], region_name="us-east-1")
        if CONFIG["profile"]
        else boto3.Session(region_name="us-east-1")
    )
    return session.client("pricing")


def fetch_pricing_from_api() -> dict[str, float]:   # noqa: F811 — redefine cleanly
    """
    Pull current S3 storage class prices from the AWS Pricing API.
    Returns {storageClass: $/GB-month} for us-east-1.
    Falls back to CONFIG["prices_per_gb"] on any error.
    """
    try:
        pricing   = _pricing_client()
        prices    = {}
        paginator = pricing.get_paginator("get_products")

        for page in paginator.paginate(
            ServiceCode="AmazonS3",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "location",     "Value": "US East (N. Virginia)"},
                {"Type": "TERM_MATCH", "Field": "productFamily","Value": "Storage"},
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
            log.info("Pricing API returned %d storage class prices", len(prices))
            return prices

    except Exception as exc:
        log.warning("Pricing API call failed (%s) — using hardcoded fallback prices", exc)

    return CONFIG["prices_per_gb"]


# ─────────────────────────────────────────────
# Storage Lens export reader
# ─────────────────────────────────────────────

def fetch_lens_exports(start: date, end: date) -> pd.DataFrame:
    """
    Read Storage Lens daily export CSV files from S3 for every day in [start, end].
    Export files are expected at:
      s3://<lens_export_bucket>/<lens_export_prefix><YYYY-MM-DD>/*.csv

    Returns a raw concatenated DataFrame of all export rows.
    Days with no export files are silently skipped with a warning.
    """
    s3      = aws_client("s3")
    bucket  = CONFIG["lens_export_bucket"]
    prefix  = CONFIG["lens_export_prefix"]
    frames  = []
    current = start

    while current <= end:
        date_prefix = f"{prefix}{current.strftime('%Y-%m-%d')}/"
        try:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=date_prefix)
            for obj in resp.get("Contents", []):
                key = obj["Key"]
                if not key.endswith(".csv"):
                    continue
                log.debug("Reading lens export: s3://%s/%s", bucket, key)
                body = s3.get_object(Bucket=bucket, Key=key)["Body"].read()
                frames.append(pd.read_csv(io.BytesIO(body), dtype=str, on_bad_lines="skip"))
        except Exception as exc:
            log.warning("Could not read lens export for %s: %s", current, exc)

        current = date.fromordinal(current.toordinal() + 1)

    if not frames:
        log.warning("No Storage Lens export files found in s3://%s/%s", bucket, prefix)
        return pd.DataFrame()

    raw = pd.concat(frames, ignore_index=True)
    log.info("Storage Lens: loaded %d rows from %d daily files", len(raw), len(frames))
    return raw


def _normalise_lens_columns(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Normalise column names and resolve alternative column name variants
    produced by different Storage Lens export versions.
    """
    raw.columns = [c.strip().lower().replace(" ", "_") for c in raw.columns]

    # Average storage bytes may appear under different names across export versions
    alt_names = {
        "average_storage_bytes": [
            "average_storage_size_bytes",
            "averagestoragebytes",
            "avg_storage_bytes",
        ]
    }
    for canonical, alternatives in alt_names.items():
        if canonical not in raw.columns:
            for alt in alternatives:
                if alt in raw.columns:
                    raw = raw.rename(columns={alt: canonical})
                    break

    return raw


# ─────────────────────────────────────────────
# Method 2 core
# ─────────────────────────────────────────────

def run(start: date, end: date) -> pd.DataFrame:
    """
    Estimate S3 costs from Storage Lens export data + AWS Pricing API.

    Steps:
      1. Fetch current S3 prices per storage class from the Pricing API.
      2. Read daily Storage Lens export CSVs from S3 for [start, end].
      3. Average daily storage bytes per bucket per storage class.
      4. Multiply: avg_gb × price_per_gb × months_in_range = cost estimate.
      5. Enrich each bucket row with team/owner/cost-center tags.

    Returns a DataFrame with the same schema as s3_chargeback_cur.run():
      bucket_name, team, owner, cost_center,
      usage_type, cost_usd, usage_amount, account_id, source
    """
    log.info("=== Method 2: S3 Storage Lens + Pricing API  |  %s → %s ===", start, end)

    prices = fetch_pricing_from_api()
    raw    = fetch_lens_exports(start, end)

    if raw.empty:
        log.error("Storage Lens returned no data — cannot produce estimates")
        return pd.DataFrame()

    raw = _normalise_lens_columns(raw)

    if "average_storage_bytes" not in raw.columns:
        log.error(
            "Cannot find storage bytes column in lens export. "
            "Available columns: %s", list(raw.columns)
        )
        return pd.DataFrame()

    raw["average_storage_bytes"] = (
        pd.to_numeric(raw["average_storage_bytes"], errors="coerce").fillna(0)
    )

    # Average across all days in the range, then convert bytes → GB
    agg = (
        raw
        .groupby(["bucket_name", "storage_class"], as_index=False)["average_storage_bytes"]
        .mean()
    )
    agg["avg_gb"] = agg["average_storage_bytes"] / (1024 ** 3)

    # Number of full calendar months in [start, end] (inclusive)
    months = (end.year - start.year) * 12 + (end.month - start.month) + 1

    agg["cost_usd"] = agg.apply(
        lambda r: r["avg_gb"] * prices.get(r["storage_class"],
                                           prices.get("StandardStorage", 0.023)) * months,
        axis=1,
    )
    agg["usage_amount"] = agg["avg_gb"] * months
    agg["usage_type"]   = agg["storage_class"]
    agg["account_id"]   = ""
    agg["source"]       = "Storage Lens + Pricing API"

    tag_map = get_all_bucket_tags()
    agg     = enrich_with_tags(agg, tag_map)

    return agg[["bucket_name", "team", "owner", "cost_center",
                "usage_type", "cost_usd", "usage_amount", "account_id", "source"]]


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="S3 Chargeback — Method 2: S3 Storage Lens + Pricing API"
    )
    parser.add_argument("--start", default="2026-01-01",
                        help="Start date YYYY-MM-DD (default: 2026-01-01)")
    parser.add_argument("--end",   default="2026-03-31",
                        help="End date YYYY-MM-DD (default: 2026-03-31)")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    return parser.parse_args()


def main():
    args  = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    start = datetime.strptime(args.start, "%Y-%m-%d").date()
    end   = datetime.strptime(args.end,   "%Y-%m-%d").date()
    if start > end:
        raise ValueError(f"--start {start} must be before --end {end}")

    df = run(start, end)
    if df.empty:
        log.error("No data produced — check Storage Lens export bucket and prefix in CONFIG.")
        return

    reports_dir, run_ts = build_reports(df, start, end)

    shared_cfg = CONFIG.get("shared_buckets", {})
    if shared_cfg:
        df = auto_split_shared_buckets(df, shared_cfg, reports_dir, run_ts)
        build_reports(df, start, end)

    log.info("Method 2 complete.")


if __name__ == "__main__":
    main()
