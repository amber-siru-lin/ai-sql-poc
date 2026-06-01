"""Append-only audit log for agent runs (S3 by default when bucket is set)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import UTC, datetime
from typing import Any, Literal

logger = logging.getLogger(__name__)

AuditDestination = Literal["s3", "local", "both"]

SQL_TOOL_NAMES = frozenset(
    {
        "execute_snowflake_sql",
        "wren_run_sql",
        "wren_dry_plan",
        "ask_cortex_analyst",
    }
)

DEFAULT_S3_PREFIX = "audit/"


def _resolve_destination() -> AuditDestination:
    raw = os.environ.get("AUDIT_DESTINATION", "").strip().lower()
    bucket = os.environ.get("AUDIT_S3_BUCKET", "").strip()
    if raw in ("s3", "local", "both"):
        return raw  # type: ignore[return-value]
    return "s3" if bucket else "local"


def audit_config(*, check_s3: bool = False) -> dict[str, Any]:
    """Resolved audit destinations (for status endpoints and docs)."""
    bucket = os.environ.get("AUDIT_S3_BUCKET", "").strip()
    prefix = os.environ.get("AUDIT_S3_PREFIX", DEFAULT_S3_PREFIX).strip() or DEFAULT_S3_PREFIX
    if not prefix.endswith("/"):
        prefix += "/"
    destination = _resolve_destination()
    cfg: dict[str, Any] = {
        "destination": destination,
        "s3_bucket": bucket or None,
        "s3_prefix": prefix,
        "local_dir": None,
        "enabled": destination != "local" or bool(bucket),
    }
    if check_s3 and destination in ("s3", "both") and bucket:
        cfg.update(check_audit_s3())
    elif destination == "s3" and not bucket:
        cfg["s3_status"] = "not_configured"
        cfg["s3_message"] = "Set AUDIT_S3_BUCKET in .env"
    else:
        cfg["s3_status"] = "not_configured"
        cfg["s3_message"] = "Audit uses local JSONL only (AUDIT_DESTINATION=local)"
    return cfg


def _s3_client():
    import boto3

    region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    return boto3.client("s3", region_name=region)


def check_audit_s3() -> dict[str, str]:
    """Probe S3 bucket access for audit writes and reads."""
    bucket = os.environ.get("AUDIT_S3_BUCKET", "").strip()
    if not bucket:
        return {
            "s3_status": "not_configured",
            "s3_message": "AUDIT_S3_BUCKET not set",
        }
    prefix = audit_config()["s3_prefix"]
    try:
        client = _s3_client()
        client.head_bucket(Bucket=bucket)
        client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        return {
            "s3_status": "ok",
            "s3_message": f"Writing to s3://{bucket}/{prefix}",
        }
    except Exception as exc:
        logger.debug("audit S3 check failed: %s", exc)
        return {
            "s3_status": "error",
            "s3_message": str(exc),
        }


def s3_key_for_record(record: dict[str, Any], prefix: str | None = None) -> str:
    prefix = prefix or audit_config()["s3_prefix"]
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
        key = s3_key_for_record(record)
        body = json.dumps(record, ensure_ascii=False, default=str).encode("utf-8")
        client = _s3_client()
        client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return f"s3://{bucket}/{key}"
    except Exception:
        logger.exception("Failed to write S3 audit log")
        return None


def result_fingerprint(text: str | None, *, max_chars: int = 4096) -> str | None:
    if not text:
        return None
    sample = text[:max_chars]
    return hashlib.sha256(sample.encode("utf-8")).hexdigest()


def write_audit_record(record: dict[str, Any]) -> dict[str, str | None]:
    """Persist one audit record. Returns destinations written."""
    destination = _resolve_destination()
    local_path: str | None = None
    s3_uri: str | None = None

    if destination in ("s3", "both"):
        s3_uri = _put_s3(record)
        if destination == "s3" and not s3_uri:
            logger.error(
                "audit record not persisted (S3 write failed); run_id=%s",
                record.get("run_id"),
            )
    elif destination == "local":
        logger.warning(
            "AUDIT_DESTINATION=local is deprecated; set AUDIT_S3_BUCKET for S3-only audit"
        )

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
    assistant_reply: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
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
    if assistant_reply and assistant_reply.strip():
        record["assistant_reply"] = assistant_reply.strip()
    return record
