"""Snowflake Cortex Analyst tool (placeholder until Semantic View is configured)."""

from __future__ import annotations

import os
from typing import Annotated

from langchain.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg

from src.semantic_layer.runtime import semantic_layer_from_config


def cortex_ready() -> tuple[bool, str]:
    view = os.environ.get("CORTEX_SEMANTIC_VIEW", "").strip()
    if not view:
        return False, "set CORTEX_SEMANTIC_VIEW=DB.SCHEMA.VIEW (not configured yet)"
    return False, "Cortex Analyst integration not implemented — placeholder only"


@tool
def ask_cortex_analyst(
    question: str,
    config: Annotated[RunnableConfig, InjectedToolArg],
) -> str:
    """Ask Snowflake Cortex Analyst using the configured Semantic View (placeholder)."""
    if semantic_layer_from_config(config) != "cortex":
        return "ERROR: Cortex Analyst is only available when semantic layer mode is Cortex."

    ready, msg = cortex_ready()
    return (
        f"CORTEX PLACEHOLDER: {msg}\n"
        f"Question was: {question.strip()}\n"
        "Switch to Off or Wren mode for live queries."
    )
