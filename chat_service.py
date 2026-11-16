"""One chat flow shared by the API and Streamlit UI."""
from uuid import uuid4

from agents import academics, campus, financial_aid, general
from memory.memory import load_history, save_history
from orchestrator import plan

AGENTS = {
    "ACADEMICS": academics,
    "CAMPUS": campus,
    "FINANCIAL_AID": financial_aid,
    "GENERAL": general,
}
CLARIFY_THRESHOLD = 0.6
CLARIFY = "Could you clarify whether you mean academics, campus life, or financial aid?"


def _needs_clarification(decision: dict) -> bool:
    # GENERAL replies are small talk; asking which domain is never more useful.
    return decision["agent"] != "GENERAL" and decision["confidence"] < CLARIFY_THRESHOLD


def _save(history, session_id, message, response):
    history.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ])
    save_history(history, session_id)


def answer(message: str, session_id: str | None = None) -> dict:
    session_id = session_id or str(uuid4())
    history = load_history(session_id)
    decision = plan(message, history)
    if _needs_clarification(decision):
        response = CLARIFY
    else:
        response = AGENTS[decision["agent"]].run(message, history, plan=decision)
    _save(history, session_id, message, response)
    return {"response": response, "agent": decision["agent"], "confidence": decision["confidence"],
            "session_id": session_id, "query": decision["query"]}


def answer_stream(message: str, session_id: str | None = None):
    """Plan first, then stream the agent's reply token by token.

    Returns (meta, token_generator): meta carries agent/confidence/session_id
    up front; exhausting the generator saves the conversation to history.
    """
    session_id = session_id or str(uuid4())
    history = load_history(session_id)
    decision = plan(message, history)
    meta = {"agent": decision["agent"], "confidence": decision["confidence"], "session_id": session_id}

    def _generate():
        if _needs_clarification(decision):
            response = CLARIFY
            yield response
        else:
            parts = []
            for token in AGENTS[decision["agent"]].run_stream(message, history, plan=decision):
                parts.append(token)
                yield token
            response = "".join(parts)
        _save(history, session_id, message, response)

    return meta, _generate()
