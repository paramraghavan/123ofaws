#!/usr/bin/env python3
"""Minimal boto3 STS AssumeRole example.

Usage:
    ./cross_account_access_sts.py arn:aws:iam::111111111111:role/OperatorRole

The caller credentials are resolved by boto3's normal provider chain:
environment variables, AWS profiles, SSO cache, EC2/ECS role credentials, etc.
"""

from __future__ import annotations

import argparse
from datetime import timezone
from typing import Any


def assume_role(
    role_arn: str,
    session_name: str,
    duration_seconds: int = 3600,
) -> dict[str, Any]:
    """Assume role and return the STS Credentials object."""
    import boto3

    sts = boto3.client("sts")
    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
        DurationSeconds=duration_seconds,
    )
    return response["Credentials"]


def s3_client_for_credentials(credentials: dict[str, Any]):
    """Create an S3 client from temporary STS credentials."""
    import boto3

    return boto3.client(
        "s3",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )


def list_buckets(role_arn: str, session_name: str, duration_seconds: int) -> None:
    credentials = assume_role(role_arn, session_name, duration_seconds)
    expiration = credentials["Expiration"].astimezone(timezone.utc).isoformat()
    print(f"Assumed role until {expiration}")

    s3 = s3_client_for_credentials(credentials)
    for bucket in s3.list_buckets().get("Buckets", []):
        print(bucket["Name"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Assume a role and list S3 buckets.")
    parser.add_argument("role_arn", help="Role ARN to assume.")
    parser.add_argument(
        "--session-name",
        default="cross-account-s3",
        help="STS role session name.",
    )
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=3600,
        help="Requested STS session duration. Minimum is 900 seconds.",
    )
    args = parser.parse_args()

    list_buckets(args.role_arn, args.session_name, args.duration_seconds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
