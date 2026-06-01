"""Append-only audit log for agent runs (local JSONL + optional S3)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SQL_TOOL_NAMES = frozenset(
    {
        "execute_snowflake_sql",
        "wren_run_sql",
        "wren_dry_plan",
        "ask_cortex_analyst",
    }
)

DEFAULT_LOCAL_DIR = Path("logs/audit")
DEFAULT_S3_PREFIX = "audit/"


def audit_config() -> dict[str, Any]:
    """Resolved audit destinations (for status endpoints and docs)."""
    bucket = os.environ.get("AUDIT_S3_BUCKET", "").strip()
    prefix = os.environ.get("AUDIT_S3_PREFIX", DEFAULT_S3_PREFIX).strip() or DEFAULT_S3_PREFIX
    if not prefix.endswith("/"):
        prefix += "/"
    local_dir = Path(os.environ.get("AUDIT_LOCAL_DIR", DEFAULT_LOCAL_DIR))
    return {
        "s3_bucket": bucket or None,
        "s3_prefix": prefix,
        "local_dir": str(local_dir),
        "enabled": True,
    }


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _local_audit_path(when: datetime | None = None) -> Path:
    when = when or datetime.now(UTC)
    day = when.strftime("%Y-%m-%d")
    cfg = audit_config()
    path = _repo_root() / cfg["local_dir"] / f"{day}.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _s3_key(record: dict[str, Any], prefix: str) -> str:
    when = datetime.fromisoformat(record["timestamp"].replace("Z", "+00:00"))
    run_id = record.get("run_id") or "unknown"
    thread_id = record.get("thread_id") or "unknown"
    date_part = when.strftime("%Y/%m/%d")
    safe_thread = "".join(c if c.isalnum() or c in "-_" else "_" for c in str(thread_id))[:64]
    return f"{prefix}{date_part}/{safe_thread}/{run_id}.json"


def _put_s3(record: dict[str, Any]) -> str | None:
    bucket = audit_config()["s3_bucket"]
    if not bucket:
        return None
    try:
        import boto3
    except ImportError:
        logger.warning("boto3 not installed; skipping S3 audit upload")
        return None

    prefix = audit_config()["s3_prefix"]
    key = _s3_key(record, prefix)
    body = json.dumps(record, ensure_ascii=False, default=str).encode("utf-8")
    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    client = boto3.client("s3", region_name=region)
    client.put_object(
        Bucket=bucket,
        Key=key,
        Body=body,
        ContentType="application/json",
    )
    return f"s3://{bucket}/{key}"


def _append_local(record: dict[str, Any]) -> Path:
    path = _local_audit_path()
    line = json.dumps(record, ensure_ascii=False, default=str) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return path


def result_fingerprint(text: str | None, *, max_chars: int = 4096) -> str | None:
    if not text:
        return None
    sample = text[:max_chars]
    return hashlib.sha256(sample.encode("utf-8")).hexdigest()


def write_audit_record(record: dict[str, Any]) -> dict[str, str | None]:
    """Persist one audit record. Returns paths written (local file, s3 uri)."""
    local_path: str | None = None
    s3_uri: str | None = None
    try:
        path = _append_local(record)
        local_path = str(path)
    except OSError:
        logger.exception("Failed to write local audit log")

    try:
        s3_uri = _put_s3(record)
    except Exception:
        logger.exception("Failed to write S3 audit log")

    return {"local_path": local_path, "s3_uri": s3_uri}


def build_audit_record(
    *,
    thread_id: str,
    run_id: str | None,
    semantic_layer: str,
    question: str | None,
    sql_executions: list[dict[str, Any]],
    status: str,
    duration_ms: int,
    error: str | None = None,
    source: str = "api",
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source": source,
        "thread_id": thread_id,
        "run_id": run_id,
        "semantic_layer": semantic_layer,
        "question": question,
        "sql_executions": sql_executions,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
    }
