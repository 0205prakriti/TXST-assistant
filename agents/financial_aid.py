from tools.tool_runner import run_tool
from agents.grounding import grounded_answer


def run(user_message: str, history: list | None = None) -> str:
    context = run_tool(user_message, agent_type="financial_aid")
    return grounded_answer(user_message, context, history)


def run_stream(user_message: str, history: list | None = None):
    """Grounded answers are rendered locally from cited passages (not LLM prose),
    so yield the final text in small chunks for progressive display."""
    answer = run(user_message, history)
    words = answer.split(" ")
    for i, word in enumerate(words):
        yield word if i == 0 else " " + word
