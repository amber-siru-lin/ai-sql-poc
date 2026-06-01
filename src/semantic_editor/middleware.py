"""LangChain middleware for semantic editor agent context."""

from __future__ import annotations

from langchain.agents.middleware import dynamic_prompt
from langchain.agents.middleware.types import ModelRequest
from langgraph.config import get_config

from src.semantic_editor.prompts import EDITOR_BASE_PROMPT


@dynamic_prompt
def editor_system_prompt(request: ModelRequest) -> str:
    """Append active file context from AG-UI forwarded props."""
    _ = request
    configurable = get_config().get("configurable") or {}
    active_file = configurable.get("active_file")
    active_content = configurable.get("active_file_content")
    parts = [EDITOR_BASE_PROMPT.rstrip()]
    if active_file:
        parts.append(f"\n## Active file in UI\n\nPath: `{active_file}`")
        if isinstance(active_content, str) and active_content.strip():
            preview = active_content
            if len(preview) > 8000:
                preview = preview[:8000] + "\n… (truncated)"
            parts.append(f"\n```\n{preview}\n```")
    return "\n".join(parts)
