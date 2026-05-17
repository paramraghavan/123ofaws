#!/usr/bin/env python3
"""
Basic AWS credential helper for use with credential_process.

Wire it up in ~/.aws/config:

    [profile emr-prod]
    region = us-east-1
    credential_process = /opt/aws-helper/aws_creds_helper.py emr-prod

Configure roles in ~/.aws/helper-roles.json:

    {
      "emr-prod": {
        "role_arn":         "arn:aws:iam::111111111111:role/EMRHygieneRole",
        "source_profile":   "base",
        "mfa_serial":       "arn:aws:iam::222222222222:mfa/yourusername",
        "duration_seconds": 3600,
        "external_id":      "optional-external-id"
      }
    }

On first call it prompts for an MFA code (if configured), assumes the
role, and caches the result under ~/.aws/helper-cache/. Subsequent calls
read from the cache until 5 minutes before expiration, at which point
it re-prompts and re-assumes.

Why this exists rather than using AWS CLI's built-in source_profile +
role_arn handling: extension points. The functions below are the natural
places to swap in a different credentials source (Vault, 1Password,
hardware token, etc.):

  - load_source_credentials()  - where the base creds come from
  - get_mfa_code()             - how MFA is gathered (TOTP CLI, push, etc.)
  - write_cache()              - where assumed creds get stored

Output format is fixed by AWS — see:
https://docs.aws.amazon.com/sdkref/latest/guide/feature-process-credentials.html
"""

import argparse
import json
import os
import stat
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, ProfileNotFound


HELPER_CONFIG = Path.home() / ".aws" / "helper-roles.json"
CACHE_DIR     = Path.home() / ".aws" / "helper-cache"
REFRESH_BUFFER = timedelta(minutes=5)   # refresh 5min before expiry


# ---------- main ----------

def main():
    p = argparse.ArgumentParser(
        description="AWS credential_process helper",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("role_name", help="Logical role name from helper-roles.json")
    p.add_argument("--no-cache", action="store_true",
                   help="Skip cache; always assume fresh")
    p.add_argument("--config", default=str(HELPER_CONFIG),
                   help="Path to roles JSON")
    args = p.parse_args()

    try:
        config = load_role_config(args.config, args.role_name)

        if not args.no_cache:
            cached = read_cache(args.role_name)
            if cached:
                emit(cached)
                return 0

        creds = assume_role(config)
        write_cache(args.role_name, creds)
        emit(creds)
        return 0

    except Exception as e:
        # Anything we write to stdout becomes the SDK's "credentials".
        # Errors must go to stderr, and we must exit non-zero.
        sys.stderr.write(f"aws_creds_helper: {e}\n")
        return 1


# ---------- config loading ----------

def load_role_config(config_path, role_name):
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"roles config not found: {path}")

    # Enforce sane perms on the config file (it can reveal role ARNs etc.).
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        sys.stderr.write(
            f"warning: {path} is mode {oct(mode)}; consider chmod 600\n"
        )

    with open(path) as f:
        all_configs = json.load(f)

    if role_name not in all_configs:
        raise KeyError(f"role '{role_name}' not found in {path}")
    return all_configs[role_name]


# ---------- caching ----------

def read_cache(role_name):
    cache_file = CACHE_DIR / f"{role_name}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file) as f:
            data = json.load(f)
        exp = parse_iso(data["Expiration"])
        if exp > datetime.now(timezone.utc) + REFRESH_BUFFER:
            return data
    except (json.JSONDecodeError, KeyError, ValueError):
        # Corrupt or stale cache file — ignore and re-assume.
        pass
    return None


def write_cache(role_name, creds):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    # Lock down cache dir perms (700) and cache file perms (600).
    os.chmod(CACHE_DIR, stat.S_IRWXU)
    cache_file = CACHE_DIR / f"{role_name}.json"
    # Write to a temp file, fsync, then rename — atomic against concurrent calls.
    tmp = cache_file.with_suffix(".tmp")
    with open(os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "w") as f:
        json.dump(creds, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, cache_file)


# ---------- assume role ----------

def assume_role(config):
    source_profile = config.get("source_profile", "default")
    try:
        session = boto3.Session(profile_name=source_profile)
    except ProfileNotFound:
        raise RuntimeError(
            f"source_profile '{source_profile}' not found in ~/.aws/credentials"
        )

    sts = session.client("sts")

    kwargs = {
        "RoleArn": config["role_arn"],
        "RoleSessionName": session_name(),
        "DurationSeconds": int(config.get("duration_seconds", 3600)),
    }
    if "external_id" in config:
        kwargs["ExternalId"] = config["external_id"]
    if "mfa_serial" in config:
        kwargs["SerialNumber"] = config["mfa_serial"]
        kwargs["TokenCode"]    = get_mfa_code()

    try:
        resp = sts.assume_role(**kwargs)
    except ClientError as e:
        raise RuntimeError(f"AssumeRole failed: {e}")

    c = resp["Credentials"]
    return {
        "Version":         1,
        "AccessKeyId":     c["AccessKeyId"],
        "SecretAccessKey": c["SecretAccessKey"],
        "SessionToken":    c["SessionToken"],
        # Expiration must be ISO 8601 with timezone, per AWS spec.
        "Expiration":      c["Expiration"].astimezone(timezone.utc).isoformat(),
    }


def get_mfa_code():
    """
    Prompt on stderr (NOT stdout — stdout is reserved for the JSON output).
    Swap this for a TOTP-from-keyring lookup or hardware-token call as needed.
    """
    sys.stderr.write("MFA code: ")
    sys.stderr.flush()
    return input().strip()


def session_name():
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "helper"
    # IAM allows up to 64 chars; restrict to safe set.
    safe = "".join(ch for ch in user if ch.isalnum() or ch in "._-")
    return f"helper-{safe}"[:64]


# ---------- helpers ----------

def emit(creds):
    """Print to stdout in the exact AWS-mandated JSON shape."""
    print(json.dumps(creds))


def parse_iso(s):
    # Handle both 'Z' and '+00:00' suffixes
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


if __name__ == "__main__":
    sys.exit(main())
