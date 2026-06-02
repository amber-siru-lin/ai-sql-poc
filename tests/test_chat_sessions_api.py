"""Postgres chat sessions store and API route tests."""

from __future__ import annotations

import os
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL", "").strip(),
    reason="DATABASE_URL not set",
)


@pytest.fixture(scope="module")
def api_client():
    import asyncio

    from src.chat_sessions.routes import router
    from src.chat_sessions.store import init_chat_sessions_from_env

    asyncio.run(init_chat_sessions_from_env())

    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        yield client


def test_list_sessions_empty(api_client: TestClient):
    res = api_client.get("/api/sessions")
    assert res.status_code == 200
    assert "sessions" in res.json()


def test_create_and_round_trip_messages(api_client: TestClient):
    thread_id = str(uuid.uuid4())
    create = api_client.post(
        "/api/sessions",
        json={"thread_id": thread_id, "title": "New chat", "semantic_layer": "off"},
    )
    assert create.status_code == 200

    messages = [
        {"id": str(uuid.uuid4()), "role": "user", "content": "Hello"},
        {"id": str(uuid.uuid4()), "role": "assistant", "content": "Hi there"},
    ]
    put = api_client.put(
        f"/api/sessions/{thread_id}/messages",
        json={"messages": messages, "semantic_layer": "off"},
    )
    assert put.status_code == 200
    assert put.json()["saved"] == 2

    get = api_client.get(f"/api/sessions/{thread_id}/messages")
    assert get.status_code == 200
    body = get.json()
    assert body["thread_id"] == thread_id
    assert len(body["messages"]) == 2
    assert body["messages"][0]["role"] == "user"

    listed = api_client.get("/api/sessions?limit=10")
    assert listed.status_code == 200
    ids = [s["thread_id"] for s in listed.json()["sessions"]]
    assert thread_id in ids


def test_put_empty_messages_rejected(api_client: TestClient):
    thread_id = str(uuid.uuid4())
    res = api_client.put(
        f"/api/sessions/{thread_id}/messages",
        json={"messages": []},
    )
    assert res.status_code == 422


def test_invalid_thread_id(api_client: TestClient):
    res = api_client.get("/api/sessions/not-a-uuid/messages")
    assert res.status_code == 400


def test_replace_all_replaces_prior_messages(api_client: TestClient):
    thread_id = str(uuid.uuid4())
    api_client.post(
        "/api/sessions",
        json={"thread_id": thread_id, "title": "New chat", "semantic_layer": "off"},
    )
    api_client.put(
        f"/api/sessions/{thread_id}/messages",
        json={
            "messages": [{"id": str(uuid.uuid4()), "role": "user", "content": "first"}],
        },
    )
    api_client.put(
        f"/api/sessions/{thread_id}/messages",
        json={
            "messages": [
                {"id": str(uuid.uuid4()), "role": "user", "content": "second"},
                {"id": str(uuid.uuid4()), "role": "assistant", "content": "reply"},
            ],
        },
    )
    body = api_client.get(f"/api/sessions/{thread_id}/messages").json()
    assert len(body["messages"]) == 2
    assert body["messages"][0]["content"] == "second"


@pytest.fixture
def chat_store():
    import asyncio

    from src.chat_sessions import store as chat_store_mod
    from src.chat_sessions.store import init_chat_sessions_from_env

    asyncio.run(init_chat_sessions_from_env())
    return chat_store_mod


def test_append_run_turn_creates_messages(chat_store):
    import asyncio

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    async def _run():
        added = await chat_store.append_run_turn(
            thread_id,
            run_id=run_id,
            question="What is revenue?",
            assistant_reply="Revenue is $1M.",
            semantic_layer="off",
            status="ok",
        )
        assert added == 2
        messages = await chat_store.get_messages(thread_id)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "What is revenue?"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Revenue is $1M."

    asyncio.run(_run())


def test_append_run_turn_idempotent(chat_store):
    import asyncio

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    async def _run():
        first = await chat_store.append_run_turn(
            thread_id,
            run_id=run_id,
            question="Hello",
            assistant_reply="Hi",
        )
        second = await chat_store.append_run_turn(
            thread_id,
            run_id=run_id,
            question="Hello",
            assistant_reply="Hi",
        )
        assert first == 2
        assert second == 0
        assert len(await chat_store.get_messages(thread_id)) == 2

    asyncio.run(_run())


def test_append_run_turn_sql_fallback(chat_store):
    import asyncio

    thread_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    async def _run():
        added = await chat_store.append_run_turn(
            thread_id,
            run_id=run_id,
            question="Show orders",
            assistant_reply=None,
            sql_executions=[{"sql": "SELECT 1", "result_preview": "1 row"}],
            status="ok",
        )
        assert added == 2
        messages = await chat_store.get_messages(thread_id)
        assert "SELECT 1" in messages[1]["content"]

    asyncio.run(_run())
