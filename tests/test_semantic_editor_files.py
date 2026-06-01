"""Semantic editor path allowlist and file I/O."""

import pytest

from src.semantic_editor.files import list_semantic_files, read_semantic_file, write_semantic_file
from src.semantic_editor.paths import SemanticPathError, normalize_relative_path


def test_normalize_rejects_traversal():
    with pytest.raises(SemanticPathError):
        normalize_relative_path("../etc/passwd")


def test_normalize_rejects_outside_prefix():
    with pytest.raises(SemanticPathError):
        normalize_relative_path("src/agent_factory.py")


def test_list_semantic_files_includes_relationships():
    payload = list_semantic_files(root="wren/tpch")
    paths = {f["path"] for f in payload["files"]}
    assert "wren/tpch/relationships.yml" in paths


def test_read_and_write_roundtrip(tmp_path, monkeypatch):
    import src.semantic_editor.files as files_mod
    import src.semantic_editor.paths as paths_mod

    rel = "schema/test_editor_roundtrip.md"
    monkeypatch.setattr(paths_mod, "ROOT", tmp_path)
    monkeypatch.setattr(files_mod, "ROOT", tmp_path)
    (tmp_path / "schema").mkdir()
    write_semantic_file(rel, "# test\n")
    out = read_semantic_file(rel)
    assert out["content"] == "# test\n"
    (tmp_path / "schema" / "test_editor_roundtrip.md").unlink()
