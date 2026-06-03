#!/usr/bin/env python3
"""Verify Snowflake access (direct + optional Wren CLI). Run from repo root."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config.settings import dataset_label, qualified_schema_prefix, snowflake_database, snowflake_schema

WREN_DIR = REPO_ROOT / "wren" / "tpch"


def main() -> int:
    print(f"=== Snowflake setup verification ({dataset_label()}) ===\n")
    errors = 0

    try:
        from config import snowflake_config as sf
    except ImportError:
        print("FAIL: config/snowflake_config.py missing")
        return 1

    db = snowflake_database() or sf.database
    sch = snowflake_schema() or sf.schema
    print(f"Account: {sf.account}")
    print(f"Database: {db}  schema: {sch}  warehouse: {sf.warehouse}\n")

    try:
        import snowflake.connector

        conn = snowflake.connector.connect(
            account=sf.account,
            user=sf.user,
            password=sf.password,
            warehouse=sf.warehouse,
            database=db,
            schema=sch,
        )
        cur = conn.cursor()
        cur.execute(f"SHOW TABLES IN SCHEMA {db}.{sch}")
        tables = cur.fetchall()
        conn.close()
        print(f"OK  Direct Snowflake: {len(tables)} table(s) visible in {db}.{sch}")
    except Exception as exc:
        print(f"FAIL Direct Snowflake: {exc}")
        errors += 1

    if not shutil.which("wren"):
        print("SKIP wren CLI not on PATH (optional — pip install 'wrenai[snowflake,memory]')")
    elif not (WREN_DIR / "target" / "mdl.json").is_file():
        print("SKIP missing wren/tpch/target/mdl.json — run: cd wren/tpch && wren context build")
    else:
        proc = subprocess.run(
            ["wren", "--sql", "SELECT COUNT(*) AS n FROM orders", "-o", "json"],
            cwd=WREN_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode == 0:
            print(f"OK  Wren MDL model 'orders': {(proc.stdout or '').strip().splitlines()[0]}")
        else:
            print(f"FAIL Wren: {(proc.stderr or proc.stdout or '').strip()}")
            errors += 1

    print()
    if errors:
        print(f"{errors} check(s) failed. Fix above, then: scripts/py scripts/sync_wren_profile.py")
        return 1
    print(
        f"All checks passed for {qualified_schema_prefix()}. "
        "In Wren mode use MDL model names, not raw Snowflake table prefixes."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
