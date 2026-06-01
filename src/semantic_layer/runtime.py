"""Read semantic layer mode from LangGraph / LangChain tool config."""

from __future__ import annotations

from langchain_core.runnables import RunnableConfig

from src.semantic_layer.types import SemanticLayerMode, normalize_semantic_layer


def semantic_layer_from_config(config: RunnableConfig | None) -> SemanticLayerMode:
    if not config:
        return "off"
    configurable = config.get("configurable") or {}
    return normalize_semantic_layer(configurable.get("semantic_layer"))
