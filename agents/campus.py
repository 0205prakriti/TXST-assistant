from llm.client import chat
from tools.tool_runner import run_tool
from agents.prompt import grounded_prompt

def run(user_message: str, history: list | None = None) -> str:
    context = run_tool(user_message, agent_type="campus")

    recent_history = (history or [])[-6:]

    system = grounded_prompt("campus life", context)

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)
