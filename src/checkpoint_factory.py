"""LangGraph checkpointer — in-memory (default) or Postgres when DATABASE_URL is set."""

from __future__ import annotations

import os
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

_pool: Any | None = None
_checkpointer: Any | None = None
_backend: str = "memory"


def checkpoint_backend() -> str:
    """``memory`` or ``postgres`` — reflects what is active after init."""
    return _backend


def get_checkpointer():
    """Return the active checkpointer (MemorySaver if Postgres was not initialized)."""
    if _checkpointer is not None:
        return _checkpointer
    return MemorySaver()


def init_postgres_checkpointer(conn_string: str) -> None:
    """Open a connection pool, create LangGraph checkpoint tables, and store the saver."""
    global _pool, _checkpointer, _backend

    if _checkpointer is not None:
        return

    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool

    def _configure_conn(conn) -> None:
        conn.autocommit = True
        conn.row_factory = dict_row

    _pool = ConnectionPool(
        conn_string,
        min_size=1,
        max_size=10,
        open=True,
        configure=_configure_conn,
    )
    _checkpointer = PostgresSaver(_pool)
    _checkpointer.setup()
    _backend = "postgres"


def init_checkpointer_from_env() -> str:
    """Initialize Postgres when ``DATABASE_URL`` is set; otherwise keep MemorySaver."""
    conn = os.environ.get("DATABASE_URL", "").strip()
    if conn:
        init_postgres_checkpointer(conn)
        return "postgres"
    return "memory"


def shutdown_checkpointer() -> None:
    """Close the Postgres pool on API shutdown."""
    global _pool, _checkpointer, _backend
    if _pool is not None:
        _pool.close()
    _pool = None
    _checkpointer = None
    _backend = "memory"
