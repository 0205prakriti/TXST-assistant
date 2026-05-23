# agents/financial_aid.py
from llm.client import chat

def run(user_message: str, history: list = []) -> str:
    with open("context/financial_aid.txt", "r", encoding="utf-8") as f:
        context = f.read(6000)

    system = f"""You are the Financial Aid Agent for Texas State University.
Answer student questions about scholarships, loans, grants, FAFSA, and financial aid processes.
Be specific and helpful. If something isn't in the context, say so honestly.

CONTEXT:
{context}"""

    messages = history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)