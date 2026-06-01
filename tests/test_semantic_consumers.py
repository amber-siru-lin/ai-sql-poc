"""Semantic editor consumers manifest."""

from src.semantic_editor.consumers import build_consumers_response


def test_build_consumers_response_includes_wren():
    status = {
        "default": "off",
        "modes": ["off", "wren", "cortex"],
        "wren_ready": False,
        "wren_message": "test",
        "cortex_ready": False,
        "cortex_message": "stub",
    }
    payload = build_consumers_response(status)
    ids = {c["id"] for c in payload["consumers"]}
    assert ids >= {"wren", "off", "cortex", "chat"}
    wren = next(c for c in payload["consumers"] if c["id"] == "wren")
    assert wren["ready"] is False
    assert wren["ready_message"] == "test"
    assert any(p["path"] == "wren/tpch/relationships.yml" for p in wren["paths"])
