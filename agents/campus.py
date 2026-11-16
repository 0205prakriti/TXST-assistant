from agents import generative

DOMAIN, COLLECTION = "campus life", "campus"


def run(user_message: str, history: list | None = None, plan: dict | None = None) -> str:
    return generative.answer(DOMAIN, COLLECTION, user_message, history, plan)


def run_stream(user_message: str, history: list | None = None, plan: dict | None = None):
    yield from generative.answer_stream(DOMAIN, COLLECTION, user_message, history, plan)
