"""One chat flow shared by the API and Streamlit UI."""
from uuid import uuid4

from agents import academics, campus, financial_aid, general
from memory.memory import load_history, save_history
from orchestrator import route

AGENTS = {
    "ACADEMICS": academics,
    "CAMPUS": campus,
    "FINANCIAL_AID": financial_aid,
    "GENERAL": general,
}


def answer(message: str, session_id: str | None = None) -> dict:
    session_id = session_id or str(uuid4())
    history = load_history(session_id)
    decision = route(message)
    agent = decision["agent"]
    confidence = decision["confidence"]
    if confidence < 0.6:
        response = "Could you clarify whether you mean academics, campus life, or financial aid?"
    else:
        response = AGENTS[agent].run(message, history)
    history.extend([
        {"role": "user", "content": message},
        {"role": "assistant", "content": response},
    ])
    save_history(history, session_id)
    return {"response": response, "agent": agent, "confidence": confidence, "session_id": session_id}


def answer_stream(message: str, session_id: str | None = None):
    """Route first, then stream the agent's reply token by token.

    Returns (meta, token_generator): meta carries agent/confidence/session_id
    up front; exhausting the generator saves the conversation to history.
    """
    session_id = session_id or str(uuid4())
    history = load_history(session_id)
    decision = route(message)
    agent = decision["agent"]
    confidence = decision["confidence"]
    meta = {"agent": agent, "confidence": confidence, "session_id": session_id}

    def _generate():
        if confidence < 0.6:
            response = "Could you clarify whether you mean academics, campus life, or financial aid?"
            yield response
        else:
            parts = []
            for token in AGENTS[agent].run_stream(message, history):
                parts.append(token)
                yield token
            response = "".join(parts)
        history.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": response},
        ])
        save_history(history, session_id)

    return meta, _generate()
