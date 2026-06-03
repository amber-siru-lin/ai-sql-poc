"""Build Wren MDL at API startup when missing (local dev only)."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

from src.check_setup import repo_root
from src.tools.wren_tools import MDL_MANIFEST, WREN_PROJECT_DIR, wren_cli_available

logger = logging.getLogger(__name__)


def _skip_wren_bootstrap() -> bool:
    if os.environ.get("WREN_SKIP_BOOTSTRAP", "").strip().lower() in ("1", "true", "yes"):
        return True
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("LAMBDA_TASK_ROOT"):
        return True
    if not WREN_PROJECT_DIR.is_dir():
        return True
    return False


def _sync_wren_profile(root: Path) -> bool:
    script = root / "scripts" / "sync_wren_profile.py"
    if not script.is_file():
        logger.warning("Wren bootstrap: missing %s", script)
        return False
    try:
        subprocess.run(
            [sys.executable, str(script)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return True
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "Wren profile sync failed (exit %s): %s",
            exc.returncode,
            (exc.stderr or exc.stdout or "").strip()[:500],
        )
    except Exception as exc:
        logger.warning("Wren profile sync failed: %s", exc)
    return False


def _run_wren_cmd(args: list[str], *, timeout: int) -> bool:
    try:
        proc = subprocess.run(
            ["wren", *args],
            cwd=WREN_PROJECT_DIR,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.stdout.strip():
            logger.info("wren %s: %s", " ".join(args), proc.stdout.strip()[:300])
        return True
    except subprocess.CalledProcessError as exc:
        logger.warning(
            "wren %s failed (exit %s): %s",
            " ".join(args),
            exc.returncode,
            (exc.stderr or exc.stdout or "").strip()[:500],
        )
    except subprocess.TimeoutExpired:
        logger.warning("wren %s timed out after %ss", " ".join(args), timeout)
    except FileNotFoundError:
        logger.warning("wren CLI not on PATH")
    except Exception as exc:
        logger.warning("wren %s failed: %s", " ".join(args), exc)
    return False


def ensure_wren_mdl_at_startup() -> None:
    """Sync Snowflake profile and run ``wren context build`` if ``target/mdl.json`` is missing."""
    if _skip_wren_bootstrap():
        return
    if not WREN_PROJECT_DIR.joinpath("wren_project.yml").is_file():
        logger.warning("Wren bootstrap skipped: missing wren/tpch/wren_project.yml")
        return
    if not wren_cli_available():
        logger.warning(
            "Wren bootstrap skipped: install wrenai — "
            "scripts/py -m pip install \"wrenai[snowflake,memory]\" pyyaml"
        )
        return
    if MDL_MANIFEST.is_file():
        logger.debug("Wren MDL already present at %s", MDL_MANIFEST)
        return

    root = repo_root()
    logger.info("Wren MDL missing — bootstrapping (sync profile + context build)")
    if not _sync_wren_profile(root):
        return

    profile = os.environ.get("WREN_PROFILE", "tpch-sf1")
    _run_wren_cmd(["context", "set-profile", profile], timeout=30)

    if not _run_wren_cmd(["context", "build"], timeout=300):
        return

    if MDL_MANIFEST.is_file():
        logger.info("Wren MDL ready: %s", MDL_MANIFEST)
    else:
        logger.warning("wren context build finished but %s not found", MDL_MANIFEST)

    if os.environ.get("WREN_BOOTSTRAP_MEMORY_INDEX", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        _run_wren_cmd(["memory", "index"], timeout=300)
