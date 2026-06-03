"""Shared startup checks for AWS and Snowflake configuration."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_repo_on_path() -> Path:
    root = repo_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def check_snowflake_config() -> None:
    config_path = repo_root() / "config" / "snowflake_config.py"
    if not config_path.exists():
        raise SystemExit(
            "Missing Snowflake config.\n"
            "  cp config/snowflake_config.example.py config/snowflake_config.py\n"
            "  Then edit with your Snowflake username/password."
        )


def check_aws_credentials() -> None:
    import boto3
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError

    profile = os.environ.get("AWS_PROFILE")
    hint = (
        "AWS credentials not found.\n\n"
        "Configure AWS CLI credentials for your account, then try again.\n"
        "Common setup:\n"
        "  aws configure sso          # first-time SSO profile\n"
        "  export AWS_PROFILE=your-profile-name\n"
        "  aws sso login --profile $AWS_PROFILE\n\n"
        "See config/README.md and SETUP.md for details."
    )
    if profile:
        hint = (
            f"AWS credentials not found for profile '{profile}'.\n\n"
            f"Run: aws sso login --profile {profile}\n"
            "SSO sessions expire — you may need to log in again."
        )

    try:
        boto3.client("sts").get_caller_identity()
    except (NoCredentialsError, PartialCredentialsError):
        raise SystemExit(hint) from None
    except Exception as exc:
        if "ExpiredToken" in str(exc) or "Unable to locate credentials" in str(exc):
            raise SystemExit(hint) from None
        raise


def check_all() -> None:
    ensure_repo_on_path()
    check_snowflake_config()
    check_aws_credentials()
