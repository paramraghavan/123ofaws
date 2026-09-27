#!/usr/bin/env python3
"""
AWS credential_process helper.

AWS runs this script when a profile has:

    [profile profile-oper]
    region = us-east-1
    credential_process = /path/to/credential_helper.py profile-oper

The script must print credentials JSON to stdout and nothing else. Prompts,
warnings, and errors go to stderr because the AWS CLI/SDK parses stdout as the
credential response.

Default role configuration file:

    ~/.aws/credential-helper.json

Example:

    {
      "profile-oper": {
        "role_arn": "arn:aws:iam::111111111111:role/OperatorRole",
        "source_profile": "base",
        "mfa_serial": "arn:aws:iam::222222222222:mfa/your-user",
        "duration_seconds": 3600,
        "external_id": "optional-external-id"
      }
    }
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import stat
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path.home() / ".aws" / "credential-helper.json"
DEFAULT_CACHE_DIR = Path.home() / ".aws" / "credential-helper-cache"
REFRESH_BUFFER = timedelta(minutes=5)
ROLE_SESSION_MAX_LENGTH = 64
REQUIRED_OUTPUT_KEYS = {
    "Version",
    "AccessKeyId",
    "SecretAccessKey",
    "SessionToken",
    "Expiration",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit AWS credential_process JSON for an assumed role.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default=os.environ.get("AWS_PROFILE", "default"),
        help="Profile key in the helper config.",
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="Path to helper JSON config.",
    )
    parser.add_argument(
        "--cache-dir",
        default=str(DEFAULT_CACHE_DIR),
        help="Directory for cached temporary credentials.",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Always fetch fresh credentials.",
    )

    args = parser.parse_args()

    try:
        config = load_profile_config(Path(args.config), args.profile)
        cache_dir = Path(args.cache_dir)

        if not args.no_cache:
            cached = read_cache(cache_dir, args.profile)
            if cached:
                emit_credentials(cached)
                return 0

        credentials = assume_role(config, args.profile)
        write_cache(cache_dir, args.profile, credentials)
        emit_credentials(credentials)
        return 0
    except Exception as exc:
        print(f"credential_helper: {exc}", file=sys.stderr)
        return 1


def load_profile_config(config_path: Path, profile: str) -> dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    warn_if_group_or_world_readable(config_path)

    with config_path.open(encoding="utf-8") as config_file:
        all_profiles = json.load(config_file)

    if not isinstance(all_profiles, dict):
        raise ValueError(f"{config_path} must contain a JSON object keyed by profile")

    if profile not in all_profiles:
        raise KeyError(f"profile '{profile}' not found in {config_path}")

    config = all_profiles[profile]
    if not isinstance(config, dict):
        raise ValueError(f"profile '{profile}' must contain a JSON object")
    validate_profile_config(config, profile)

    return config


def validate_profile_config(config: dict[str, Any], profile: str) -> None:
    required_keys = ("role_arn",)
    for key in required_keys:
        if not config.get(key):
            raise KeyError(f"profile '{profile}' is missing required key '{key}'")

    if not isinstance(config["role_arn"], str):
        raise ValueError(f"profile '{profile}' key 'role_arn' must be a string")

    for key in ("source_profile", "mfa_serial", "external_id", "role_session_name"):
        if key in config and not isinstance(config[key], str):
            raise ValueError(f"profile '{profile}' key '{key}' must be a string")


def warn_if_group_or_world_readable(path: Path) -> None:
    mode = path.stat().st_mode & 0o777
    if mode & 0o077:
        print(
            f"warning: {path} is mode {oct(mode)}; consider chmod 600",
            file=sys.stderr,
        )


def read_cache(cache_dir: Path, profile: str) -> dict[str, Any] | None:
    cache_file = cache_path(cache_dir, profile)
    if not cache_file.exists():
        return None

    try:
        with cache_file.open(encoding="utf-8") as cache:
            credentials = json.load(cache)
        if not REQUIRED_OUTPUT_KEYS.issubset(credentials):
            return None
        expiration = parse_expiration(credentials["Expiration"])
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        return None

    if expiration > datetime.now(timezone.utc) + REFRESH_BUFFER:
        return credentials
    return None


def write_cache(cache_dir: Path, profile: str, credentials: dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(cache_dir, stat.S_IRWXU)

    destination = cache_path(cache_dir, profile)
    temporary = destination.with_name(f"{destination.name}.{os.getpid()}.tmp")

    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as cache:
            json.dump(credentials, cache)
            cache.flush()
            os.fsync(cache.fileno())

        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def cache_path(cache_dir: Path, profile: str) -> Path:
    safe_profile = re.sub(r"[^A-Za-z0-9_.-]", "_", profile)
    return cache_dir / f"{safe_profile}.json"


def assume_role(config: dict[str, Any], profile: str) -> dict[str, Any]:
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError, ProfileNotFound
    except ImportError as exc:
        raise RuntimeError(
            "boto3 is required: install it with 'python3 -m pip install boto3'"
        ) from exc

    source_profile = config.get("source_profile", "default")

    try:
        session = boto3.Session(profile_name=source_profile)
    except ProfileNotFound as exc:
        raise RuntimeError(f"source_profile '{source_profile}' not found") from exc

    sts = session.client("sts")
    request: dict[str, Any] = {
        "RoleArn": config["role_arn"],
        "RoleSessionName": role_session_name(
            config.get("role_session_name") or profile
        ),
        "DurationSeconds": duration_seconds(config),
    }

    if config.get("external_id"):
        request["ExternalId"] = config["external_id"]

    if config.get("mfa_serial"):
        request["SerialNumber"] = config["mfa_serial"]
        request["TokenCode"] = get_mfa_code()

    try:
        response = sts.assume_role(**request)
    except (BotoCoreError, ClientError) as exc:
        raise RuntimeError(f"AssumeRole failed: {exc}") from exc

    credentials = response["Credentials"]
    return {
        "Version": 1,
        "AccessKeyId": credentials["AccessKeyId"],
        "SecretAccessKey": credentials["SecretAccessKey"],
        "SessionToken": credentials["SessionToken"],
        "Expiration": credentials["Expiration"].astimezone(timezone.utc).isoformat(),
    }


def get_mfa_code() -> str:
    return getpass.getpass("MFA code: ", stream=sys.stderr).strip()


def role_session_name(profile: str) -> str:
    user = os.environ.get("USER") or os.environ.get("USERNAME") or "aws-helper"
    raw_name = f"{user}-{profile}"
    safe_name = re.sub(r"[^A-Za-z0-9+=,.@_-]", "-", raw_name)
    return safe_name[:ROLE_SESSION_MAX_LENGTH]


def duration_seconds(config: dict[str, Any]) -> int:
    try:
        duration = int(config.get("duration_seconds", 3600))
    except (TypeError, ValueError) as exc:
        raise ValueError("duration_seconds must be an integer") from exc

    if duration < 900 or duration > 43200:
        raise ValueError("duration_seconds must be between 900 and 43200")
    return duration


def emit_credentials(credentials: dict[str, Any]) -> None:
    print(json.dumps(credentials, separators=(",", ":")))


def parse_expiration(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


if __name__ == "__main__":
    sys.exit(main())
