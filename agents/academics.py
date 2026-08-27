from llm.client import chat
from tools.tool_runner import run_tool

def run(user_message: str, history: list = []) -> str:
    # agent autonomously decides which tool to use
    context = run_tool(user_message, agent_type="academics")

    recent_history = history[-6:] if len(history) > 6 else history

    system = f"""You are the Academics Agent for Texas State University.
Answer student questions using the tool results below.
Be specific and helpful. If something isn't in the context, say so honestly.

TOOL RESULTS:
{context}"""

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)