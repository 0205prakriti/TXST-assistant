"""Small JSON-backed conversation store, isolated by session ID."""
import json
import os
from pathlib import Path
from threading import RLock

MEMORY_FILE = Path(__file__).resolve().parent / "sessions.json"
_lock = RLock()


def _read():
    if not MEMORY_FILE.exists():
        return {}
    with MEMORY_FILE.open(encoding="utf-8") as file:
        data = json.load(file)
    # Older versions stored a single shared history. Do not expose it to new sessions.
    return data.get("sessions", {})


def _write(sessions):
    temporary = MEMORY_FILE.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump({"sessions": sessions}, file, indent=2)
    os.replace(temporary, MEMORY_FILE)


def load_history(session_id: str = "") -> list:
    if not session_id:
        return []
    with _lock:
        return list(_read().get(session_id, []))


def save_history(history: list, session_id: str = ""):
    if not session_id:
        raise ValueError("session_id is required")
    with _lock:
        sessions = _read()
        sessions[session_id] = history
        _write(sessions)


def clear_history(session_id: str = ""):
    if not session_id:
        raise ValueError("session_id is required")
    with _lock:
        sessions = _read()
        sessions.pop(session_id, None)
        _write(sessions)
