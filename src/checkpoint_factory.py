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


async def init_postgres_checkpointer(conn_string: str) -> None:
    """Open an async pool, create LangGraph checkpoint tables, and store the saver."""
    global _pool, _checkpointer, _backend

    if _checkpointer is not None:
        return

    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg.rows import dict_row
    from psycopg_pool import AsyncConnectionPool

    async def _configure_conn(conn) -> None:
        await conn.set_autocommit(True)
        conn.row_factory = dict_row

    _pool = AsyncConnectionPool(
        conn_string,
        min_size=1,
        max_size=10,
        open=False,
        configure=_configure_conn,
    )
    await _pool.open()
    _checkpointer = AsyncPostgresSaver(_pool)
    await _checkpointer.setup()
    _backend = "postgres"


async def init_checkpointer_from_env() -> str:
    """Initialize Postgres when ``DATABASE_URL`` is set; otherwise keep MemorySaver."""
    conn = os.environ.get("DATABASE_URL", "").strip()
    if conn:
        await init_postgres_checkpointer(conn)
        return "postgres"
    return "memory"


async def shutdown_checkpointer() -> None:
    """Close the Postgres pool on API shutdown."""
    global _pool, _checkpointer, _backend
    if _pool is not None:
        await _pool.close()
    _pool = None
    _checkpointer = None
    _backend = "memory"
