"""Static manifest of semantic-layer consumers merged with live readiness."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.tools.cortex_tools import cortex_ready
from src.tools.wren_tools import wren_ready

ROOT = Path(__file__).resolve().parent.parent.parent


def _path_entry(relative: str, *, role: str) -> dict[str, Any]:
    full = ROOT / relative
    return {
        "path": relative,
        "role": role,
        "exists": full.is_file(),
    }


def _consumer_manifest() -> list[dict[str, Any]]:
    return [
        {
            "id": "wren",
            "name": "Wren AI",
            "mode": "wren",
            "description": (
                "MDL models and relationships; expanded SQL via wren context build "
                "(target/mdl.json is gitignored)."
            ),
            "paths": [
                _path_entry("wren/tpch/wren_project.yml", role="project"),
                _path_entry("wren/tpch/relationships.yml", role="relationships"),
                _path_entry("wren/tpch/models/customer/metadata.yml", role="model"),
                _path_entry("wren/tpch/models/orders/metadata.yml", role="model"),
                _path_entry("wren/tpch/models/nation/metadata.yml", role="model"),
                _path_entry("wren/tpch/instructions.md", role="instructions"),
            ],
            "tools": ["wren_dry_plan", "wren_run_sql", "wren_memory_fetch"],
            "build_artifact": "wren/tpch/target/mdl.json",
        },
        {
            "id": "off",
            "name": "Off (markdown schema)",
            "mode": "off",
            "description": "Prompt-backed TPCH schema summary for raw Snowflake SQL.",
            "paths": [
                _path_entry("schema/tpch_sf1.md", role="schema"),
            ],
            "tools": ["get_schema_summary", "execute_snowflake_sql"],
        },
        {
            "id": "cortex",
            "name": "Snowflake Cortex Analyst",
            "mode": "cortex",
            "description": (
                "Semantic View YAML (planned under semantic/cortex/). "
                "Stub until cortex_ready."
            ),
            "paths": [
                _path_entry("semantic/cortex/.gitkeep", role="placeholder"),
            ],
            "tools": ["ask_cortex_analyst"],
        },
        {
            "id": "chat",
            "name": "NL→SQL chat (CopilotKit)",
            "mode": "all",
            "description": (
                "Uses whichever mode is selected in the sidebar Semantics toggle; "
                "records semantic_layer on each audit run."
            ),
            "paths": [
                _path_entry("src/semantic_layer/prompts.py", role="prompts"),
            ],
            "tools": [],
        },
    ]


def build_consumers_response(semantic_layer_status: dict[str, Any]) -> dict[str, Any]:
    """Return consumers list with ready flags from /api/status semantic_layer block."""
    wren_ok = bool(semantic_layer_status.get("wren_ready"))
    wren_msg = str(semantic_layer_status.get("wren_message") or "")
    cortex_ok = bool(semantic_layer_status.get("cortex_ready"))
    cortex_msg = str(semantic_layer_status.get("cortex_message") or "")

    consumers: list[dict[str, Any]] = []
    for raw in _consumer_manifest():
        entry = dict(raw)
        cid = entry["id"]
        if cid == "wren":
            entry["ready"] = wren_ok
            entry["ready_message"] = wren_msg
        elif cid == "cortex":
            entry["ready"] = cortex_ok
            entry["ready_message"] = cortex_msg
        else:
            entry["ready"] = True
            entry["ready_message"] = ""
        consumers.append(entry)

    return {
        "repo_root": str(ROOT),
        "semantic_layer": semantic_layer_status,
        "consumers": consumers,
    }
