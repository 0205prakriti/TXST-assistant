from llm.client import chat, chat_stream

def run(user_message: str, history: list | None = None) -> str:
    recent_history = (history or [])[-6:]

    system = """You are a friendly campus assistant for Texas State University.
For casual greetings, respond warmly and tell the user what you can help with.
Keep responses short — 2-3 sentences max.
You can help with: academics, campus life, and financial aid."""

    messages = recent_history + [{"role": "user", "content": user_message}]
    return chat(messages=messages, system=system)


def run_stream(user_message: str, history: list | None = None):
    """Same as run(), but yields LLM tokens as they arrive."""
    recent_history = (history or [])[-6:]

    system = """You are a friendly campus assistant for Texas State University.
For casual greetings, respond warmly and tell the user what you can help with.
Keep responses short — 2-3 sentences max.
You can help with: academics, campus life, and financial aid."""

    messages = recent_history + [{"role": "user", "content": user_message}]
    yield from chat_stream(messages=messages, system=system)
