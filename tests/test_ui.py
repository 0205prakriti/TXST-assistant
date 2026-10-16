from pathlib import Path

from streamlit.testing.v1 import AppTest

import memory.memory as memory


def test_streamed_legacy_reply_is_compacted_in_history(monkeypatch, tmp_path):
    """The live stream shows raw tokens, but what lands in history is compacted."""
    url = "https://onestop.txst.edu/financial-aid/how.html"
    legacy = (
        "TXST’s published guidance:\n\n"
        f"> Complete the FAFSA.\n\n[How to Apply]({url})\n\n"
        f"> List the school code.\n\n[How to Apply]({url})"
    )
    monkeypatch.setattr(memory, "MEMORY_FILE", tmp_path / "sessions.json")
    monkeypatch.setattr("chat_service.answer_stream", lambda *args: (
        {"agent": "FINANCIAL_AID", "confidence": 0.98, "session_id": "s1"},
        iter([legacy]),
    ))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "main.py"))
    app.run()
    app.chat_input[0].set_value("How do I apply for financial aid?").run()
    assert not app.exception
    # live stream renders the raw tokens as they arrive
    assert any("TXST’s published guidance:" in item.value for item in app.markdown)
    # history keeps the compacted form
    saved = [m for m in app.session_state.history if m["role"] == "assistant"]
    assert saved[-1]["content"].startswith("1. Complete the FAFSA.\n2. List the school code.")
    assert saved[-1]["content"].count(f"]({url})") == 1
    # rerun displays the compact form from history
    app.run()
    assert not app.exception
    rendered = [item.value for item in app.markdown]
    assert any(text.startswith("1. Complete the FAFSA.") for text in rendered)
    assert not any("TXST’s published guidance:" in text for text in rendered)
