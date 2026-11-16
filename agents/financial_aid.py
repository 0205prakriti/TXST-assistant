from agents.generative import search_inputs
from agents.grounding import grounded_answer
from tools.tool_runner import run_tool


def run(user_message: str, history: list | None = None, plan: dict | None = None) -> str:
    query, tool = search_inputs(user_message, plan)
    context = run_tool(query, agent_type="financial_aid", tool=tool)
    # The standalone query carries the subject of follow-ups into passage selection.
    return grounded_answer(query, context, history)


def run_stream(user_message: str, history: list | None = None, plan: dict | None = None):
    """Grounded answers are rendered locally from cited passages (not LLM prose),
    so yield the final text in small chunks for progressive display."""
    answer = run(user_message, history, plan)
    words = answer.split(" ")
    for i, word in enumerate(words):
        yield word if i == 0 else " " + word
