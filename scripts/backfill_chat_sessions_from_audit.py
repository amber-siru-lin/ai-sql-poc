#!/usr/bin/env python3
"""Backfill Postgres chat sessions from S3 audit logs (server-side)."""

from __future__ import annotations

import argparse
import asyncio
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


def _messages_from_audit_entries(entries: list[dict]) -> list[dict]:
    ordered = sorted(entries, key=lambda e: e.get("timestamp") or "")
    messages: list[dict] = []
    for entry in ordered:
        run_id = entry.get("run_id") or "run"
        question = entry.get("question")
        if question:
            messages.append(
                {"id": f"{run_id}-user", "role": "user", "content": question},
            )
        parts: list[str] = []
        if entry.get("error"):
            parts.append(f"**Error:** {entry['error']}")
        for step in entry.get("sql_executions") or []:
            if step.get("sql"):
                parts.append(f"```sql\n{step['sql']}\n```")
            if step.get("error"):
                parts.append(f"**SQL error:** {step['error']}")
            elif step.get("result_preview"):
                parts.append(step["result_preview"])
        assistant = "\n\n".join(parts) if parts else (
            "Run failed." if entry.get("status") == "error" else "Completed."
        )
        messages.append(
            {"id": f"{run_id}-assistant", "role": "assistant", "content": assistant},
        )
    return messages


async def _backfill(*, limit: int, dry_run: bool) -> int:
    from src.audit_reader import read_audit_entries
    from src.chat_sessions.store import (
        conversation_exists,
        create_session,
        init_chat_sessions_from_env,
        replace_messages,
        shutdown_chat_sessions,
    )

    if not await init_chat_sessions_from_env():
        print("DATABASE_URL not set or Postgres unavailable.")
        return 1

    entries = read_audit_entries(limit=limit, source="api")
    by_thread: dict[str, list[dict]] = {}
    for entry in entries:
        tid = entry.get("thread_id")
        if not tid:
            continue
        by_thread.setdefault(str(tid), []).append(entry)

    written = 0
    for thread_id, thread_entries in by_thread.items():
        if await conversation_exists(thread_id):
            continue
        messages = _messages_from_audit_entries(thread_entries)
        if not messages:
            continue
        semantic = (thread_entries[-1].get("semantic_layer") or "off") if thread_entries else "off"
        if dry_run:
            print(f"would backfill {thread_id} ({len(messages)} messages)")
            written += 1
            continue
        await create_session(thread_id, semantic_layer=semantic)
        await replace_messages(thread_id, messages, semantic_layer=semantic)
        print(f"backfilled {thread_id} ({len(messages)} messages)")
        written += 1

    await shutdown_chat_sessions()
    print(f"Done — {written} thread(s).")
    return 0


def main() -> int:
    _load_dotenv()
    parser = argparse.ArgumentParser(description="Backfill chat sessions from audit logs")
    parser.add_argument("--limit", type=int, default=500, help="Max audit entries to scan")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    return asyncio.run(_backfill(limit=args.limit, dry_run=args.dry_run))


if __name__ == "__main__":
    raise SystemExit(main())
