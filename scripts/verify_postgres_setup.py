#!/usr/bin/env python3
"""Verify Docker Postgres + LangGraph checkpoint tables for Phase 3.6."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_dotenv() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        return
    for raw in env_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def main() -> int:
    _load_dotenv()
    conn = os.environ.get("DATABASE_URL", "").strip()
    if not conn:
        print("DATABASE_URL is not set.")
        print("Copy .env.example → .env and run: docker compose up -d")
        return 1

    try:
        from psycopg import connect

        with connect(conn) as db:
            with db.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"Postgres OK: {version.split(',')[0]}")

                cur.execute(
                    """
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                      AND tablename IN (
                        'checkpoints', 'conversations', 'messages'
                      )
                    ORDER BY tablename
                    """
                )
                tables = [row[0] for row in cur.fetchall()]
                if tables:
                    print(f"Postgres tables: {', '.join(tables)}")
                else:
                    print(
                        "No app tables yet — start the API once "
                        "(uvicorn api.main:app) to run schema setup."
                    )
    except Exception as exc:
        print(f"Postgres check failed: {exc}")
        print("Is the container running?  docker compose up -d")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
