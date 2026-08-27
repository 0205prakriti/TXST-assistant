import json
from llm.client import chat

def route(user_message: str) -> dict:
    system = """You are a router for a Texas State University campus assistant.
Given a user message, respond with JSON only. No explanation.

Rules:
- ACADEMICS: courses, registration, grades, advising, degree plans, deadlines
- CAMPUS: dining, parking, library, events, facilities, housing
- FINANCIAL_AID: scholarships, loans, grants, FAFSA, tuition, financial aid
- GENERAL: greetings, casual chat, unclear questions, anything else

Format:
{"agent": "ACADEMICS", "confidence": 0.95}"""

    response = chat(
        messages=[{"role": "user", "content": user_message}],
        system=system
    )

    try:
        return json.loads(response)
    except:
        return {"agent": "GENERAL", "confidence": 0.5}