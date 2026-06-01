"""Audit message extraction helpers."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.audit_extract import last_assistant_reply, last_user_question


def test_last_assistant_reply_after_final_user_turn():
    messages = [
        HumanMessage(content="first question"),
        AIMessage(content="first answer"),
        HumanMessage(content="what can you do?"),
        AIMessage(content=""),
        AIMessage(content="I help edit MDL YAML and relationships."),
    ]
    assert last_user_question(messages) == "what can you do?"
    assert last_assistant_reply(messages) == "I help edit MDL YAML and relationships."


def test_last_assistant_reply_skips_tool_only_ai_message():
    messages = [
        HumanMessage(content="check paas errors"),
        AIMessage(content="", tool_calls=[{"id": "1", "name": "search_audit_logs", "args": {}}]),
        ToolMessage(content='[{"status": "error"}]', tool_call_id="1", name="search_audit_logs"),
        AIMessage(content="Three relationship fixes are suggested below."),
    ]
    assert last_assistant_reply(messages) == "Three relationship fixes are suggested below."


def test_last_assistant_reply_handles_langgraph_dict_messages():
    messages = [
        {"type": "human", "content": "what can you do?"},
        {"type": "ai", "content": "I edit MDL YAML and relationships."},
    ]
    assert last_assistant_reply(messages) == "I edit MDL YAML and relationships."
