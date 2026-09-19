from pathlib import Path

from streamlit.testing.v1 import AppTest

import memory.memory as memory


def test_new_legacy_reply_is_compact_before_and_after_rerun(monkeypatch, tmp_path):
    """An already-running app may still receive responses in the old format."""
    url = "https://onestop.txst.edu/financial-aid/how.html"
    legacy = (
        "TXST’s published guidance:\n\n"
        f"> Complete the FAFSA.\n\n[How to Apply]({url})\n\n"
        f"> List the school code.\n\n[How to Apply]({url})"
    )
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    monkeypatch.setattr("chat_service.answer", lambda *args: {
        "response": legacy, "agent": "FINANCIAL_AID", "confidence": 0.98,
    })
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "main.py"))
    app.run()
    app.chat_input[0].set_value("How do I apply for financial aid?").run()
    assert not app.exception
    rendered = [item.value for item in app.markdown]
    reply = next(text for text in rendered if "Complete the FAFSA." in text)
    assert reply.startswith("1. Complete the FAFSA.\n2. List the school code.")
    assert reply.count(f"]({url})") == 1
    assert not any("98%" in text or "TXST’s published guidance:" in text for text in rendered)
    app.run()
    assert not app.exception
    assert reply in [item.value for item in app.markdown]
