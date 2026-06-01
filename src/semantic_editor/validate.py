"""Run Wren context validate for the TPCH MDL project."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from src.tools.wren_tools import WREN_PROJECT_DIR, wren_cli_available


def run_wren_validate(*, timeout_seconds: int = 120) -> dict[str, Any]:
    """Execute ``wren context validate`` in ``wren/tpch``."""
    if not wren_cli_available():
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "message": "wren CLI not on PATH (pip install 'wrenai[snowflake,memory]')",
        }
    if not WREN_PROJECT_DIR.joinpath("wren_project.yml").is_file():
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "message": "missing wren/tpch/wren_project.yml",
        }

    try:
        proc = subprocess.run(
            ["wren", "context", "validate"],
            cwd=WREN_PROJECT_DIR,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "message": f"validate timed out after {timeout_seconds}s",
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "message": "wren CLI not found on PATH",
        }

    ok = proc.returncode == 0
    return {
        "ok": ok,
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "message": "ok" if ok else "wren context validate failed",
    }
