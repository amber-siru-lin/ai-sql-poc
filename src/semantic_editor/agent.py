"""Semantic layer editor Deep Agent graph."""

from __future__ import annotations

from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from config.settings import create_bedrock_chat

from src.semantic_editor.middleware import editor_system_prompt
from src.semantic_editor.prompts import EDITOR_BASE_PROMPT
from src.semantic_editor.tools import EDITOR_TOOLS

EDITOR_AGENT_NAME = "semantic_editor"
EDITOR_AGENT_DESCRIPTION = (
    "Semantic layer editor — MDL/YAML edits, audit-aware relationship fixes, Wren validate."
)


def build_editor_agent_graph(*, checkpointer=None):
    """Return the compiled LangGraph for the semantic layer editor agent."""
    if checkpointer is None:
        checkpointer = MemorySaver()
    model = create_bedrock_chat()
    return create_deep_agent(
        model=model,
        tools=EDITOR_TOOLS,
        system_prompt=EDITOR_BASE_PROMPT,
        middleware=[editor_system_prompt],
        checkpointer=checkpointer,
    )
