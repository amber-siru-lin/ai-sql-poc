"""Postgres-backed chat sessions and messages (Phase 3.6.2)."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

DEFAULT_USER_ID = "local"
MAX_MESSAGES_PER_THREAD = 80
TITLE_MAX_LEN = 80

_pool: AsyncConnectionPool | None = None
_available = False

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def sessions_available() -> bool:
    return _available


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _title_from_messages(messages: list[dict[str, Any]]) -> str:
    for msg in messages:
        if msg.get("role") == "user":
            text = str(msg.get("content") or "").strip()
            if text:
                one_line = " ".join(text.split())
                if len(one_line) > TITLE_MAX_LEN:
                    return one_line[: TITLE_MAX_LEN - 1] + "…"
                return one_line
    return "New chat"


async def init_chat_sessions_from_env() -> bool:
    """Open pool and apply schema when DATABASE_URL is set."""
    global _pool, _available

    conn_string = os.environ.get("DATABASE_URL", "").strip()
    if not conn_string:
        _available = False
        return False

    if _pool is not None:
        _available = True
        return True

    async def _configure_conn(conn) -> None:
        conn.row_factory = dict_row

    _pool = AsyncConnectionPool(
        conn_string,
        min_size=1,
        max_size=5,
        open=False,
        configure=_configure_conn,
    )
    await _pool.open()
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    async with _pool.connection() as conn:
        await conn.execute(schema_sql)
    _available = True
    return True


async def shutdown_chat_sessions() -> None:
    global _pool, _available
    if _pool is not None:
        await _pool.close()
    _pool = None
    _available = False


def _require_pool() -> AsyncConnectionPool:
    if _pool is None or not _available:
        raise RuntimeError("chat sessions store is not initialized")
    return _pool


def _parse_thread_id(thread_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(thread_id)
    except ValueError as exc:
        raise ValueError(f"invalid thread_id: {thread_id}") from exc


def _parse_message_id(message_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(message_id)
    except ValueError:
        try:
            # CopilotKit ids are not always UUIDs — derive stable UUID v5
            return uuid.uuid5(uuid.NAMESPACE_URL, message_id)
        except Exception as exc:
            raise ValueError(f"invalid message id: {message_id}") from exc


async def list_sessions(*, user_id: str = DEFAULT_USER_ID, limit: int = 40) -> list[dict[str, Any]]:
    pool = _require_pool()
    limit = max(1, min(limit, 200))
    async with pool.connection() as conn:
        rows = await conn.execute(
            """
            SELECT
              c.thread_id,
              c.title,
              c.semantic_layer,
              c.created_at,
              c.updated_at,
              COUNT(*) FILTER (WHERE m.role = 'user') AS user_message_count
            FROM conversations c
            LEFT JOIN messages m ON m.thread_id = c.thread_id
            WHERE c.user_id = %s
            GROUP BY c.thread_id, c.title, c.semantic_layer, c.created_at, c.updated_at
            ORDER BY c.updated_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        records = await rows.fetchall()

    sessions: list[dict[str, Any]] = []
    for row in records:
        sessions.append(
            {
                "thread_id": str(row["thread_id"]),
                "title": row["title"],
                "first_timestamp": _iso(row["created_at"]),
                "last_timestamp": _iso(row["updated_at"]),
                "run_count": int(row["user_message_count"] or 0),
                "semantic_layer": row["semantic_layer"],
                "last_status": None,
            }
        )
    return sessions


async def get_messages(thread_id: str) -> list[dict[str, Any]]:
    tid = _parse_thread_id(thread_id)
    pool = _require_pool()
    async with pool.connection() as conn:
        cur = await conn.execute(
            """
            SELECT id, role, content
            FROM messages
            WHERE thread_id = %s
            ORDER BY seq ASC
            """,
            (tid,),
        )
        rows = await cur.fetchall()
    return [
        {"id": str(row["id"]), "role": row["role"], "content": row["content"]}
        for row in rows
    ]


async def conversation_exists(thread_id: str, *, user_id: str = DEFAULT_USER_ID) -> bool:
    tid = _parse_thread_id(thread_id)
    pool = _require_pool()
    async with pool.connection() as conn:
        cur = await conn.execute(
            "SELECT 1 FROM conversations WHERE thread_id = %s AND user_id = %s",
            (tid, user_id),
        )
        return await cur.fetchone() is not None


async def create_session(
    thread_id: str,
    *,
    user_id: str = DEFAULT_USER_ID,
    title: str = "New chat",
    semantic_layer: str | None = None,
) -> dict[str, Any]:
    tid = _parse_thread_id(thread_id)
    pool = _require_pool()
    async with pool.connection() as conn:
        await conn.execute(
            """
            INSERT INTO conversations (thread_id, user_id, title, semantic_layer)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (thread_id) DO NOTHING
            """,
            (tid, user_id, title[:TITLE_MAX_LEN], semantic_layer),
        )
    return {"thread_id": str(tid), "title": title[:TITLE_MAX_LEN]}


async def replace_messages(
    thread_id: str,
    messages: list[dict[str, Any]],
    *,
    user_id: str = DEFAULT_USER_ID,
    semantic_layer: str | None = None,
) -> int:
    if not messages:
        raise ValueError("messages must not be empty")

    tid = _parse_thread_id(thread_id)
    capped = messages[-MAX_MESSAGES_PER_THREAD:]
    title = _title_from_messages(capped)
    pool = _require_pool()

    async with pool.connection() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                INSERT INTO conversations (thread_id, user_id, title, semantic_layer, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (thread_id) DO UPDATE SET
                  title = EXCLUDED.title,
                  semantic_layer = COALESCE(EXCLUDED.semantic_layer, conversations.semantic_layer),
                  updated_at = NOW()
                """,
                (tid, user_id, title, semantic_layer),
            )
            await conn.execute("DELETE FROM messages WHERE thread_id = %s", (tid,))
            for seq, msg in enumerate(capped):
                role = msg.get("role")
                if role not in ("user", "assistant", "system"):
                    continue
                content = str(msg.get("content") or "").strip()
                if not content and role != "user":
                    continue
                if not content:
                    content = "(empty message)"
                mid = _parse_message_id(str(msg.get("id") or f"{thread_id}-{seq}"))
                await conn.execute(
                    """
                    INSERT INTO messages (id, thread_id, role, content, seq)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (mid, tid, role, content, seq),
                )

    return len(capped)


def _assistant_content_from_run(
    *,
    assistant_reply: str | None,
    sql_executions: list[dict[str, Any]] | None,
    status: str,
    error: str | None,
) -> str | None:
    if assistant_reply and assistant_reply.strip():
        return assistant_reply.strip()
    parts: list[str] = []
    if error:
        parts.append(f"**Error:** {error}")
    for step in sql_executions or []:
        sql = step.get("sql")
        if sql:
            parts.append(f"```sql\n{sql}\n```")
        if step.get("error"):
            parts.append(f"**SQL error:** {step['error']}")
        elif step.get("result_preview"):
            parts.append(str(step["result_preview"]))
    if parts:
        return "\n\n".join(parts)
    if status == "error":
        return "Run failed."
    return None


async def append_run_turn(
    thread_id: str,
    *,
    run_id: str,
    question: str | None,
    assistant_reply: str | None = None,
    semantic_layer: str | None = None,
    sql_executions: list[dict[str, Any]] | None = None,
    status: str = "ok",
    error: str | None = None,
    user_id: str = DEFAULT_USER_ID,
) -> int:
    """Append one user/assistant pair after an API agent run (idempotent by run_id)."""
    if not question and not assistant_reply:
        assistant_reply = _assistant_content_from_run(
            assistant_reply=assistant_reply,
            sql_executions=sql_executions,
            status=status,
            error=error,
        )
    if not question and not assistant_reply:
        return 0

    tid = _parse_thread_id(thread_id)
    user_mid = _parse_message_id(f"{run_id}-user")
    asst_mid = _parse_message_id(f"{run_id}-assistant")
    pool = _require_pool()

    async with pool.connection() as conn:
        async with conn.transaction():
            cur = await conn.execute(
                "SELECT id FROM messages WHERE thread_id = %s AND id = %s",
                (tid, user_mid),
            )
            if await cur.fetchone() is not None:
                return 0

            cur = await conn.execute(
                "SELECT COALESCE(MAX(seq), -1) AS max_seq FROM messages WHERE thread_id = %s",
                (tid,),
            )
            row = await cur.fetchone()
            next_seq = int(row["max_seq"]) + 1

            to_insert: list[tuple[Any, ...]] = []
            title = "New chat"
            if question and question.strip():
                title = _title_from_messages([{"role": "user", "content": question}])
                to_insert.append((user_mid, tid, "user", question.strip(), next_seq))
                next_seq += 1

            assistant_content = _assistant_content_from_run(
                assistant_reply=assistant_reply,
                sql_executions=sql_executions,
                status=status,
                error=error,
            )
            if assistant_content:
                to_insert.append((asst_mid, tid, "assistant", assistant_content, next_seq))

            if not to_insert:
                return 0

            await conn.execute(
                """
                INSERT INTO conversations (thread_id, user_id, title, semantic_layer, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (thread_id) DO UPDATE SET
                  title = CASE
                    WHEN EXCLUDED.title != 'New chat' THEN EXCLUDED.title
                    ELSE conversations.title
                  END,
                  semantic_layer = COALESCE(EXCLUDED.semantic_layer, conversations.semantic_layer),
                  updated_at = NOW()
                """,
                (tid, user_id, title, semantic_layer),
            )

            for mid, thread_uuid, role, content, seq in to_insert:
                await conn.execute(
                    """
                    INSERT INTO messages (id, thread_id, role, content, seq)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (thread_id, id) DO NOTHING
                    """,
                    (mid, thread_uuid, role, content, seq),
                )

            await conn.execute(
                """
                DELETE FROM messages AS m
                USING (
                  SELECT id FROM messages
                  WHERE thread_id = %s
                  ORDER BY seq DESC
                  OFFSET %s
                ) AS old
                WHERE m.id = old.id
                """,
                (tid, MAX_MESSAGES_PER_THREAD),
            )

    return len(to_insert)
