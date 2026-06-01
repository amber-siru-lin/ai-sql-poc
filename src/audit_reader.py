"""Read audit records from S3 (or legacy local JSONL)."""

from __future__ import annotations

import json
from typing import Any

from src.audit_logger import _resolve_destination, _s3_client, audit_config


def _parse_record(raw: str, *, source_key: str) -> dict[str, Any] | None:
    try:
        record = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(record, dict):
        record["_meta"] = {"s3_key": source_key}
    return record


def _date_to_prefix(date: str, prefix: str) -> str:
    parts = date.split("-")
    if len(parts) != 3:
        return prefix
    return f"{prefix}{parts[0]}/{parts[1]}/{parts[2]}/"


def _list_s3_keys(*, date: str | None = None, max_keys: int = 500) -> list[str]:
    cfg = audit_config()
    bucket = cfg["s3_bucket"]
    if not bucket:
        return []

    prefix = cfg["s3_prefix"]
    if date:
        prefix = _date_to_prefix(date, prefix)

    client = _s3_client()
    keys: list[str] = []
    token: str | None = None
    while len(keys) < max_keys:
        kwargs: dict[str, Any] = {
            "Bucket": bucket,
            "Prefix": prefix,
            "MaxKeys": min(1000, max_keys - len(keys)),
        }
        if token:
            kwargs["ContinuationToken"] = token
        resp = client.list_objects_v2(**kwargs)
        for obj in resp.get("Contents") or []:
            key = obj.get("Key") or ""
            if key.endswith(".json"):
                keys.append(key)
        if not resp.get("IsTruncated"):
            break
        token = resp.get("NextContinuationToken")
        if not token:
            break

    keys.sort(reverse=True)
    return keys[:max_keys]


def _fetch_s3_records(keys: list[str]) -> list[dict[str, Any]]:
    cfg = audit_config()
    bucket = cfg["s3_bucket"]
    if not bucket or not keys:
        return []

    client = _s3_client()
    records: list[dict[str, Any]] = []
    for key in keys:
        try:
            resp = client.get_object(Bucket=bucket, Key=key)
            body = resp["Body"].read().decode("utf-8")
            record = _parse_record(body, source_key=key)
            if record:
                records.append(record)
        except Exception:
            continue
    return records


def list_audit_dates() -> list[str]:
    """Available log dates (YYYY-MM-DD), newest first."""
    if _resolve_destination() not in ("s3", "both"):
        return _list_local_dates()
    keys = _list_s3_keys(max_keys=2000)
    dates: set[str] = set()
    prefix = audit_config()["s3_prefix"]
    for key in keys:
        # audit/2026/06/01/thread/run.json
        rest = key[len(prefix) :] if key.startswith(prefix) else key
        parts = rest.split("/")
        if len(parts) >= 3 and len(parts[0]) == 4:
            dates.add(f"{parts[0]}-{parts[1]}-{parts[2]}")
    return sorted(dates, reverse=True)


def _list_local_dates() -> list[str]:
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "logs/audit"
    if not root.is_dir():
        return []
    return sorted((p.stem for p in root.glob("*.jsonl") if p.is_file()), reverse=True)


def read_audit_entries(
    *,
    date: str | None = None,
    limit: int = 50,
    thread_id: str | None = None,
    source: str | None = None,
) -> list[dict[str, Any]]:
    """Return audit records newest-first."""

    def _matches(entry: dict[str, Any]) -> bool:
        if thread_id and entry.get("thread_id") != thread_id:
            return False
        if source and entry.get("source") != source:
            return False
        return True

    limit = max(1, min(limit, 200))
    if _resolve_destination() in ("s3", "both") and audit_config()["s3_bucket"]:
        scan = max(limit, min(500, limit * 10))
        keys = _list_s3_keys(date=date, max_keys=scan)
        entries = _fetch_s3_records(keys)
    else:
        entries = _read_local_entries(date=date)

    entries = [e for e in entries if _matches(e)]
    if (thread_id or source) and _resolve_destination() in ("s3", "both") and audit_config()["s3_bucket"]:
        # First pass may miss runs when many records share a day — scan deeper.
        if len(entries) < limit:
            keys = _list_s3_keys(date=date, max_keys=min(2000, scan * 4))
            entries = [e for e in _fetch_s3_records(keys) if _matches(e)]

    entries.sort(key=lambda r: r.get("timestamp") or "", reverse=True)
    return entries[:limit]


def _read_local_entries(*, date: str | None) -> list[dict[str, Any]]:
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "logs/audit"
    if not root.is_dir():
        return []
    if date:
        files = [root / f"{date}.jsonl"] if (root / f"{date}.jsonl").is_file() else []
    else:
        files = sorted(root.glob("*.jsonl"), key=lambda p: p.stem, reverse=True)

    entries: list[dict[str, Any]] = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                record["_meta"] = {"file": path.name, "line": i}
                entries.append(record)
    return entries


def list_audit_sessions(
    *,
    limit: int = 30,
    scan_limit: int = 500,
    source: str | None = "api",
) -> list[dict[str, Any]]:
    """Group audit records into sessions (newest activity first).

    ``source`` filters audit ``source`` (e.g. ``api``, ``semantic_editor``).
    Pass ``source=None`` to include all sources.
    """
    limit = max(1, min(limit, 100))
    scan_limit = max(limit, min(scan_limit, 2000))
    entries = read_audit_entries(limit=scan_limit)

    sessions: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if source is not None and entry.get("source") != source:
            continue
        tid = entry.get("thread_id")
        if not tid or tid == "cli":
            continue

        ts = entry.get("timestamp") or ""
        question = (entry.get("question") or "").strip()
        active_file = entry.get("active_file")
        session = sessions.get(tid)
        if session is None:
            sessions[tid] = {
                "thread_id": tid,
                "title": question or "(untitled session)",
                "first_timestamp": ts,
                "last_timestamp": ts,
                "run_count": 1,
                "semantic_layer": entry.get("semantic_layer"),
                "last_status": entry.get("status"),
                "active_file": active_file,
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
            if active_file:
                session["active_file"] = active_file

    ordered = sorted(
        sessions.values(),
        key=lambda s: s.get("last_timestamp") or "",
        reverse=True,
    )
    return ordered[:limit]


def search_audit_entries(
    *,
    query: str | None = None,
    semantic_layer: str | None = None,
    status: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Search audit records by optional text, semantic layer, or status."""
    limit = max(1, min(limit, 50))
    scan = max(limit * 5, 50)
    entries = read_audit_entries(limit=min(scan, 200))

    if semantic_layer:
        layer = semantic_layer.strip().lower()
        entries = [
            e
            for e in entries
            if str(e.get("semantic_layer") or "").lower() == layer
        ]

    if status:
        st = status.strip().lower()
        entries = [e for e in entries if str(e.get("status") or "").lower() == st]

    if query:
        needle = query.strip().lower()
        if needle:

            def _matches(entry: dict[str, Any]) -> bool:
                haystacks = [
                    str(entry.get("question") or ""),
                    str(entry.get("error") or ""),
                    json.dumps(entry.get("sql_executions") or []),
                ]
                return any(needle in h.lower() for h in haystacks)

            entries = [e for e in entries if _matches(e)]

    return entries[:limit]
