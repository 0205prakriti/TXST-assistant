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
        result = json.loads(response)
        agent = result.get("agent", "GENERAL")
        confidence = float(result.get("confidence", 0))
        if agent not in {"ACADEMICS", "CAMPUS", "FINANCIAL_AID", "GENERAL"}:
            raise ValueError("Unknown agent")
        return {"agent": agent, "confidence": max(0.0, min(1.0, confidence))}
    except (ValueError, TypeError, json.JSONDecodeError):
        return {"agent": "GENERAL", "confidence": 0.5}
