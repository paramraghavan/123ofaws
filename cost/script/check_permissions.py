"""
S3 Chargeback — Permission Checker
====================================
Verifies that your current IAM role has all permissions required
for Method 1 (CUR v2 + Athena) and Method 2 (S3 Storage Lens + Pricing API).

Each check makes a real lightweight API call — no data is modified.
Results are printed as a colour-coded table and saved to
  ./reports/permission_check_<timestamp>.csv

Usage:
  python check_permissions.py                      # check both methods
  python check_permissions.py --method cur         # Method 1 only
  python check_permissions.py --method lens        # Method 2 only
  python check_permissions.py --profile my-profile # use a named AWS profile

Requirements:
  pip install boto3 pandas
"""

import argparse
import csv
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

# ─────────────────────────────────────────────
# CONFIG — set these to match your environment
# ─────────────────────────────────────────────

CONFIG = {
    "region":                "us-east-1",
    "profile":               None,           # or e.g. "my-aws-profile"

    # Method 1 — CUR + Athena
    "cur_bucket":            "your-cur-export-bucket",
    "athena_results_bucket": "your-athena-results-bucket",
    "athena_database":       "cur_database",
    "athena_table":          "cur_table",
    "athena_workgroup":      "primary",

    # Method 2 — Storage Lens
    "lens_export_bucket":    "your-lens-export-bucket",
    "lens_config_id":        "default-account-dashboard",
}

# ─────────────────────────────────────────────
# Colours (ANSI — disabled on Windows if needed)
# ─────────────────────────────────────────────

USE_COLOUR = os.name != "nt"

GREEN  = "\033[92m" if USE_COLOUR else ""
RED    = "\033[91m" if USE_COLOUR else ""
YELLOW = "\033[93m" if USE_COLOUR else ""
BOLD   = "\033[1m"  if USE_COLOUR else ""
RESET  = "\033[0m"  if USE_COLOUR else ""

OK      = f"{GREEN}PASS{RESET}"
FAIL    = f"{RED}FAIL{RESET}"
WARN    = f"{YELLOW}WARN{RESET}"

# ─────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────

@dataclass
class CheckResult:
    method:      str
    service:     str
    permission:  str
    status:      str          # PASS | FAIL | WARN
    detail:      str = ""
    required:    bool = True  # False = optional but recommended


# ─────────────────────────────────────────────
# Session
# ─────────────────────────────────────────────

def get_session(profile: str | None) -> boto3.Session:
    try:
        if profile:
            return boto3.Session(profile_name=profile, region_name=CONFIG["region"])
        return boto3.Session(region_name=CONFIG["region"])
    except ProfileNotFound:
        print(f"{RED}ERROR: AWS profile '{profile}' not found.{RESET}")
        raise


def whoami(session: boto3.Session) -> str:
    """Return the ARN of the current caller for display purposes."""
    try:
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        return identity["Arn"]
    except Exception:
        return "unknown (STS call failed)"


# ─────────────────────────────────────────────
# Generic error classifier
# ─────────────────────────────────────────────

def classify_error(exc: ClientError) -> tuple[str, str]:
    """Return (status, detail) from a ClientError."""
    code = exc.response["Error"]["Code"]
    msg  = exc.response["Error"]["Message"]
    if code in ("AccessDenied", "AccessDeniedException",
                "AuthorizationError", "UnauthorizedAccess",
                "403", "InvalidClientTokenId"):
        return "FAIL", f"Access denied ({code})"
    if code in ("NoSuchBucket", "NoSuchKey", "ResourceNotFoundException",
                "EntityNotFoundException", "NotFoundException"):
        return "WARN", f"Resource not found ({code}) — check CONFIG values"
    return "WARN", f"{code}: {msg[:80]}"


# ═══════════════════════════════════════════════════════════════
# METHOD 1 CHECKS — CUR v2 + Athena
# ═══════════════════════════════════════════════════════════════

def check_cur_bucket_read(session: boto3.Session) -> CheckResult:
    """s3:ListBucket on the CUR export bucket."""
    s3     = session.client("s3")
    bucket = CONFIG["cur_bucket"]
    try:
        s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        return CheckResult("Method 1", "S3", "s3:ListBucket (CUR bucket)",
                           "PASS", f"Listed objects in {bucket}")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 1", "S3", "s3:ListBucket (CUR bucket)",
                           status, detail)


def check_cur_bucket_get(session: boto3.Session) -> CheckResult:
    """s3:GetObject on the CUR export bucket (reads first available file)."""
    s3     = session.client("s3")
    bucket = CONFIG["cur_bucket"]
    try:
        resp = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        contents = resp.get("Contents", [])
        if not contents:
            return CheckResult("Method 1", "S3", "s3:GetObject (CUR bucket)",
                               "WARN", "Bucket is empty — cannot test GetObject")
        key = contents[0]["Key"]
        s3.get_object(Bucket=bucket, Key=key, Range="bytes=0-0")
        return CheckResult("Method 1", "S3", "s3:GetObject (CUR bucket)",
                           "PASS", f"Read 1 byte from {key}")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 1", "S3", "s3:GetObject (CUR bucket)",
                           status, detail)


def check_athena_results_put(session: boto3.Session) -> CheckResult:
    """s3:PutObject on the Athena results bucket (needed to write query output)."""
    s3      = session.client("s3")
    bucket  = CONFIG["athena_results_bucket"]
    key     = "permission-check/probe.txt"
    try:
        s3.put_object(Bucket=bucket, Key=key, Body=b"probe")
        s3.delete_object(Bucket=bucket, Key=key)   # clean up
        return CheckResult("Method 1", "S3", "s3:PutObject (Athena results bucket)",
                           "PASS", f"Wrote and deleted probe object in {bucket}")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 1", "S3", "s3:PutObject (Athena results bucket)",
                           status, detail)


def check_athena_start_query(session: boto3.Session) -> CheckResult:
    """athena:StartQueryExecution — run a cheap no-op query."""
    athena = session.client("athena")
    try:
        resp = athena.start_query_execution(
            QueryString="SELECT 1",
            ResultConfiguration={
                "OutputLocation": f"s3://{CONFIG['athena_results_bucket']}/permission-check/"
            },
            WorkGroup=CONFIG["athena_workgroup"],
        )
        qid = resp["QueryExecutionId"]
        # cancel it immediately so we don't burn Athena credits
        try:
            athena.stop_query_execution(QueryExecutionId=qid)
        except Exception:
            pass
        return CheckResult("Method 1", "Athena", "athena:StartQueryExecution",
                           "PASS", f"Started and stopped query {qid[:8]}…")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 1", "Athena", "athena:StartQueryExecution",
                           status, detail)


def check_athena_get_execution(session: boto3.Session) -> CheckResult:
    """athena:GetQueryExecution — requires a real execution ID; we use a dummy."""
    athena = session.client("athena")
    dummy  = "00000000-0000-0000-0000-000000000000"
    try:
        athena.get_query_execution(QueryExecutionId=dummy)
        return CheckResult("Method 1", "Athena", "athena:GetQueryExecution",
                           "PASS", "")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        # InvalidRequestException means the call reached Athena and the dummy ID
        # was rejected — that's actually a PASS (we have permission)
        if code in ("InvalidRequestException", "InvalidExecutionIdException"):
            return CheckResult("Method 1", "Athena", "athena:GetQueryExecution",
                               "PASS", "Permission confirmed (dummy ID rejected as expected)")
        status, detail = classify_error(e)
        return CheckResult("Method 1", "Athena", "athena:GetQueryExecution",
                           status, detail)


def check_athena_get_results(session: boto3.Session) -> CheckResult:
    """athena:GetQueryResults — same dummy-ID approach."""
    athena = session.client("athena")
    dummy  = "00000000-0000-0000-0000-000000000000"
    try:
        athena.get_query_results(QueryExecutionId=dummy)
        return CheckResult("Method 1", "Athena", "athena:GetQueryResults",
                           "PASS", "")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("InvalidRequestException", "InvalidExecutionIdException"):
            return CheckResult("Method 1", "Athena", "athena:GetQueryResults",
                               "PASS", "Permission confirmed (dummy ID rejected as expected)")
        status, detail = classify_error(e)
        return CheckResult("Method 1", "Athena", "athena:GetQueryResults",
                           status, detail)


def check_glue_get_database(session: boto3.Session) -> CheckResult:
    """glue:GetDatabase — reads the Glue catalog DB that holds the CUR table."""
    glue = session.client("glue")
    db   = CONFIG["athena_database"]
    try:
        glue.get_database(Name=db)
        return CheckResult("Method 1", "Glue", "glue:GetDatabase",
                           "PASS", f"Found database '{db}'")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 1", "Glue", "glue:GetDatabase",
                           status, detail)


def check_glue_get_table(session: boto3.Session) -> CheckResult:
    """glue:GetTable — reads the CUR table schema."""
    glue  = session.client("glue")
    db    = CONFIG["athena_database"]
    table = CONFIG["athena_table"]
    try:
        glue.get_table(DatabaseName=db, Name=table)
        return CheckResult("Method 1", "Glue", "glue:GetTable",
                           "PASS", f"Found table '{db}.{table}'")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 1", "Glue", "glue:GetTable",
                           status, detail)


def check_glue_get_partitions(session: boto3.Session) -> CheckResult:
    """glue:GetPartitions — needed for efficient month-by-month CUR queries."""
    glue  = session.client("glue")
    db    = CONFIG["athena_database"]
    table = CONFIG["athena_table"]
    try:
        glue.get_partitions(DatabaseName=db, TableName=table, MaxResults=1)
        return CheckResult("Method 1", "Glue", "glue:GetPartitions",
                           "PASS", "Retrieved partition metadata")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "EntityNotFoundException":
            return CheckResult("Method 1", "Glue", "glue:GetPartitions",
                               "WARN", "Table not found — run Glue crawler first")
        status, detail = classify_error(e)
        return CheckResult("Method 1", "Glue", "glue:GetPartitions",
                           status, detail)


# ═══════════════════════════════════════════════════════════════
# METHOD 2 CHECKS — Storage Lens + Pricing API
# ═══════════════════════════════════════════════════════════════

def check_lens_list_configs(session: boto3.Session) -> CheckResult:
    """s3:ListStorageLensConfigurations — enumerate available dashboards."""
    s3control = session.client("s3control")
    sts       = session.client("sts")
    account   = sts.get_caller_identity()["Account"]
    try:
        s3control.list_storage_lens_configurations(AccountId=account)
        return CheckResult("Method 2", "S3 Control", "s3:ListStorageLensConfigurations",
                           "PASS", "Listed Storage Lens configurations")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "S3 Control", "s3:ListStorageLensConfigurations",
                           status, detail)


def check_lens_get_config(session: boto3.Session) -> CheckResult:
    """s3:GetStorageLensConfiguration — read a specific dashboard config."""
    s3control = session.client("s3control")
    sts       = session.client("sts")
    account   = sts.get_caller_identity()["Account"]
    config_id = CONFIG["lens_config_id"]
    try:
        s3control.get_storage_lens_configuration(
            ConfigId=config_id, AccountId=account
        )
        return CheckResult("Method 2", "S3 Control", "s3:GetStorageLensConfiguration",
                           "PASS", f"Read config '{config_id}'")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "NoSuchConfiguration":
            return CheckResult("Method 2", "S3 Control", "s3:GetStorageLensConfiguration",
                               "WARN", f"Config '{config_id}' not found — check CONFIG['lens_config_id']")
        status, detail = classify_error(e)
        return CheckResult("Method 2", "S3 Control", "s3:GetStorageLensConfiguration",
                           status, detail)


def check_lens_export_read(session: boto3.Session) -> CheckResult:
    """s3:GetObject on the Storage Lens export bucket."""
    s3     = session.client("s3")
    bucket = CONFIG["lens_export_bucket"]
    try:
        resp     = s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        contents = resp.get("Contents", [])
        if not contents:
            return CheckResult("Method 2", "S3", "s3:GetObject (Lens export bucket)",
                               "WARN", "Export bucket is empty — exports may not be configured yet")
        key = contents[0]["Key"]
        s3.get_object(Bucket=bucket, Key=key, Range="bytes=0-0")
        return CheckResult("Method 2", "S3", "s3:GetObject (Lens export bucket)",
                           "PASS", f"Read from {bucket}/{key[:40]}…")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "S3", "s3:GetObject (Lens export bucket)",
                           status, detail)


def check_lens_export_list(session: boto3.Session) -> CheckResult:
    """s3:ListBucket on the Storage Lens export bucket."""
    s3     = session.client("s3")
    bucket = CONFIG["lens_export_bucket"]
    try:
        s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
        return CheckResult("Method 2", "S3", "s3:ListBucket (Lens export bucket)",
                           "PASS", f"Listed objects in {bucket}")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "S3", "s3:ListBucket (Lens export bucket)",
                           status, detail)


def check_bucket_tagging(session: boto3.Session) -> CheckResult:
    """s3:GetBucketTagging — reads tags from the first available bucket."""
    s3 = session.client("s3")
    try:
        buckets = s3.list_buckets().get("Buckets", [])
        if not buckets:
            return CheckResult("Method 2", "S3", "s3:GetBucketTagging",
                               "WARN", "No buckets found in this account")
        bucket = buckets[0]["Name"]
        try:
            s3.get_bucket_tagging(Bucket=bucket)
            return CheckResult("Method 2", "S3", "s3:GetBucketTagging",
                               "PASS", f"Read tags from '{bucket}'")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "NoSuchTagSet":
                return CheckResult("Method 2", "S3", "s3:GetBucketTagging",
                                   "PASS", f"Permission confirmed ('{bucket}' has no tags)")
            status, detail = classify_error(e)
            return CheckResult("Method 2", "S3", "s3:GetBucketTagging",
                               status, detail)
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "S3", "s3:GetBucketTagging",
                           status, detail)


def check_list_all_buckets(session: boto3.Session) -> CheckResult:
    """s3:ListAllMyBuckets — list all buckets in the account."""
    s3 = session.client("s3")
    try:
        resp  = s3.list_buckets()
        count = len(resp.get("Buckets", []))
        return CheckResult("Method 2", "S3", "s3:ListAllMyBuckets",
                           "PASS", f"Found {count} buckets")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "S3", "s3:ListAllMyBuckets",
                           status, detail)


def check_pricing_api(session: boto3.Session) -> CheckResult:
    """pricing:GetProducts — fetches one S3 price from the Pricing API."""
    # Pricing API is always in us-east-1 regardless of your region
    pricing = session.client("pricing", region_name="us-east-1")
    try:
        resp = pricing.get_products(
            ServiceCode="AmazonS3",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "location",     "Value": "US East (N. Virginia)"},
                {"Type": "TERM_MATCH", "Field": "storageClass", "Value": "General Purpose"},
            ],
            MaxResults=1,
        )
        count = len(resp.get("PriceList", []))
        return CheckResult("Method 2", "Pricing", "pricing:GetProducts",
                           "PASS", f"Retrieved {count} price record(s)")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "Pricing", "pricing:GetProducts",
                           status, detail)


def check_pricing_describe(session: boto3.Session) -> CheckResult:
    """pricing:DescribeServices — verifies access to the Pricing service."""
    pricing = session.client("pricing", region_name="us-east-1")
    try:
        pricing.describe_services(ServiceCode="AmazonS3", MaxResults=1)
        return CheckResult("Method 2", "Pricing", "pricing:DescribeServices",
                           "PASS", "AmazonS3 service described")
    except ClientError as e:
        status, detail = classify_error(e)
        return CheckResult("Method 2", "Pricing", "pricing:DescribeServices",
                           status, detail)


# ═══════════════════════════════════════════════════════════════
# RUNNER + REPORTER
# ═══════════════════════════════════════════════════════════════

METHOD1_CHECKS = [
    check_cur_bucket_read,
    check_cur_bucket_get,
    check_athena_results_put,
    check_athena_start_query,
    check_athena_get_execution,
    check_athena_get_results,
    check_glue_get_database,
    check_glue_get_table,
    check_glue_get_partitions,
]

METHOD2_CHECKS = [
    check_list_all_buckets,
    check_bucket_tagging,
    check_lens_list_configs,
    check_lens_get_config,
    check_lens_export_list,
    check_lens_export_read,
    check_pricing_describe,
    check_pricing_api,
]


def run_checks(checks: list, session: boto3.Session) -> list[CheckResult]:
    results = []
    for fn in checks:
        label = fn.__doc__.split("—")[0].strip() if fn.__doc__ else fn.__name__
        print(f"  Checking {label:<55}", end="", flush=True)
        try:
            result = fn(session)
        except Exception as exc:
            result = CheckResult(
                "?", "?", fn.__name__, "FAIL",
                f"Unexpected error: {str(exc)[:80]}"
            )
        symbol = {"PASS": OK, "FAIL": FAIL, "WARN": WARN}.get(result.status, WARN)
        print(f"  {symbol}  {result.detail}")
        results.append(result)
    return results


def print_section(title: str) -> None:
    print(f"\n{BOLD}{'─' * 64}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─' * 64}{RESET}")


def print_summary(results: list[CheckResult]) -> None:
    passed  = sum(1 for r in results if r.status == "PASS")
    failed  = sum(1 for r in results if r.status == "FAIL")
    warned  = sum(1 for r in results if r.status == "WARN")
    total   = len(results)

    print(f"\n{BOLD}{'═' * 64}{RESET}")
    print(f"{BOLD}  SUMMARY{RESET}")
    print(f"{BOLD}{'═' * 64}{RESET}")
    print(f"  {GREEN}PASS{RESET}  {passed}/{total}")
    print(f"  {RED}FAIL{RESET}  {failed}/{total}  ← permissions you need to request")
    print(f"  {YELLOW}WARN{RESET}  {warned}/{total}  ← resource not found or partially configured")

    if failed:
        print(f"\n{BOLD}  Permissions to add to your IAM role:{RESET}")
        for r in results:
            if r.status == "FAIL":
                print(f"  {RED}✗{RESET}  [{r.method}] {r.service} — {r.permission}")

    if warned:
        print(f"\n{BOLD}  Items needing attention:{RESET}")
        for r in results:
            if r.status == "WARN":
                print(f"  {YELLOW}!{RESET}  [{r.method}] {r.service} — {r.permission}")
                if r.detail:
                    print(f"      {r.detail}")
    print()


def save_csv(results: list[CheckResult]) -> None:
    Path("./reports").mkdir(exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"./reports/permission_check_{ts}.csv"
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["method", "service", "permission",
                                                "status", "detail", "required"])
        writer.writeheader()
        for r in results:
            writer.writerow({
                "method":     r.method,
                "service":    r.service,
                "permission": r.permission,
                "status":     r.status,
                "detail":     r.detail,
                "required":   r.required,
            })
    print(f"  Results saved → {path}\n")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="Check IAM permissions for the S3 chargeback pipeline"
    )
    parser.add_argument(
        "--method", choices=["cur", "lens", "both"], default="both",
        help="Which method to check (default: both)"
    )
    parser.add_argument(
        "--profile", default=None,
        help="AWS profile name to use (default: env/instance role)"
    )
    return parser.parse_args()


def main():
    args    = parse_args()
    session = get_session(args.profile)

    print(f"\n{BOLD}S3 Chargeback — Permission Checker{RESET}")
    print(f"  Identity : {whoami(session)}")
    print(f"  Region   : {CONFIG['region']}")
    print(f"  Checking : {args.method.upper()}")

    all_results = []

    if args.method in ("cur", "both"):
        print_section("Method 1 — CUR v2 + Athena")
        results = run_checks(METHOD1_CHECKS, session)
        all_results.extend(results)

    if args.method in ("lens", "both"):
        print_section("Method 2 — S3 Storage Lens + Pricing API")
        results = run_checks(METHOD2_CHECKS, session)
        all_results.extend(results)

    print_summary(all_results)
    save_csv(all_results)


if __name__ == "__main__":
    try:
        main()
    except NoCredentialsError:
        print(f"\n{RED}ERROR: No AWS credentials found.{RESET}")
        print("  Configure credentials via one of:")
        print("  1. aws configure  (sets ~/.aws/credentials)")
        print("  2. export AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY")
        print("  3. Attach an IAM role to your EC2/ECS/Lambda instance")
        raise SystemExit(1)
