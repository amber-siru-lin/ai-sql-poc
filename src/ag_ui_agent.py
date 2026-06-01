"""AG-UI LangGraph agent with per-run semantic_layer in config."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from ag_ui.core import RunAgentInput
from ag_ui_langgraph.agent import LangGraphAgent
from langchain_core.runnables import ensure_config

from src.semantic_layer.retry_policy import GRAPH_RECURSION_LIMIT
from src.semantic_layer.types import normalize_semantic_layer


class SemanticLayerLangGraphAgent(LangGraphAgent):
    """Injects ``semantic_layer`` from AG-UI ``forwarded_props`` into RunnableConfig."""

    async def prepare_stream(self, input, agent_state, config):
        forwarded = input.forwarded_props or {}
        mode = normalize_semantic_layer(forwarded.get("semantic_layer"))
        config = ensure_config(config)
        configurable = dict(config.get("configurable") or {})
        configurable["semantic_layer"] = mode
        thread_id = getattr(input, "thread_id", None) or getattr(input, "run_id", None)
        if thread_id:
            configurable["thread_id"] = str(thread_id)
        config["configurable"] = configurable
        config["recursion_limit"] = GRAPH_RECURSION_LIMIT
        return await super().prepare_stream(input, agent_state, config)
