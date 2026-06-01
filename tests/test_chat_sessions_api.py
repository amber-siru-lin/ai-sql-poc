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
