from llm.client import chat

def route(user_message: str) -> str:
    system = """You are a router for a Texas State University campus assistant.
Given a user message, respond with exactly one word:
- ACADEMICS for questions about courses, registration, grades, advising, degree plans, deadlines
- CAMPUS for questions about dining, parking, library, events, facilities, housing
No explanation. One word only."""

    response = chat(
        messages=[{"role": "user", "content": user_message}],
        system=system
    )
    return response.strip().upper()