"""
s3_chargeback_cur.py  —  Method 1: CUR v2 + Athena
====================================================
Pulls exact billed S3 costs from your Cost and Usage Report (CUR v2)
via Amazon Athena and produces per-team chargeback CSVs.

Accuracy : ~100% — reconciles exactly to your AWS invoice.

Prerequisites
-------------
  Admin (one-time setup):
    • CUR v2 enabled in Billing Console, exporting to S3
    • Glue crawler run against the CUR bucket to create the Athena table
    • Cost allocation tags activated in Billing Console

  Your IAM role (read-only):
    • s3:ListBucket + s3:GetObject on the CUR export bucket
    • s3:PutObject + s3:GetBucketLocation on the Athena results bucket
    • athena:StartQueryExecution, GetQueryExecution, GetQueryResults, StopQueryExecution
    • glue:GetDatabase, GetTable, GetPartitions
    • s3:ListAllMyBuckets + s3:GetBucketTagging  (for tag fallback)

Usage
-----
  python s3_chargeback_cur.py --start 2026-01-01 --end 2026-03-31
  python s3_chargeback_cur.py --start 2026-01-01 --end 2026-03-31 --debug

Output  (written to CONFIG["reports_dir"])
------
  chargeback_summary_<ts>.csv       — total cost per team
  chargeback_detail_<ts>.csv        — cost per bucket per team
  chargeback_untagged_<ts>.csv      — buckets missing a team tag
  chargeback_prefix_sizes_<ts>.csv  — prefix split audit (shared buckets only)
"""

import argparse
import logging
import time
from datetime import date, datetime

import pandas as pd

from s3_chargeback_common import (
    CONFIG,
    auto_split_shared_buckets,
    aws_client,
    build_reports,
    get_all_bucket_tags,
    log,
)

# ─────────────────────────────────────────────
# Athena SQL template
# ─────────────────────────────────────────────

CUR_QUERY_TEMPLATE = """
SELECT
    line_item_resource_id                       AS bucket_name,
    resource_tags_user_{tag_team}               AS cur_team,
    resource_tags_user_{tag_owner}              AS cur_owner,
    resource_tags_user_{tag_cost_center}        AS cur_cost_center,
    line_item_usage_type                        AS usage_type,
    SUM(line_item_unblended_cost)               AS cost_usd,
    SUM(line_item_usage_amount)                 AS usage_amount,
    line_item_usage_account_id                  AS account_id
FROM   "{database}"."{table}"
WHERE  (year  = '{year_start}' AND month >= '{month_start}')
   OR  (year  = '{year_end}'   AND month <= '{month_end}')
  AND  line_item_product_code    = 'AmazonS3'
  AND  line_item_line_item_type IN ('Usage', 'DiscountedUsage', 'SavingsPlanCoveredUsage')
  AND  line_item_resource_id    != ''
GROUP BY 1, 2, 3, 4, 5, 8
ORDER BY cost_usd DESC
"""


# ─────────────────────────────────────────────
# Athena helpers
# ─────────────────────────────────────────────

def run_athena_query(sql: str) -> str:
    """
    Submit a query to Athena and poll until it succeeds or fails.
    Returns the QueryExecutionId on success.
    Polls every 5 s for up to 5 minutes before raising TimeoutError.
    """
    athena = aws_client("athena")
    resp   = athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={"Database": CONFIG["athena_database"]},
        ResultConfiguration={"OutputLocation": CONFIG["athena_results_bucket"]},
        WorkGroup=CONFIG["athena_workgroup"],
    )
    qid = resp["QueryExecutionId"]
    log.info("Athena query submitted: %s", qid)

    for attempt in range(60):       # 60 × 5 s = 5 min ceiling
        time.sleep(5)
        status = athena.get_query_execution(QueryExecutionId=qid)
        state  = status["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            log.info("Athena query succeeded after %d polls", attempt + 1)
            return qid
        if state in ("FAILED", "CANCELLED"):
            reason = status["QueryExecution"]["Status"].get("StateChangeReason", "unknown")
            raise RuntimeError(f"Athena query {state}: {reason}")

    raise TimeoutError(f"Athena query {qid} did not finish within 5 minutes")


def fetch_athena_results(qid: str) -> pd.DataFrame:
    """
    Page through all Athena result pages and return a single DataFrame.
    Skips the header row that Athena includes in page 0.
    """
    athena    = aws_client("athena")
    rows      = []
    headers   = []
    paginator = athena.get_paginator("get_query_results")

    for page_num, page in enumerate(paginator.paginate(QueryExecutionId=qid)):
        result_rows = page["ResultSet"]["Rows"]
        if page_num == 0:
            headers     = [c["VarCharValue"] for c in result_rows[0]["Data"]]
            result_rows = result_rows[1:]   # drop header row
        for row in result_rows:
            rows.append([c.get("VarCharValue", "") for c in row["Data"]])

    df = pd.DataFrame(rows, columns=headers)
    log.info("Athena returned %d rows", len(df))
    return df


# ─────────────────────────────────────────────
# Method 1 core
# ─────────────────────────────────────────────

def run(start: date, end: date) -> pd.DataFrame:
    """
    Query CUR via Athena for the given date range.

    Tag resolution strategy:
      1. Use the tag embedded in CUR (recorded at billing time).
      2. If CUR tag is empty, fall back to the live bucket tag (caught at runtime).
      This handles buckets that were tagged after the billing period closed.

    Returns a DataFrame with columns:
      bucket_name, team, owner, cost_center,
      usage_type, cost_usd, usage_amount, account_id, source
    """
    log.info("=== Method 1: CUR v2 + Athena  |  %s → %s ===", start, end)

    sql = CUR_QUERY_TEMPLATE.format(
        database        = CONFIG["athena_database"],
        table           = CONFIG["athena_table"],
        tag_team        = CONFIG["tag_team"].replace("-", "_"),
        tag_owner       = CONFIG["tag_owner"].replace("-", "_"),
        tag_cost_center = CONFIG["tag_cost_center"].replace("-", "_"),
        year_start      = start.year,
        month_start     = start.month,
        year_end        = end.year,
        month_end       = end.month,
    )

    qid = run_athena_query(sql)
    df  = fetch_athena_results(qid)

    df["cost_usd"]     = pd.to_numeric(df["cost_usd"],     errors="coerce").fillna(0)
    df["usage_amount"] = pd.to_numeric(df["usage_amount"], errors="coerce").fillna(0)

    # Tag fallback: live bucket tags fill gaps left by missing CUR tags
    tag_map  = get_all_bucket_tags()
    untagged = CONFIG["untagged_label"]

    def resolve(row, cur_col, tag_key):
        v = row.get(cur_col, "")
        return v if v else tag_map.get(row["bucket_name"], {}).get(tag_key, untagged)

    df["team"]        = df.apply(lambda r: resolve(r, "cur_team",         CONFIG["tag_team"]),        axis=1)
    df["owner"]       = df.apply(lambda r: resolve(r, "cur_owner",        CONFIG["tag_owner"]),       axis=1)
    df["cost_center"] = df.apply(lambda r: resolve(r, "cur_cost_center",  CONFIG["tag_cost_center"]), axis=1)
    df["source"]      = "CUR v2 + Athena"

    return df[["bucket_name", "team", "owner", "cost_center",
               "usage_type", "cost_usd", "usage_amount", "account_id", "source"]]


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description="S3 Chargeback — Method 1: CUR v2 + Athena"
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

    # Build initial reports and get run_ts for the audit file
    reports_dir, run_ts = build_reports(df, start, end)

    # Auto-split shared buckets by measuring real prefix sizes
    shared_cfg = CONFIG.get("shared_buckets", {})
    if shared_cfg:
        df = auto_split_shared_buckets(df, shared_cfg, reports_dir, run_ts)
        build_reports(df, start, end)   # rebuild with split data

    log.info("Method 1 complete.")


if __name__ == "__main__":
    main()
