"""Semantic layer mode types."""

from __future__ import annotations

from typing import Literal, get_args

SemanticLayerMode = Literal["off", "wren", "cortex"]

SEMANTIC_LAYER_MODES: tuple[SemanticLayerMode, ...] = get_args(SemanticLayerMode)

DEFAULT_SEMANTIC_LAYER: SemanticLayerMode = "off"


def normalize_semantic_layer(value: str | None) -> SemanticLayerMode:
    """Coerce API/UI input to a valid mode (defaults to off)."""
    if value in SEMANTIC_LAYER_MODES:
        return value  # type: ignore[return-value]
    return DEFAULT_SEMANTIC_LAYER
