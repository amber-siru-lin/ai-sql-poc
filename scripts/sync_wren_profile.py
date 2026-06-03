#!/usr/bin/env python3
"""Sync ~/.wren/profiles.yml from config/snowflake_config.py (local secrets only)."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config.settings import snowflake_schema, wren_profile_name

try:
    from config import snowflake_config as sf
except ImportError as exc:
    raise SystemExit(
        "Missing config/snowflake_config.py — "
        "cp config/snowflake_config.example.py config/snowflake_config.py"
    ) from exc

WREN_PROFILES = Path.home() / ".wren" / "profiles.yml"


def main() -> None:
    WREN_PROFILES.parent.mkdir(parents=True, exist_ok=True)
    profile_name = wren_profile_name()
    wren_schema = snowflake_schema()

    data: dict = {"active": profile_name, "profiles": {}}
    if WREN_PROFILES.is_file():
        loaded = yaml.safe_load(WREN_PROFILES.read_text()) or {}
        if isinstance(loaded, dict):
            data["profiles"] = loaded.get("profiles") or {}

    data["profiles"][profile_name] = {
        "datasource": "snowflake",
        "user": sf.user,
        "password": sf.password,
        "account": sf.account,
        "database": sf.database,
        "sf_schema": wren_schema,
        "warehouse": sf.warehouse,
    }
    data["active"] = profile_name

    WREN_PROFILES.write_text(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))
    print(
        f"Wrote {WREN_PROFILES} (profile {profile_name!r}, "
        f"account={sf.account!r}, schema={wren_schema!r})"
    )


if __name__ == "__main__":
    main()
