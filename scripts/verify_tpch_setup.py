#!/usr/bin/env python3
"""Verify Snowflake TPCH access (direct + Wren CLI). Run from repo root."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

WREN_DIR = REPO_ROOT / "wren" / "tpch"


def main() -> int:
    print("=== TPCH setup verification ===\n")
    errors = 0

    try:
        from config import snowflake_config as sf
    except ImportError:
        print("FAIL: config/snowflake_config.py missing")
        return 1

    print(f"Account: {sf.account}")
    print(f"Database: {sf.database}  warehouse: {sf.warehouse}\n")

    try:
        import snowflake.connector

        conn = snowflake.connector.connect(
            account=sf.account,
            user=sf.user,
            password=sf.password,
            warehouse=sf.warehouse,
            database=sf.database,
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS")
        count = cur.fetchone()[0]
        conn.close()
        print(f"OK  Direct Snowflake: ORDERS row count = {count}")
    except Exception as exc:
        print(f"FAIL Direct Snowflake: {exc}")
        errors += 1

    if not shutil.which("wren"):
        print("FAIL wren CLI not on PATH (pip install 'wrenai[snowflake,memory]')")
        errors += 1
    elif not (WREN_DIR / "target" / "mdl.json").is_file():
        print("FAIL missing wren/tpch/target/mdl.json — run: cd wren/tpch && wren context build")
        errors += 1
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
    print("All checks passed. Use Semantics → Wren with model names (orders, customer), not TPCH_SF1.*")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
