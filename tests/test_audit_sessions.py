"""Audit session listing by source."""

from src.audit_reader import list_audit_sessions, read_audit_entries


def test_read_audit_entries_filters_by_source(monkeypatch):
    entries = [
        {"thread_id": "a", "source": "api", "timestamp": "2026-06-01T12:00:00Z"},
        {"thread_id": "b", "source": "semantic_editor", "timestamp": "2026-06-01T13:00:00Z"},
    ]
    monkeypatch.setattr("src.audit_reader._read_local_entries", lambda **kwargs: entries)

    api_only = read_audit_entries(limit=10, source="api")
    editor_only = read_audit_entries(limit=10, source="semantic_editor")

    assert len(api_only) == 1
    assert api_only[0]["source"] == "api"
    assert len(editor_only) == 1
    assert editor_only[0]["source"] == "semantic_editor"


def test_list_audit_sessions_filters_by_source(monkeypatch):
    entries = [
        {
            "thread_id": "chat-1",
            "source": "api",
            "timestamp": "2026-06-01T12:00:00Z",
            "question": "revenue?",
            "status": "ok",
            "semantic_layer": "wren",
        },
        {
            "thread_id": "editor-1",
            "source": "semantic_editor",
            "timestamp": "2026-06-01T13:00:00Z",
            "question": "fix orders join",
            "status": "ok",
            "semantic_layer": "editor",
            "active_file": "wren/tpch/relationships.yml",
        },
    ]
    monkeypatch.setattr("src.audit_reader.read_audit_entries", lambda **kwargs: entries)

    chat = list_audit_sessions(limit=10, source="api")
    editor = list_audit_sessions(limit=10, source="semantic_editor")

    assert len(chat) == 1
    assert chat[0]["thread_id"] == "chat-1"
    assert len(editor) == 1
    assert editor[0]["thread_id"] == "editor-1"
    assert editor[0]["active_file"] == "wren/tpch/relationships.yml"
