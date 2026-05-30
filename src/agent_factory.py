"""Shared Deep Agent graph for CLI and CopilotKit API."""

from __future__ import annotations

from deepagents import create_deep_agent
from langchain_aws import ChatBedrock
from langgraph.checkpoint.memory import MemorySaver

from src.tools.snowflake_tools import execute_snowflake_sql, get_schema_summary

SYSTEM_PROMPT = """You are a Snowflake SQL analyst for the TPCH_SF1 sample dataset.

Workflow:
1. Understand the user's question (including follow-ups — see below).
2. Call get_schema_summary if you need table or column names.
3. Write a SELECT using fully qualified names (TPCH_SF1.CUSTOMER, etc.).
4. Call execute_snowflake_sql to run it.
5. If Snowflake returns an error, fix the SQL and retry (max 3 attempts).
6. Reply with: (a) plain-English answer, (b) final SQL, (c) key numbers.

Follow-up questions:
- The conversation history contains prior questions and answers.
- If the user says "instead", "also", "same but", "now show", etc., refine the LAST analysis.
- Keep the same tables, joins, and grouping unless they ask to change dimension.

Never run INSERT, UPDATE, DELETE, or DDL.
"""

AGENT_NAME = "nl2sql_assistant"
AGENT_DESCRIPTION = (
    "Snowflake TPCH analyst — natural language to SQL with schema lookup and query tools."
)


def build_agent_graph():
    """Return the compiled LangGraph used by CLI and FastAPI."""
    model = ChatBedrock(model_id="us.amazon.nova-pro-v1:0", region_name="us-east-1")
    return create_deep_agent(
        model=model,
        tools=[execute_snowflake_sql, get_schema_summary],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )
