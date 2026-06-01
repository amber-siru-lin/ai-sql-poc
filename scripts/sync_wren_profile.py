#!/usr/bin/env python3
"""Sync ~/.wren/profiles.yml from config/snowflake_config.py (local secrets only)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

try:
    from config import snowflake_config as sf
except ImportError as exc:
    raise SystemExit(
        "Missing config/snowflake_config.py — "
        "cp config/snowflake_config.example.py config/snowflake_config.py"
    ) from exc

PROFILE_NAME = "tpch-sf1"
WREN_PROFILES = Path.home() / ".wren" / "profiles.yml"
# Session schema for TPCH sample data (MDL uses SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.*)
TPCH_SCHEMA = "TPCH_SF1"


def main() -> None:
    WREN_PROFILES.parent.mkdir(parents=True, exist_ok=True)

    data: dict = {"active": PROFILE_NAME, "profiles": {}}
    if WREN_PROFILES.is_file():
        loaded = yaml.safe_load(WREN_PROFILES.read_text()) or {}
        if isinstance(loaded, dict):
            data["profiles"] = loaded.get("profiles") or {}

    data["profiles"][PROFILE_NAME] = {
        "datasource": "snowflake",
        "user": sf.user,
        "password": sf.password,
        "account": sf.account,
        "database": sf.database,
        "sf_schema": TPCH_SCHEMA,
        "warehouse": sf.warehouse,
    }
    data["active"] = PROFILE_NAME

    WREN_PROFILES.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))
    print(f"Wrote {WREN_PROFILES} (profile {PROFILE_NAME!r}, account={sf.account!r})")


if __name__ == "__main__":
    main()
