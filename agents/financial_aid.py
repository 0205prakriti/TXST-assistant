from tools.tool_runner import run_tool
from agents.grounding import grounded_answer


def run(user_message: str, history: list | None = None) -> str:
    context = run_tool(user_message, agent_type="financial_aid")
    return grounded_answer(user_message, context, history)
