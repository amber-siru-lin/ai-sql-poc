"""LangChain middleware for per-run semantic layer system prompts."""

from __future__ import annotations

from langchain.agents.middleware import dynamic_prompt
from langchain.agents.middleware.types import ModelRequest
from langgraph.config import get_config

from src.semantic_layer.prompts import get_system_prompt
from src.semantic_layer.types import normalize_semantic_layer


@dynamic_prompt
def semantic_layer_system_prompt(request: ModelRequest) -> str:
    """System prompt from AG-UI ``forwarded_props.semantic_layer`` → configurable."""
    _ = request  # available for future state-based customization
    configurable = (get_config().get("configurable") or {})
    mode = normalize_semantic_layer(configurable.get("semantic_layer"))
    return get_system_prompt(mode)
