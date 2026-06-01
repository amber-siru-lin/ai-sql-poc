"""Wren AI semantic layer tools (main branch — MDL + CLI)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Annotated

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from src.check_setup import repo_root
from src.semantic_layer.retry_policy import (
    check_sql_attempt_allowed,
    register_sql_failure,
    reset_sql_attempts,
)
from src.semantic_layer.runtime import semantic_layer_from_config

WREN_PROJECT_DIR = repo_root() / "wren" / "tpch"
MDL_MANIFEST = WREN_PROJECT_DIR / "target" / "mdl.json"


def wren_project_dir() -> Path:
    return WREN_PROJECT_DIR


def wren_cli_available() -> bool:
    return shutil.which("wren") is not None


def wren_ready() -> tuple[bool, str]:
    if not WREN_PROJECT_DIR.joinpath("wren_project.yml").is_file():
        return False, "missing wren/tpch/wren_project.yml"
    if not wren_cli_available():
        return False, "wren CLI not on PATH (pip install 'wrenai[snowflake,memory]')"
    if not MDL_MANIFEST.is_file():
        return False, "MDL not built — run: cd wren/tpch && wren context build"
    return True, "ok"


def _require_wren_mode(config: RunnableConfig | None) -> str | None:
    if semantic_layer_from_config(config) != "wren":
        return "ERROR: Wren tools are only available when semantic layer mode is Wren."
    ready, msg = wren_ready()
    if not ready:
        return f"ERROR: Wren not ready — {msg}"
    return None


def _run_wren(args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["wren", *args],
            cwd=WREN_PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        return "WREN ERROR: command timed out after 120s"
    except FileNotFoundError:
        return "WREN ERROR: wren CLI not found on PATH"
    except Exception as exc:
        return f"WREN ERROR: {exc}"

    out = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    if proc.returncode != 0:
        return f"WREN ERROR (exit {proc.returncode}):\n{err or out}"
    return out or "(no output)"


@tool
def wren_dry_plan(
    sql: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Preview SQL expanded through the Wren MDL semantic layer without executing."""
    if block := _require_wren_mode(config):
        return block
    return _run_wren(["dry-plan", "--sql", sql.strip()])


@tool
def wren_run_sql(
    sql: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Execute SQL written against Wren MDL model names; returns table output."""
    if block := _require_wren_mode(config):
        return block
    if block := check_sql_attempt_allowed(config, tool_name="wren_run_sql"):
        return block
    result = _run_wren(["--sql", sql.strip(), "-o", "json"])
    if "WREN ERROR" in result or result.startswith("ERROR"):
        return register_sql_failure(config, result, tool_name="wren_run_sql")
    reset_sql_attempts(config)
    return result


@tool
def wren_memory_fetch(
    question: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Retrieve relevant MDL schema context and instructions for a natural-language question."""
    if block := _require_wren_mode(config):
        return block
    return _run_wren(["memory", "fetch", "-q", question.strip()])
