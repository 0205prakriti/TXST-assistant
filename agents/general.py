from llm.client import chat, chat_stream

SYSTEM = """You are a friendly campus assistant for Texas State University.
For casual greetings, respond warmly and tell the user what you can help with.
Keep responses short — 2-3 sentences max.
You can help with: academics, campus life, and financial aid.
Do not state TXST facts such as dates, costs or policies; offer to look them up instead."""


def _messages(user_message, history):
    return (history or [])[-6:] + [{"role": "user", "content": user_message}]


def run(user_message: str, history: list | None = None, plan: dict | None = None) -> str:
    return chat(messages=_messages(user_message, history), system=SYSTEM)


def run_stream(user_message: str, history: list | None = None, plan: dict | None = None):
    yield from chat_stream(messages=_messages(user_message, history), system=SYSTEM)
