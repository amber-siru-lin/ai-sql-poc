"""AG-UI LangGraph agent for the semantic layer editor."""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import AsyncGenerator

from ag_ui.core import RunAgentInput
from ag_ui_langgraph.agent import LangGraphAgent
from langchain_core.runnables import ensure_config

from src.audit_extract import extract_sql_executions, last_assistant_reply, last_user_question
from src.audit_logger import build_audit_record, write_audit_record
from src.semantic_layer.retry_policy import GRAPH_RECURSION_LIMIT

logger = logging.getLogger(__name__)


class SemanticEditorLangGraphAgent(LangGraphAgent):
    """Injects active file context from AG-UI forwarded_props; audits as semantic_editor."""

    async def prepare_stream(self, input, agent_state, config):
        forwarded = input.forwarded_props or {}
        config = ensure_config(config)
        configurable = dict(config.get("configurable") or {})
        active_file = forwarded.get("activeFile") or forwarded.get("active_file")
        active_content = forwarded.get("activeFileContent") or forwarded.get(
            "active_file_content"
        )
        if active_file:
            configurable["active_file"] = str(active_file)
        if active_content is not None:
            configurable["active_file_content"] = str(active_content)
        thread_id = getattr(input, "thread_id", None) or getattr(input, "run_id", None)
        if thread_id:
            configurable["thread_id"] = str(thread_id)
        config["configurable"] = configurable
        config["recursion_limit"] = GRAPH_RECURSION_LIMIT
        return await super().prepare_stream(input, agent_state, config)

    async def run(self, input: RunAgentInput) -> AsyncGenerator:
        forwarded = input.forwarded_props or {}
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
                config["configurable"] = configurable
                state = await self.graph.aget_state(config)
                messages = list(state.values.get("messages", [])) if state and state.values else []
                if not question:
                    question = last_user_question(messages)
                active_file = forwarded.get("activeFile") or forwarded.get("active_file")
                record = build_audit_record(
                    thread_id=thread_id,
                    run_id=run_id,
                    semantic_layer="editor",
                    question=question,
                    sql_executions=extract_sql_executions(messages),
                    status=status,
                    duration_ms=duration_ms,
                    error=error,
                    source="semantic_editor",
                    assistant_reply=last_assistant_reply(messages),
                )
                if active_file:
                    record["active_file"] = str(active_file)
                destinations = write_audit_record(record)
                logger.info(
                    "editor audit run_id=%s thread_id=%s status=%s local=%s s3=%s",
                    run_id,
                    thread_id,
                    status,
                    destinations.get("local_path"),
                    destinations.get("s3_uri"),
                )
            except Exception:
                logger.exception("editor audit logging failed for run_id=%s", run_id)
