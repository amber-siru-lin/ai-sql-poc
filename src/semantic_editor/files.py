"""List, read, and write allowlisted semantic layer files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.semantic_editor.paths import (
    ROOT,
    SKIP_DIR_NAMES,
    SemanticPathError,
    default_tree_roots,
    normalize_relative_path,
    resolve_semantic_path,
)


def _rel_path(full: Path) -> str:
    return full.relative_to(ROOT).as_posix()


def list_semantic_files(*, root: str | None = None) -> dict[str, Any]:
    """Return editable files under allowlisted roots (optional single root filter)."""
    roots = list(default_tree_roots())
    if root is not None:
        root_norm = root.strip().replace("\\", "/").strip("/")
        if root_norm not in roots:
            raise SemanticPathError(
                f"root must be one of: {', '.join(default_tree_roots())}"
            )
        roots = [root_norm]

    files: list[dict[str, Any]] = []
    for root_name in roots:
        base = ROOT / root_name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            if any(part in SKIP_DIR_NAMES for part in path.parts):
                continue
            rel = _rel_path(path)
            try:
                normalize_relative_path(rel)
            except SemanticPathError:
                continue
            stat = path.stat()
            files.append(
                {
                    "path": rel,
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                }
            )

    return {"roots": default_tree_roots(), "files": files}


def read_semantic_file(path: str) -> dict[str, Any]:
    full = resolve_semantic_path(path)
    if not full.is_file():
        raise FileNotFoundError(path)
    content = full.read_text(encoding="utf-8")
    return {"path": normalize_relative_path(path), "content": content}


def write_semantic_file(path: str, content: str) -> dict[str, Any]:
    relative = normalize_relative_path(path)
    full = resolve_semantic_path(relative)
    full.parent.mkdir(parents=True, exist_ok=True)
    full.write_text(content, encoding="utf-8")
    return {"path": relative, "saved": True, "size": full.stat().st_size}
