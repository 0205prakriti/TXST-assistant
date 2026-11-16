"""Shared flow for agents that write grounded answers from retrieved sources."""
from agents.prompt import grounded_prompt
from llm.client import chat, chat_stream
from tools.tool_runner import run_tool

HISTORY_TURNS = 6


def search_inputs(user_message: str, plan: dict | None) -> tuple[str, str]:
    """Use the planner's standalone query and tool when available."""
    plan = plan or {}
    return plan.get("query") or user_message, plan.get("tool") or "search_knowledge_base"


def _request(domain, collection, user_message, history, plan):
    query, tool = search_inputs(user_message, plan)
    context = run_tool(query, agent_type=collection, tool=tool)
    messages = (history or [])[-HISTORY_TURNS:] + [{"role": "user", "content": user_message}]
    return messages, grounded_prompt(domain, context)


def answer(domain, collection, user_message, history=None, plan=None) -> str:
    messages, system = _request(domain, collection, user_message, history, plan)
    return chat(messages=messages, system=system)


def answer_stream(domain, collection, user_message, history=None, plan=None):
    messages, system = _request(domain, collection, user_message, history, plan)
    yield from chat_stream(messages=messages, system=system)
