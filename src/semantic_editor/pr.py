"""Git branch/commit and GitHub PR workflow for semantic layer edits."""

from __future__ import annotations

import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from src.semantic_editor.paths import ROOT, SemanticPathError, normalize_relative_path
from src.semantic_editor.validate import run_wren_validate

FORBIDDEN_PATH_FRAGMENTS: tuple[str, ...] = (
    ".env",
    "profiles.yml",
    "profiles.local.yml",
    "snowflake_config.py",
)

GITHUB_API_VERSION = "2022-11-28"


class SemanticPrError(ValueError):
    """PR workflow failed with a user-facing message."""


def github_config() -> dict[str, Any]:
    """Return GitHub settings from env (token never included in responses)."""
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPO", "").strip() or _repo_from_git_remote()
    base = os.environ.get("GITHUB_DEFAULT_BRANCH", "").strip() or _detect_default_branch()
    return {
        "configured": bool(token and repo),
        "token_present": bool(token),
        "repo": repo,
        "default_branch": base,
    }


def build_pr_draft(
    *,
    paths: list[str] | None = None,
    audit_entry_ids: list[str] | None = None,
    base_branch: str | None = None,
) -> dict[str, Any]:
    """Suggest PR title/body from git diff without mutating git state."""
    cfg = github_config()
    changed = _normalize_path_list(paths) if paths else collect_semantic_changes()
    if not changed:
        raise SemanticPrError("No semantic layer changes to include in a PR")

    base = (base_branch or cfg["default_branch"]).strip()
    return {
        "title": suggest_pr_title(changed),
        "body": build_pr_body(changed, audit_entry_ids=audit_entry_ids),
        "paths": changed,
        "base_branch": base,
        "branch_name": suggest_branch_name(),
        "github": {
            "configured": cfg["configured"],
            "repo": cfg["repo"],
            "default_branch": cfg["default_branch"],
        },
        "diff_stat": git_diff_stat(changed),
    }


def create_semantic_pr(
    *,
    title: str,
    body: str,
    paths: list[str] | None = None,
    base_branch: str | None = None,
    branch_name: str | None = None,
    audit_entry_ids: list[str] | None = None,
    require_validate: bool = True,
) -> dict[str, Any]:
    """Create branch, commit allowlisted paths, push, and open a GitHub PR."""
    cfg = github_config()
    if not cfg["configured"]:
        raise SemanticPrError(
            "GitHub not configured — set GITHUB_TOKEN and GITHUB_REPO in .env"
        )

    changed = _normalize_path_list(paths) if paths else collect_semantic_changes()
    if not changed:
        raise SemanticPrError("No semantic layer changes to commit")

    _assert_paths_allowed(changed)

    base = (base_branch or cfg["default_branch"]).strip()
    branch = (branch_name or suggest_branch_name()).strip()
    _assert_branch_name(branch)

    if require_validate and _has_wren_paths(changed):
        validation = run_wren_validate()
        if not validation.get("ok"):
            raise SemanticPrError(
                "Wren validate must pass before opening a PR — fix MDL errors first"
            )

    commit_title = title.strip() or suggest_pr_title(changed)
    commit_body = body.strip() or build_pr_body(changed, audit_entry_ids=audit_entry_ids)

    _ensure_branch(base_branch=base, branch_name=branch)
    _stage_paths(changed)
    if not _has_staged_changes():
        raise SemanticPrError("Nothing staged to commit — save files first")

    commit_sha = _commit(commit_title, commit_body)
    _push_branch(branch)
    pr = _create_github_pr(
        token=os.environ["GITHUB_TOKEN"].strip(),
        repo=cfg["repo"],
        title=commit_title,
        body=commit_body,
        head=branch,
        base=base,
    )

    return {
        "ok": True,
        "branch": branch,
        "base_branch": base,
        "commit_sha": commit_sha,
        "paths": changed,
        "pr_number": pr.get("number"),
        "pr_url": pr.get("html_url"),
        "pr_title": pr.get("title"),
    }


def collect_semantic_changes() -> list[str]:
    """Return allowlisted repo-relative paths with uncommitted changes."""
    candidates: set[str] = set()
    for line in _git_lines("status", "--porcelain"):
        if len(line) < 4:
            continue
        path = line[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1].strip()
        candidates.add(path)
    candidates.update(_git_lines("diff", "--name-only"))
    candidates.update(_git_lines("diff", "--cached", "--name-only"))

    changed: list[str] = []
    for path in sorted(candidates):
        try:
            normalized = normalize_relative_path(path)
        except SemanticPathError:
            continue
        if normalized not in changed:
            changed.append(normalized)
    return changed


def suggest_pr_title(paths: list[str]) -> str:
    scope = "wren/tpch" if any(p.startswith("wren/tpch/") for p in paths) else paths[0].split("/")[0]
    if len(paths) == 1:
        suffix = _path_stem(paths[0])
        return f"semantic({scope}): update {suffix}"
    return f"semantic({scope}): update {len(paths)} files"


def suggest_branch_name() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"feat/semantic-edit-{stamp}"


def build_pr_body(
    paths: list[str],
    *,
    audit_entry_ids: list[str] | None = None,
) -> str:
    lines = [
        "## Summary",
        "",
        "Semantic layer edits from the in-app editor:",
        "",
    ]
    for path in paths:
        lines.append(f"- `{path}`")
    lines.extend(["", "## Diff stat", "", "```", git_diff_stat(paths).strip() or "(no diff)", "```"])
    if audit_entry_ids:
        lines.extend(["", "## Audit context", ""])
        for entry_id in audit_entry_ids:
            lines.append(f"- Audit entry `{entry_id}`")
    lines.extend(
        [
            "",
            "## Test plan",
            "",
            "- [ ] `wren context validate` passes",
            "- [ ] Manual Wren chat question against updated MDL",
        ]
    )
    return "\n".join(lines)


def git_diff_stat(paths: list[str]) -> str:
    if not paths:
        return ""
    result = _git("diff", "--stat", "--", *paths)
    if result.stdout.strip():
        return result.stdout.strip()
    result = _git("diff", "--stat", "--cached", "--", *paths)
    return result.stdout.strip()


def _path_stem(path: str) -> str:
    name = path.rsplit("/", 1)[-1]
    for suffix in (".yml", ".yaml", ".md"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


def _normalize_path_list(paths: list[str]) -> list[str]:
    normalized: list[str] = []
    for raw in paths:
        normalized.append(normalize_relative_path(raw))
    return normalized


def _assert_paths_allowed(paths: list[str]) -> None:
    for path in paths:
        normalize_relative_path(path)
        lowered = path.lower()
        for forbidden in FORBIDDEN_PATH_FRAGMENTS:
            if forbidden in lowered:
                raise SemanticPrError(f"Refusing to PR forbidden path: {path}")


def _has_wren_paths(paths: list[str]) -> bool:
    return any(p.startswith("wren/tpch/") for p in paths)


def _assert_branch_name(branch: str) -> None:
    if not branch or branch.startswith("-") or ".." in branch or branch.endswith("/"):
        raise SemanticPrError("Invalid branch name")
    if not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
        raise SemanticPrError("Branch name contains invalid characters")


def _repo_from_git_remote() -> str:
    result = _git("remote", "get-url", "origin")
    if result.returncode != 0:
        return ""
    url = result.stdout.strip()
    if url.startswith("git@"):
        # git@github.com:owner/repo.git
        match = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
        return match.group(1) if match else ""
    match = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?$", url)
    return match.group(1) if match else ""


def _detect_default_branch() -> str:
    env = os.environ.get("GITHUB_DEFAULT_BRANCH", "").strip()
    if env:
        return env
    result = _git("symbolic-ref", "refs/remotes/origin/HEAD")
    if result.returncode == 0:
        ref = result.stdout.strip()
        if ref:
            return ref.rsplit("/", 1)[-1]
    for candidate in ("main", "master"):
        probe = _git("rev-parse", "--verify", f"origin/{candidate}")
        if probe.returncode == 0:
            return candidate
    return "main"


def _git_lines(*args: str) -> list[str]:
    result = _git(*args)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _ensure_branch(*, base_branch: str, branch_name: str) -> None:
    del base_branch  # PR base is set on GitHub; branch is created from current HEAD.
    current = _git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if current == branch_name:
        return

    checkout = _git("checkout", "-b", branch_name)
    if checkout.returncode != 0:
        existing = _git("checkout", branch_name)
        if existing.returncode != 0:
            detail = (checkout.stderr or checkout.stdout).strip()
            raise SemanticPrError(f"Could not create branch {branch_name}: {detail}")


def _stage_paths(paths: list[str]) -> None:
    add = _git("add", "--", *paths)
    if add.returncode != 0:
        raise SemanticPrError(f"git add failed: {add.stderr.strip()}")


def _has_staged_changes() -> bool:
    result = _git("diff", "--cached", "--quiet")
    return result.returncode != 0


def _commit(title: str, body: str) -> str:
    message = title if not body.strip() else f"{title}\n\n{body}"
    commit = _git("commit", "-m", message)
    if commit.returncode != 0:
        raise SemanticPrError(f"git commit failed: {commit.stderr.strip()}")
    sha = _git("rev-parse", "HEAD").stdout.strip()
    return sha


def _push_branch(branch: str) -> None:
    push = _git("push", "-u", "origin", branch)
    if push.returncode != 0:
        detail = (push.stderr or push.stdout).strip()
        if "Authentication failed" in detail or "403" in detail:
            raise SemanticPrError("Git push rejected — check GITHUB_TOKEN repo scope")
        raise SemanticPrError(f"git push failed: {detail}")


def _create_github_pr(
    *,
    token: str,
    repo: str,
    title: str,
    body: str,
    head: str,
    base: str,
) -> dict[str, Any]:
    url = f"https://api.github.com/repos/{repo}/pulls"
    payload = {"title": title, "body": body, "head": head, "base": base}
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
            "Content-Type": "application/json",
            "User-Agent": "ai-sql-poc-semantic-editor",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        message = detail
        try:
            parsed = json.loads(detail)
            message = parsed.get("message") or detail
            if isinstance(parsed.get("errors"), list) and parsed["errors"]:
                message = f"{message}: {parsed['errors'][0]}"
        except json.JSONDecodeError:
            pass
        if exc.code == 401:
            raise SemanticPrError("GitHub authentication failed — check GITHUB_TOKEN") from exc
        if exc.code == 422:
            raise SemanticPrError(f"GitHub rejected PR: {message}") from exc
        raise SemanticPrError(f"GitHub API error ({exc.code}): {message}") from exc
    except urllib.error.URLError as exc:
        raise SemanticPrError(f"Could not reach GitHub API: {exc.reason}") from exc
