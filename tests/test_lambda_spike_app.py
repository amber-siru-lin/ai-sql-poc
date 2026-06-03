"""Contract tests for Lambda spike FastAPI app."""

from fastapi.testclient import TestClient

from api.lambda_spike import app


def test_api_status_ok():
    client = TestClient(app)
    r = client.get("/api/status")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["agent"] == "nl2sql_assistant"


def test_copilotkit_info():
    client = TestClient(app)
    r = client.get("/copilotkit/info")
    assert r.status_code == 200
    assert r.json()["agents"] == {}


def test_agui_root_streams():
    client = TestClient(app)
    r = client.post("/")
    assert r.status_code == 200
    assert "text/event-stream" in r.headers.get("content-type", "")
