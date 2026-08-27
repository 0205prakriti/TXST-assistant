from llm.client import chat
from tools.tool_runner import run_tool

def run(user_message: str, history: list = []) -> str:
    # agent autonomously decides which tool to use
    context = run_tool(user_message, agent_type="academics")

    recent_history = history[-6:] if len(history) > 6 else history

    system = f"""...
Be concise — answer in 3-5 sentences unless the question needs more detail.
Avoid tables and long lists unless specifically asked.
CONTEXT:
{context}"""

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)