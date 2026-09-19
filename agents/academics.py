from llm.client import chat
from tools.tool_runner import run_tool
from agents.prompt import grounded_prompt

def run(user_message: str, history: list | None = None) -> str:
    # agent autonomously decides which tool to use
    context = run_tool(user_message, agent_type="academics")

    recent_history = (history or [])[-6:]

    system = grounded_prompt("academics", context)

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)
