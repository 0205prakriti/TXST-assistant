import json
from llm.client import chat

def route(user_message: str) -> dict:
    system = """You are a router for a Texas State University campus assistant.
Given a user message, respond with a JSON object only. No explanation. No extra text.
Format:
{"agent": "ACADEMICS", "confidence": 0.95}

Rules:
- agent must be one of: ACADEMICS, CAMPUS, FINANCIAL_AID
- ACADEMICS: courses, registration, grades, advising, degree plans, deadlines
- CAMPUS: dining, parking, library, events, facilities, housing
- FINANCIAL_AID: scholarships, loans, grants, FAFSA, tuition, financial aid
- confidence is a float between 0.0 and 1.0
- if confidence is below 0.6, still pick the best agent but set confidence low"""

    response = chat(
        messages=[{"role": "user", "content": user_message}],
        system=system
    )

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # fallback if model doesn't return clean JSON
        return {"agent": "CAMPUS", "confidence": 0.5}