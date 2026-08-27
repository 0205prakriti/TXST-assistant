from llm.client import chat

def run(user_message: str, history: list = []) -> str:
    recent_history = history[-6:] if len(history) > 6 else history

    system = """You are a friendly campus assistant for Texas State University.
For casual greetings, respond warmly and tell the user what you can help with.
Keep responses short — 2-3 sentences max.
You can help with: academics, campus life, and financial aid."""

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)