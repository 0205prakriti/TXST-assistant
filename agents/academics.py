from llm.client import chat

def run(user_message: str, history: list = []) -> str:
    with open("context/academics.txt", "r", encoding="utf-8") as f:
        context = f.read()

    system = f"""You are the Academics Agent for Texas State University.
Answer student questions using the information below.
Be specific and helpful. If something isn't in the context, say so honestly.

CONTEXT:
{context}"""

    messages = history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)