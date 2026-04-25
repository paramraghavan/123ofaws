"""
s3_chargeback_common.py
=======================
Shared config, AWS helpers, tag resolution, shared-bucket auto-splitter,
and report builder used by both chargeback scripts.

Do not run this file directly — import it from:
  s3_chargeback_cur.py   (Method 1 — CUR v2 + Athena)
  s3_chargeback_lens.py  (Method 2 — S3 Storage Lens + Pricing API)
"""

import logging
from datetime import date, datetime
from pathlib import Path

import boto3
import pandas as pd
from botocore.exceptions import ClientError

# ─────────────────────────────────────────────
# CONFIGURATION — edit once, shared by both scripts
# ─────────────────────────────────────────────

CONFIG = {
    # AWS
    "region":  "us-east-1",
    "profile": None,              # named AWS profile, or None to use env/instance role

    # Method 1 — CUR v2 + Athena
    "athena_database":       "cur_database",
    "athena_table":          "cur_table",
    "athena_workgroup":      "primary",
    "athena_results_bucket": "s3://your-athena-results-bucket/results/",

    # Method 2 — S3 Storage Lens
    "lens_export_bucket": "your-lens-export-bucket",
    "lens_export_prefix": "storage-lens/",
    "lens_config_id":     "default-account-dashboard",

    # Tagging — keys used on your S3 buckets
    "tag_team":        "team",
    "tag_owner":       "owner",
    "tag_cost_center": "cost-center",
    "untagged_label":  "untagged",

    # Fallback S3 prices $/GB-month for us-east-1 (Method 2 uses Pricing API first)
    "prices_per_gb": {
        "StandardStorage":             0.023,
        "StandardIAStorage":           0.0125,
        "OneZoneIAStorage":            0.010,
        "ReducedRedundancyStorage":    0.023,
        "GlacierInstantStorage":       0.004,
        "GlacierStorage":              0.0036,
        "DeepArchiveStorage":          0.00099,
        "IntelligentTieringFAStorage": 0.023,
        "IntelligentTieringIAStorage": 0.0125,
    },

    # Shared buckets — declare bucket + team prefixes.
    # The pipeline measures actual prefix sizes via S3 list API
    # and splits the bucket cost proportionally. No manual GB numbers needed.
    #
    # Format: { "bucket-name": ["team-prefix/", "another-team/", ...] }
    # Prefixes must end with "/" to avoid partial name matches.
    #
    # Example:
    #   "my-platform-bucket": ["team-alpha/", "team-beta/", "team-gamma/"],
    #   "shared-ml-data":     ["data-science/", "engineering/"],
    "shared_buckets": {},

    # Output directory for CSV reports
    "reports_dir": "./reports",
}

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("s3-chargeback")


# ─────────────────────────────────────────────
# AWS session + client helpers
# ─────────────────────────────────────────────

def get_session() -> boto3.Session:
    profile = CONFIG["profile"]
    region  = CONFIG["region"]
    return (
        boto3.Session(profile_name=profile, region_name=region)
        if profile
        else boto3.Session(region_name=region)
    )


def aws_client(service: str):
    """Return a boto3 client for the given service using the configured session."""
    return get_session().client(service)


# ─────────────────────────────────────────────
# Tag helpers
# ─────────────────────────────────────────────

def get_all_bucket_tags() -> dict[str, dict]:
    """
    Return {bucket_name: {tag_key: tag_value}} for every bucket accessible
    to the caller. Buckets with no tag set are returned with an empty dict.
    Requires: s3:ListAllMyBuckets, s3:GetBucketTagging
    """
    s3      = aws_client("s3")
    tag_map: dict[str, dict] = {}

    try:
        buckets = s3.list_buckets().get("Buckets", [])
    except Exception as exc:
        log.error("Cannot list buckets: %s", exc)
        return tag_map

    for b in buckets:
        name = b["Name"]
        try:
            resp = s3.get_bucket_tagging(Bucket=name)
            tag_map[name] = {t["Key"]: t["Value"] for t in resp.get("TagSet", [])}
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            tag_map[name] = {}
            if code != "NoSuchTagSet":
                log.warning("Cannot read tags for %s: %s", name, code)

    log.info("Fetched tags for %d buckets", len(tag_map))
    return tag_map


def enrich_with_tags(df: pd.DataFrame, tag_map: dict) -> pd.DataFrame:
    """
    Add team / owner / cost_center columns to df by joining on bucket_name.
    Buckets missing from tag_map are labelled with CONFIG["untagged_label"].
    """
    untagged = CONFIG["untagged_label"]
    for col, key in [
        ("team",        CONFIG["tag_team"]),
        ("owner",       CONFIG["tag_owner"]),
        ("cost_center", CONFIG["tag_cost_center"]),
    ]:
        df[col] = df["bucket_name"].map(
            lambda b, k=key: tag_map.get(b, {}).get(k, untagged)
        )
    return df


# ─────────────────────────────────────────────
# Shared bucket splitter
# ─────────────────────────────────────────────

def measure_prefix_sizes_gb(bucket: str, prefixes: list[str]) -> dict[str, float]:
    """
    For each prefix, paginate s3:ListObjectsV2 and sum object sizes.
    Returns {prefix: size_in_gb}.
    Logs progress every 100 pages (~100 000 objects) so long scans are visible.
    Requires: s3:ListBucket on the bucket.
    """
    s3    = aws_client("s3")
    sizes: dict[str, float] = {}

    for prefix in prefixes:
        total_bytes = 0
        page_count  = 0
        paginator   = s3.get_paginator("list_objects_v2")
        log.info("Measuring s3://%s/%s …", bucket, prefix)
        try:
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                for obj in page.get("Contents", []):
                    total_bytes += obj["Size"]
                page_count += 1
                if page_count % 100 == 0:
                    log.info(
                        "  … %d pages scanned, %.2f GB so far (prefix=%s)",
                        page_count, total_bytes / (1024 ** 3), prefix,
                    )
        except Exception as exc:
            log.warning("Could not list s3://%s/%s: %s", bucket, prefix, exc)
            total_bytes = 0

        gb = total_bytes / (1024 ** 3)
        sizes[prefix] = gb
        log.info("  s3://%s/%s  →  %.4f GB", bucket, prefix, gb)

    return sizes


def auto_split_shared_buckets(
    df: pd.DataFrame,
    shared_buckets_cfg: dict[str, list[str]],
    reports_dir: Path,
    run_ts: str,
) -> pd.DataFrame:
    """
    For every bucket in shared_buckets_cfg:
      1. Measure the actual byte size of each team prefix via S3 list API.
      2. Compute each team's fraction of total prefix bytes.
      3. Replace the bucket's single cost row with one row per team,
         each carrying its proportional share of cost and usage.

    Also writes ./reports/chargeback_prefix_sizes_<run_ts>.csv as an audit trail.

    shared_buckets_cfg comes from CONFIG["shared_buckets"]:
        {
            "my-platform-bucket": ["team-alpha/", "team-beta/", "team-gamma/"],
            "shared-ml-data":     ["data-science/", "engineering/"],
        }
    """
    if not shared_buckets_cfg:
        return df

    all_prefix_rows: list[dict] = []
    new_rows:        list        = []
    drop_idx:        list        = []

    for bucket, prefixes in shared_buckets_cfg.items():
        prefix_sizes_gb = measure_prefix_sizes_gb(bucket, prefixes)
        total_gb        = sum(prefix_sizes_gb.values())

        for prefix, gb in prefix_sizes_gb.items():
            all_prefix_rows.append({
                "bucket":       bucket,
                "prefix":       prefix,
                "team":         prefix.rstrip("/"),
                "size_gb":      round(gb, 4),
                "fraction_pct": round((gb / total_gb * 100) if total_gb else 0, 2),
            })

        bucket_rows = df[df["bucket_name"] == bucket]
        if bucket_rows.empty:
            log.warning("Shared bucket '%s' not found in cost data — skipping", bucket)
            continue

        drop_idx.extend(bucket_rows.index.tolist())

        for _, row in bucket_rows.iterrows():
            for prefix, gb in prefix_sizes_gb.items():
                fraction               = (gb / total_gb) if total_gb else 0
                new_row                = row.copy()
                new_row["team"]        = prefix.rstrip("/")
                new_row["cost_usd"]    = row["cost_usd"]   * fraction
                new_row["usage_amount"]= row["usage_amount"] * fraction
                new_rows.append(new_row)

        log.info(
            "Split '%s' across %d prefixes (total %.2f GB)",
            bucket, len(prefixes), total_gb,
        )

    if drop_idx:
        df = df.drop(index=drop_idx)
    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)

    if all_prefix_rows:
        audit_path = reports_dir / f"chargeback_prefix_sizes_{run_ts}.csv"
        pd.DataFrame(all_prefix_rows).to_csv(audit_path, index=False)
        log.info("Prefix sizes audit → %s", audit_path)

    return df


# ─────────────────────────────────────────────
# Report builder  (shared by both methods)
# ─────────────────────────────────────────────

def build_reports(df: pd.DataFrame, start: date, end: date) -> tuple[Path, str]:
    """
    Write three CSV reports and print a console summary table.

    Reports written:
      chargeback_summary_<ts>.csv  — total cost per team
      chargeback_detail_<ts>.csv   — cost per bucket per team
      chargeback_untagged_<ts>.csv — buckets with no team tag (if any)

    Returns (reports_dir, run_ts) so callers can pass run_ts to
    auto_split_shared_buckets for the prefix-sizes audit file.
    """
    reports_dir = Path(CONFIG["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)
    run_ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    period   = f"{start.strftime('%b %Y')} – {end.strftime('%b %Y')}"
    untagged = CONFIG["untagged_label"]

    # ── 1. Summary per team ───────────────────────────────────
    summary = (
        df
        .groupby(["team", "cost_center"])
        .agg(
            total_cost_usd  =("cost_usd",      "sum"),
            bucket_count    =("bucket_name",    "nunique"),
            usage_amount_gb =("usage_amount",   "sum"),
        )
        .reset_index()
        .sort_values("total_cost_usd", ascending=False)
    )
    summary["total_cost_usd"]  = summary["total_cost_usd"].round(4)
    summary["usage_amount_gb"] = summary["usage_amount_gb"].round(2)
    summary["period"]          = period

    summary_path = reports_dir / f"chargeback_summary_{run_ts}.csv"
    summary.to_csv(summary_path, index=False)
    log.info("Summary report   → %s", summary_path)

    # ── 2. Detail per bucket ──────────────────────────────────
    detail = (
        df
        .groupby(["team", "cost_center", "owner", "bucket_name", "source"])
        .agg(
            cost_usd        =("cost_usd",     "sum"),
            usage_amount_gb =("usage_amount", "sum"),
        )
        .reset_index()
        .sort_values(["team", "cost_usd"], ascending=[True, False])
    )
    detail["cost_usd"]        = detail["cost_usd"].round(4)
    detail["usage_amount_gb"] = detail["usage_amount_gb"].round(2)
    detail["period"]          = period

    detail_path = reports_dir / f"chargeback_detail_{run_ts}.csv"
    detail.to_csv(detail_path, index=False)
    log.info("Detail report    → %s", detail_path)

    # ── 3. Untagged buckets ───────────────────────────────────
    untagged_df = df[df["team"] == untagged].copy()
    if not untagged_df.empty:
        untagged_path = reports_dir / f"chargeback_untagged_{run_ts}.csv"
        untagged_df.to_csv(untagged_path, index=False)
        log.warning(
            "Untagged report  → %s  (%d buckets, $%.2f unattributed)",
            untagged_path,
            untagged_df["bucket_name"].nunique(),
            untagged_df["cost_usd"].sum(),
        )
    else:
        log.info("No untagged buckets — full attribution achieved.")

    # ── Console summary table ─────────────────────────────────
    print("\n" + "=" * 62)
    print(f"  S3 Chargeback Summary  |  {period}")
    print("=" * 62)
    print(f"  {'Team':<28}  {'Cost (USD)':>12}  {'Buckets':>8}")
    print("  " + "-" * 58)
    for _, row in summary.iterrows():
        print(f"  {row['team']:<28}  ${row['total_cost_usd']:>11.4f}  {int(row['bucket_count']):>8}")
    print("  " + "-" * 58)
    print(f"  {'TOTAL':<28}  ${summary['total_cost_usd'].sum():>11.4f}")
    print("=" * 62 + "\n")

    return reports_dir, run_ts
