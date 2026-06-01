"""AG-UI LangGraph agent with per-run semantic_layer in config."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncGenerator

from ag_ui.core import RunAgentInput
from ag_ui_langgraph.agent import LangGraphAgent
from langchain_core.runnables import ensure_config

from src.audit_extract import extract_sql_executions, last_user_question
from src.audit_logger import build_audit_record, write_audit_record
from src.semantic_layer.retry_policy import GRAPH_RECURSION_LIMIT
from src.semantic_layer.types import normalize_semantic_layer

logger = logging.getLogger(__name__)


def _semantic_layer_from_forwarded(forwarded: dict) -> str:
    """UI sends camelCase ``semanticLayer``; accept snake_case too."""
    raw = forwarded.get("semantic_layer")
    if raw is None:
        raw = forwarded.get("semanticLayer")
    return normalize_semantic_layer(raw)


class SemanticLayerLangGraphAgent(LangGraphAgent):
    """Injects ``semantic_layer`` from AG-UI ``forwarded_props`` into RunnableConfig."""

    async def prepare_stream(self, input, agent_state, config):
        forwarded = input.forwarded_props or {}
        mode = _semantic_layer_from_forwarded(forwarded)
        config = ensure_config(config)
        configurable = dict(config.get("configurable") or {})
        configurable["semantic_layer"] = mode
        thread_id = getattr(input, "thread_id", None) or getattr(input, "run_id", None)
        if thread_id:
            configurable["thread_id"] = str(thread_id)
        config["configurable"] = configurable
        config["recursion_limit"] = GRAPH_RECURSION_LIMIT
        return await super().prepare_stream(input, agent_state, config)

    async def run(self, input: RunAgentInput) -> AsyncGenerator:
        forwarded = input.forwarded_props or {}
        semantic_layer = _semantic_layer_from_forwarded(forwarded)
        thread_id = input.thread_id or str(uuid.uuid4())
        run_id = input.run_id
        question = last_user_question(input.messages or [])
        started = time.perf_counter()
        status = "ok"
        error: str | None = None

        try:
            async for event in super().run(input):
                yield event
        except Exception as exc:
            status = "error"
            error = str(exc)
            raise
        finally:
            duration_ms = int((time.perf_counter() - started) * 1000)
            try:
                config = ensure_config(self.config.copy() if self.config else {})
                configurable = dict(config.get("configurable") or {})
                configurable["thread_id"] = thread_id
                configurable["semantic_layer"] = semantic_layer
                config["configurable"] = configurable
                state = await self.graph.aget_state(config)
                messages = list(state.values.get("messages", [])) if state and state.values else []
                if not question:
                    question = last_user_question(messages)
                record = build_audit_record(
                    thread_id=thread_id,
                    run_id=run_id,
                    semantic_layer=semantic_layer,
                    question=question,
                    sql_executions=extract_sql_executions(messages),
                    status=status,
                    duration_ms=duration_ms,
                    error=error,
                    source="api",
                )
                destinations = write_audit_record(record)
                logger.info(
                    "audit run_id=%s thread_id=%s status=%s local=%s s3=%s",
                    run_id,
                    thread_id,
                    status,
                    destinations.get("local_path"),
                    destinations.get("s3_uri"),
                )
            except Exception:
                logger.exception("audit logging failed for run_id=%s", run_id)
