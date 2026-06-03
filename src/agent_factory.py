"""Shared Deep Agent graph for CLI and CopilotKit API."""

from __future__ import annotations

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from config.settings import create_bedrock_chat, dataset_label
from src.semantic_layer.middleware import semantic_layer_system_prompt
from src.semantic_layer.prompts import get_system_prompt
from src.semantic_layer.types import DEFAULT_SEMANTIC_LAYER, SemanticLayerMode
from src.tools.cortex_tools import ask_cortex_analyst
from src.tools.snowflake_tools import execute_snowflake_sql, get_schema_summary
from src.tools.wren_tools import wren_dry_plan, wren_memory_fetch, wren_run_sql

AGENT_NAME = "nl2sql_assistant"
AGENT_DESCRIPTION = (
    f"{dataset_label()} analyst — natural language to SQL with optional Wren semantic layer."
)

ALL_TOOLS = [
    get_schema_summary,
    execute_snowflake_sql,
    wren_dry_plan,
    wren_run_sql,
    wren_memory_fetch,
    ask_cortex_analyst,
]


def build_agent_graph(
    semantic_layer: SemanticLayerMode = DEFAULT_SEMANTIC_LAYER,
    *,
    checkpointer=None,
):
    """Return the compiled LangGraph used by CLI and FastAPI.

    ``semantic_layer`` selects the system prompt. Per-request mode for the API
    comes from AG-UI ``forwarded_props`` → ``config.configurable``; tools enforce
    mode at call time.

    Pass ``checkpointer`` for API (Postgres pool) or omit for CLI (MemorySaver).
    """
    if checkpointer is None:
        checkpointer = MemorySaver()
    model = create_bedrock_chat()
    return create_deep_agent(
        model=model,
        tools=ALL_TOOLS,
        system_prompt=get_system_prompt(semantic_layer),
        middleware=[semantic_layer_system_prompt],
        checkpointer=checkpointer,
    )
