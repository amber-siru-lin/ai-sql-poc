"""Read local audit JSONL files for the API / UI."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.audit_logger import _repo_root, audit_config


def _audit_dir() -> Path:
    return _repo_root() / audit_config()["local_dir"]


def list_audit_dates() -> list[str]:
    """Available log dates (YYYY-MM-DD), newest first."""
    root = _audit_dir()
    if not root.is_dir():
        return []
    dates = sorted(
        (p.stem for p in root.glob("*.jsonl") if p.is_file()),
        reverse=True,
    )
    return dates


def _parse_line(line: str, *, source_file: str, line_no: int) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        record = json.loads(line)
    except json.JSONDecodeError:
        return None
    if isinstance(record, dict):
        record["_meta"] = {"file": source_file, "line": line_no}
    return record


def read_audit_entries(
    *,
    date: str | None = None,
    limit: int = 50,
    thread_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return audit records newest-first."""
    root = _audit_dir()
    if not root.is_dir():
        return []

    limit = max(1, min(limit, 200))
    files: list[Path]
    if date:
        path = root / f"{date}.jsonl"
        files = [path] if path.is_file() else []
    else:
        files = sorted(root.glob("*.jsonl"), key=lambda p: p.stem, reverse=True)

    entries: list[dict[str, Any]] = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, start=1):
            record = _parse_line(line, source_file=path.name, line_no=i)
            if record is None:
                continue
            if thread_id and record.get("thread_id") != thread_id:
                continue
            entries.append(record)

    entries.sort(key=lambda r: r.get("timestamp") or "", reverse=True)
    return entries[:limit]


def list_audit_sessions(*, limit: int = 30, scan_limit: int = 500) -> list[dict[str, Any]]:
    """Group audit records into chat sessions (newest activity first)."""
    limit = max(1, min(limit, 100))
    scan_limit = max(limit, min(scan_limit, 2000))
    entries = read_audit_entries(limit=scan_limit)

    sessions: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if entry.get("source") != "api":
            continue
        thread_id = entry.get("thread_id")
        if not thread_id or thread_id == "cli":
            continue

        ts = entry.get("timestamp") or ""
        question = (entry.get("question") or "").strip()
        session = sessions.get(thread_id)
        if session is None:
            sessions[thread_id] = {
                "thread_id": thread_id,
                "title": question or "(untitled session)",
                "first_timestamp": ts,
                "last_timestamp": ts,
                "run_count": 1,
                "semantic_layer": entry.get("semantic_layer"),
                "last_status": entry.get("status"),
            }
            continue

        session["run_count"] += 1
        if ts and ts < session["first_timestamp"]:
            session["first_timestamp"] = ts
            if question:
                session["title"] = question
        if ts and ts > session["last_timestamp"]:
            session["last_timestamp"] = ts
            session["last_status"] = entry.get("status")
            session["semantic_layer"] = entry.get("semantic_layer")

    ordered = sorted(
        sessions.values(),
        key=lambda s: s.get("last_timestamp") or "",
        reverse=True,
    )
    return ordered[:limit]
