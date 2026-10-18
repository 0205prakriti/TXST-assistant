# feedback.py — thumbs up/down votes on assistant answers, logged to SQLite.
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "feedback.db"


def _connect(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            rating TEXT NOT NULL,
            agent TEXT,
            created_at TEXT NOT NULL
        )"""
    )
    return conn


def log_feedback(question, answer, rating, session_id=None, agent=None, db_path=DB_PATH):
    """Record one vote ('up' or 'down') for an assistant answer."""
    if rating not in ("up", "down"):
        raise ValueError("rating must be 'up' or 'down'")
    conn = _connect(db_path)
    try:
        conn.execute(
            "INSERT INTO feedback (session_id, question, answer, rating, agent, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, question, answer, rating, agent,
             datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_feedback(db_path=DB_PATH, limit=100):
    """Most recent votes, newest first (feeds the future eval dashboard)."""
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT session_id, question, answer, rating, agent, created_at"
            " FROM feedback ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        conn.close()
    keys = ("session_id", "question", "answer", "rating", "agent", "created_at")
    return [dict(zip(keys, r)) for r in rows]
