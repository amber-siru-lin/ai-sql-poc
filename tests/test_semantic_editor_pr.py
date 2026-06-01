"""Semantic editor PR draft and GitHub workflow."""

from __future__ import annotations

import json

import pytest

from src.semantic_editor.pr import (
    SemanticPrError,
    build_pr_body,
    build_pr_draft,
    collect_semantic_changes,
    create_semantic_pr,
    github_config,
    suggest_pr_title,
)


def test_suggest_pr_title_single_file():
    title = suggest_pr_title(["wren/tpch/relationships.yml"])
    assert title == "semantic(wren/tpch): update relationships"


def test_build_pr_body_includes_paths_and_test_plan():
    body = build_pr_body(["wren/tpch/relationships.yml"], audit_entry_ids=["abc123"])
    assert "wren/tpch/relationships.yml" in body
    assert "abc123" in body
    assert "wren context validate" in body


def test_build_pr_draft_requires_changes(monkeypatch):
    monkeypatch.setattr("src.semantic_editor.pr.collect_semantic_changes", lambda: [])
    with pytest.raises(SemanticPrError, match="No semantic layer changes"):
        build_pr_draft()


def test_build_pr_draft_from_explicit_paths(monkeypatch):
    monkeypatch.setattr(
        "src.semantic_editor.pr.github_config",
        lambda: {
            "configured": False,
            "token_present": False,
            "repo": "owner/repo",
            "default_branch": "main",
        },
    )
    monkeypatch.setattr("src.semantic_editor.pr.git_diff_stat", lambda paths: "1 file changed")
    draft = build_pr_draft(paths=["schema/tpch_sf1.md"])
    assert draft["title"].startswith("semantic(schema)")
    assert draft["paths"] == ["schema/tpch_sf1.md"]
    assert draft["base_branch"] == "main"
    assert "schema/tpch_sf1.md" in draft["body"]


def test_collect_semantic_changes_filters_allowlist(monkeypatch):
    monkeypatch.setattr(
        "src.semantic_editor.pr._git_lines",
        lambda *args: [
            " M wren/tpch/relationships.yml",
            " M src/agent_factory.py",
            "?? schema/note.md",
        ]
        if args[0] == "status"
        else [],
    )
    changed = collect_semantic_changes()
    assert changed == ["schema/note.md", "wren/tpch/relationships.yml"]


def test_create_semantic_pr_blocks_without_github_config(monkeypatch):
    monkeypatch.setattr(
        "src.semantic_editor.pr.github_config",
        lambda: {
            "configured": False,
            "token_present": False,
            "repo": "",
            "default_branch": "main",
        },
    )
    with pytest.raises(SemanticPrError, match="GitHub not configured"):
        create_semantic_pr(title="t", body="b", paths=["schema/tpch_sf1.md"])


def test_create_semantic_pr_blocks_forbidden_paths(monkeypatch):
    monkeypatch.setattr(
        "src.semantic_editor.pr.github_config",
        lambda: {
            "configured": True,
            "token_present": True,
            "repo": "owner/repo",
            "default_branch": "main",
        },
    )
    with pytest.raises(SemanticPrError, match="forbidden path"):
        create_semantic_pr(title="t", body="b", paths=["wren/tpch/profiles.yml"])


def test_create_semantic_pr_happy_path(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        "src.semantic_editor.pr.github_config",
        lambda: {
            "configured": True,
            "token_present": True,
            "repo": "owner/repo",
            "default_branch": "main",
        },
    )
    monkeypatch.setattr(
        "src.semantic_editor.pr.run_wren_validate",
        lambda: {"ok": True},
    )
    monkeypatch.setattr("src.semantic_editor.pr._ensure_branch", lambda **kwargs: None)
    monkeypatch.setattr("src.semantic_editor.pr._stage_paths", lambda paths: None)
    monkeypatch.setattr("src.semantic_editor.pr._has_staged_changes", lambda: True)
    monkeypatch.setattr("src.semantic_editor.pr._commit", lambda title, body: "deadbeef")
    monkeypatch.setattr("src.semantic_editor.pr._push_branch", lambda branch: None)
    monkeypatch.setattr(
        "src.semantic_editor.pr._create_github_pr",
        lambda **kwargs: {"number": 42, "html_url": "https://github.com/o/r/pull/42", "title": kwargs["title"]},
    )

    result = create_semantic_pr(
        title="semantic(wren/tpch): update relationships",
        body="body",
        paths=["wren/tpch/relationships.yml"],
        branch_name="feat/semantic-edit-test",
        require_validate=True,
    )
    assert result["ok"] is True
    assert result["pr_number"] == 42
    assert result["pr_url"].endswith("/pull/42")


def test_github_config_reads_env(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("GITHUB_REPO", "acme/widget")
    monkeypatch.setenv("GITHUB_DEFAULT_BRANCH", "develop")
    cfg = github_config()
    assert cfg["configured"] is True
    assert cfg["token_present"] is True
    assert cfg["repo"] == "acme/widget"
    assert cfg["default_branch"] == "develop"
    assert "secret" not in json.dumps(cfg)


def test_create_semantic_pr_requires_validate_for_wren_paths(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        "src.semantic_editor.pr.github_config",
        lambda: {
            "configured": True,
            "token_present": True,
            "repo": "owner/repo",
            "default_branch": "main",
        },
    )
    monkeypatch.setattr(
        "src.semantic_editor.pr.run_wren_validate",
        lambda: {"ok": False, "message": "bad yaml"},
    )
    with pytest.raises(SemanticPrError, match="Wren validate must pass"):
        create_semantic_pr(
            title="t",
            body="b",
            paths=["wren/tpch/relationships.yml"],
            require_validate=True,
        )
