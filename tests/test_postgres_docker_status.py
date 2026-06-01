"""Postgres / Docker status helper."""

from src.postgres_docker_status import postgres_docker_status


def test_postgres_docker_status_not_configured(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr("src.postgres_docker_status.checkpoint_backend", lambda: "memory")
    monkeypatch.setattr("src.postgres_docker_status._docker_container_state", lambda: None)
    monkeypatch.setattr("src.postgres_docker_status._docker_cli_available", lambda: False)
    out = postgres_docker_status()
    assert out["status"] == "not_configured"
    assert out["configured"] is False
