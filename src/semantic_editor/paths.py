"""Allowlisted paths for semantic layer file read/write."""

from __future__ import annotations

from pathlib import Path

from src.check_setup import repo_root

ALLOWED_PREFIXES: tuple[str, ...] = ("wren/tpch/", "schema/", "semantic/")
EDITABLE_SUFFIXES: tuple[str, ...] = (".yml", ".yaml", ".md")
SKIP_DIR_NAMES: frozenset[str] = frozenset({".wren", "target", "__pycache__", ".git", "node_modules"})

ROOT = repo_root()


class SemanticPathError(ValueError):
    """Invalid or disallowed semantic editor path."""


def normalize_relative_path(raw: str) -> str:
    """Return a safe repo-relative POSIX path or raise."""
    text = raw.strip().replace("\\", "/")
    if not text or text.startswith("/") or ".." in text.split("/"):
        raise SemanticPathError("path must be relative with no parent segments")
    if not any(text.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        raise SemanticPathError(
            f"path must start with one of: {', '.join(ALLOWED_PREFIXES)}"
        )
    suffix = Path(text).suffix.lower()
    if suffix not in EDITABLE_SUFFIXES and not text.endswith(".gitkeep"):
        raise SemanticPathError(
            f"path must end with {', '.join(EDITABLE_SUFFIXES)} or .gitkeep"
        )
    return text


def resolve_semantic_path(raw: str) -> Path:
    """Resolve allowlisted path under repo root."""
    relative = normalize_relative_path(raw)
    full = (ROOT / relative).resolve()
    if not str(full).startswith(str(ROOT.resolve())):
        raise SemanticPathError("path escapes repository root")
    return full


def default_tree_roots() -> list[str]:
    return ["wren/tpch", "schema", "semantic"]
