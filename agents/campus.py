from llm.client import chat
from tools.tool_runner import run_tool

def run(user_message: str, history: list = []) -> str:
    context = run_tool(user_message, agent_type="campus")

    recent_history = history[-6:] if len(history) > 6 else history

    system = f"""You are the Campus Agent for Texas State University.
Answer student questions about campus life, dining, parking, facilities, and services.
Be specific and helpful. If something isn't in the context, say so honestly.

TOOL RESULTS:
{context}"""

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)