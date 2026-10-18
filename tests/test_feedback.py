import pytest

from feedback import log_feedback, get_feedback


def test_log_and_read_feedback(tmp_path):
    db = tmp_path / "feedback.db"
    log_feedback("What is FAFSA?", "FAFSA is...", "up",
                 session_id="s1", agent="FINANCIAL_AID", db_path=db)
    log_feedback("Q2", "A2", "down", db_path=db)
    rows = get_feedback(db_path=db)
    assert len(rows) == 2
    assert rows[0]["rating"] == "down"  # newest first
    assert rows[1]["question"] == "What is FAFSA?"
    assert rows[1]["agent"] == "FINANCIAL_AID"
    assert rows[1]["session_id"] == "s1"
    assert rows[1]["created_at"]


def test_invalid_rating_rejected(tmp_path):
    db = tmp_path / "fb.db"
    with pytest.raises(ValueError):
        log_feedback("q", "a", "meh", db_path=db)
    assert get_feedback(db_path=db) == []
