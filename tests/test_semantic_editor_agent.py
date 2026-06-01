"""Semantic editor agent tools and audit search."""

from src.audit_reader import search_audit_entries
from src.semantic_editor.tools import _enforce_limit_10, list_semantic_files_tool, read_semantic_file_tool


def test_enforce_limit_10_requires_limit():
    assert _enforce_limit_10("SELECT 1") is not None
    assert _enforce_limit_10("SELECT * FROM orders LIMIT 10") is None
    assert _enforce_limit_10("SELECT * FROM orders LIMIT 11") is not None


def test_enforce_limit_10_blocks_dml():
    assert _enforce_limit_10("DELETE FROM orders LIMIT 1") is not None


def test_list_semantic_files_tool():
    out = list_semantic_files_tool.invoke({})
    assert "wren/tpch/relationships.yml" in out


def test_read_semantic_file_tool():
    out = read_semantic_file_tool.invoke({"path": "wren/tpch/relationships.yml"})
    assert "path: wren/tpch/relationships.yml" in out


def test_search_audit_entries_no_crash():
    entries = search_audit_entries(query="orders", status="error", limit=5)
    assert isinstance(entries, list)
