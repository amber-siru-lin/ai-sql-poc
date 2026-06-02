"""FastAPI routes for Postgres chat sessions."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.chat_sessions.store import (
    create_session,
    get_messages,
    list_sessions,
    replace_messages,
    sessions_available,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class StoredMessage(BaseModel):
    id: str
    role: str
    content: str


class CreateSessionRequest(BaseModel):
    thread_id: str
    title: str = "New chat"
    semantic_layer: str | None = None


class ReplaceMessagesRequest(BaseModel):
    messages: list[StoredMessage] = Field(min_length=1)
    semantic_layer: str | None = None


def _require_sessions_store() -> None:
    if not sessions_available():
        raise HTTPException(
            status_code=503,
            detail="Chat sessions store unavailable — set DATABASE_URL and ensure Postgres is running",
        )


@router.get("")
async def sessions_list(limit: int = 40):
    _require_sessions_store()
    return {"sessions": await list_sessions(limit=limit)}


@router.post("")
async def sessions_create(body: CreateSessionRequest):
    _require_sessions_store()
    try:
        result = await create_session(
            body.thread_id,
            title=body.title,
            semantic_layer=body.semantic_layer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result


@router.get("/{thread_id}/messages")
async def sessions_get_messages(thread_id: str):
    _require_sessions_store()
    try:
        messages = await get_messages(thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"thread_id": thread_id, "messages": messages}


@router.put("/{thread_id}/messages")
async def sessions_put_messages(thread_id: str, body: ReplaceMessagesRequest):
    _require_sessions_store()
    try:
        saved = await replace_messages(
            thread_id,
            [m.model_dump() for m in body.messages],
            semantic_layer=body.semantic_layer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"thread_id": thread_id, "saved": saved}
