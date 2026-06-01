"""Postgres / Docker health for the UI connection panel."""

from __future__ import annotations

import os
import subprocess
from typing import Any

from src.checkpoint_factory import checkpoint_backend

POSTGRES_CONTAINER = "ai-sql-poc-postgres"


def _docker_container_state() -> str | None:
    try:
        proc = subprocess.run(
            [
                "docker",
                "inspect",
                "-f",
                "{{.State.Status}}",
                POSTGRES_CONTAINER,
            ],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    state = proc.stdout.strip()
    return state or None


def _probe_postgres(conn_string: str) -> tuple[bool, str]:
    try:
        import psycopg

        with psycopg.connect(conn_string, connect_timeout=2) as conn:
            conn.execute("SELECT 1")
        return True, "Postgres accepting connections"
    except Exception as exc:
        return False, str(exc)


def postgres_docker_status() -> dict[str, Any]:
    """Return Docker/Postgres connectivity for ``GET /api/status``."""
    configured = bool(os.environ.get("DATABASE_URL", "").strip())
    backend = checkpoint_backend()
    container = _docker_container_state()

    if not configured:
        if container == "running":
            msg = "DATABASE_URL not set — Docker container is running"
            status = "not_configured"
        elif container is None:
            msg = "Postgres (Docker) not configured"
            status = "not_configured"
        else:
            msg = f"Postgres container {container} — set DATABASE_URL in .env"
            status = "not_configured"
        return {
            "status": status,
            "message": msg,
            "configured": False,
            "backend": backend,
            "container": container,
            "docker_available": container is not None or _docker_cli_available(),
        }

    conn = os.environ["DATABASE_URL"].strip()
    ok, detail = _probe_postgres(conn)
    if ok and backend == "postgres":
        return {
            "status": "connected",
            "message": "Postgres (Docker) connected",
            "configured": True,
            "backend": backend,
            "container": container or "running",
            "docker_available": True,
        }
    if ok:
        return {
            "status": "disconnected",
            "message": "Postgres reachable but API using in-memory checkpoints — restart API",
            "configured": True,
            "backend": backend,
            "container": container,
            "docker_available": True,
        }
    if container == "running":
        return {
            "status": "disconnected",
            "message": f"Postgres container running but DB unreachable: {detail}",
            "configured": True,
            "backend": backend,
            "container": container,
            "docker_available": True,
        }
    return {
        "status": "disconnected",
        "message": f"Postgres unavailable: {detail}",
        "configured": True,
        "backend": backend,
        "container": container,
        "docker_available": _docker_cli_available(),
    }


def _docker_cli_available() -> bool:
    try:
        proc = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=2,
            check=False,
        )
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
