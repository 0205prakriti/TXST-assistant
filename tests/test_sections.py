"""Section headings keep award amounts and similar facts tied to what they describe."""
import json
from pathlib import Path

from agents import grounding
from rag.embedder import chunk_text
from rag.text import heading_text, is_heading_line, mark_headings

ROOT = Path(__file__).resolve().parents[1]
GRANTS = """Undergraduate Grants
Texas Public Educational Grant (TPEG)
This institutional grant is awarded to students based on their financial need.
For 2026-2027, the maximum award is $5,300.
Important:
This grant is contingent upon the availability of state funds.
Toward Excellence, Access, and Success Grant (TEXAS Grant)
To view the TEXAS Grant eligibility criteria, visit the
Texas Higher Education Coordinating Board
.
For 2026-2027 the maximum award is $5,000.
"""


def test_heading_detection_rejects_fragments_and_table_cells():
    assert is_heading_line("Texas State Tuition Grant", previous="Funds are limited.")
    assert not is_heading_line("Texas Higher Education Coordinating Board", previous="criteria, visit the")
    assert not is_heading_line("To view the TEXAS Grant eligibility criteria, visit the")
    assert not is_heading_line("Complete a", previous="Apply now.")
    assert not is_heading_line("Monday-Thursday 7:00am - 12:00am")
    assert not is_heading_line("Hours of Operation")
    assert not is_heading_line("Phone: (512) 467-8080")


def test_mark_headings_and_heading_text():
    marked = mark_headings(GRANTS).splitlines()
    assert "## Texas Public Educational Grant (TPEG)." in marked
    assert "## Toward Excellence, Access, and Success Grant (TEXAS Grant)." in marked
    assert "Texas Higher Education Coordinating Board" in marked
    assert heading_text("## Undergraduate Grants.") == "Undergraduate Grants"
    assert heading_text("Plain sentence.") is None


def test_chunks_starting_mid_section_carry_their_heading():
    chunks = chunk_text(GRANTS, chunk_size=180, overlap=0)
    amount = next(c for c in chunks if "$5,000" in c)
    assert "TEXAS Grant" in amount
    assert all(c.startswith("## ") for c in chunks)


def test_academics_style_plain_chunks_are_unchanged():
    assert "## " not in " ".join(chunk_text(GRANTS, headings=False))


def test_selected_amount_is_rendered_with_its_grant_name(monkeypatch):
    context = "Source: https://onestop.txst.edu/financial-aid/learn-more/types/grants.html\nGrants\n" + \
        " ".join(chunk_text(GRANTS))
    passages = grounding.source_passages(context)
    texas = next(pid for pid, p in passages.items() if "$5,000" in p["text"])
    assert passages[texas]["section"] == "Toward Excellence, Access, and Success Grant (TEXAS Grant)"
    assert not any(p["text"].startswith("## ") for p in passages.values())
    monkeypatch.setattr(grounding, "chat", lambda **_: json.dumps({"limitation": "none", "passage_ids": [texas]}))
    answer = grounding.grounded_answer("What is the maximum TEXAS Grant award?", context)
    assert "TEXAS Grant" in answer and "$5,000" in answer and "$5,300" not in answer


def test_real_grants_page_keeps_each_amount_with_its_grant():
    import re
    raw = (ROOT / "context" / "financial_aid.txt").read_text(encoding="utf-8")
    parts = re.split(r"--- SOURCE: (\S+) ---", raw)
    body = next(b for u, b in zip(parts[1::2], parts[2::2]) if "grants.html" in u)
    context = "".join(f"Source: https://x/grants.html\n{chunk}\n\n" for chunk in chunk_text(body))
    sections = {p["text"]: p.get("section") for p in grounding.source_passages(context).values()}
    assert sections["For 2026-2027 the maximum award is $5,000."].endswith("(TEXAS Grant)")
    assert "TPEG" in sections["For 2026-2027, the maximum award is $5,300."] or \
        "Tuition Grant" in sections["For 2026-2027, the maximum award is $5,300."]


def test_fast_calls_use_small_model_with_low_reasoning(monkeypatch):
    from llm import client
    sent = []

    class Completions:
        def create(self, **kwargs):
            sent.append(kwargs)
            message = type("M", (), {"content": "{}"})
            return type("R", (), {"choices": [type("C", (), {"message": message})]})

    fake = type("Client", (), {"chat": type("Chat", (), {"completions": Completions()})()})()
    monkeypatch.setattr(client, "_client", lambda: fake)
    client.chat([{"role": "user", "content": "hi"}], json_mode=True, fast=True)
    client.chat([{"role": "user", "content": "hi"}])
    assert sent[0]["model"] == client.FAST_MODEL
    assert sent[0]["extra_body"] == {"reasoning_effort": client.FAST_REASONING_EFFORT}
    assert sent[1]["model"] == client.MODEL and "extra_body" not in sent[1]


def test_table_rows_keep_values_with_labels():
    from rag.text import is_table_row
    table = """Minimum Cumulative Texas State GPA Requirements
Degree or Certificate
Minimum Cumulative Texas State GPA
1st Bachelor's
2.0
Master's
3.0
"""
    marked = mark_headings(table).splitlines()
    assert "1st Bachelor's: 2.0." in marked and "Master's: 3.0." in marked
    assert not any(line == "2.0" for line in marked)
    assert is_table_row("Monday-Thursday", "10:00am - 11:30pm")
    assert is_table_row("Fall semester only", "November 1, 2026")
    assert not is_table_row("Minimum Cumulative Texas State GPA", "1st Bachelor's")
    assert not is_table_row("April 11, 2026", "2025-2026")
    assert not is_table_row("-", "9:00pm")
    assert not is_table_row("This is a full sentence.", "2.0")


def test_real_sap_page_pairs_gpa_rows():
    import re
    raw = (ROOT / "context" / "financial_aid.txt").read_text(encoding="utf-8")
    parts = re.split(r"--- SOURCE: (\S+) ---", raw)
    body = next(b for u, b in zip(parts[1::2], parts[2::2]) if "maintain.html" in u)
    context = "".join(f"Source: https://x/maintain.html\n{chunk}\n\n" for chunk in chunk_text(body))
    texts = [p["text"] for p in grounding.source_passages(context).values()]
    assert "1st Bachelor's: 2.0." in texts and "Master's: 3.0." in texts
