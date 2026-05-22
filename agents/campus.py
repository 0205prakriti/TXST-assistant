from llm.client import chat

def run(user_message: str, history: list = []) -> str:
    with open("context/campus.txt", "r", encoding="utf-8") as f:
        context = f.read(3000)

    system = f"""You are the Campus Agent for Texas State University.
Answer student questions about campus life, dining, parking, facilities, and services.
Be specific and helpful. If something isn't in the context, say so honestly.

CONTEXT:
{context}"""

    messages = history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)