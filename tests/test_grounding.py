import json

from agents import grounding

URL = "https://onestop.txst.edu/financial-aid/how.html"
CONTEXT = f"Source: {URL}\nCheck your award in Self-Service."


def test_model_cannot_add_contact_details(monkeypatch):
    monkeypatch.setattr(grounding, "chat", lambda **_: json.dumps({
        "limitation": "none", "passage_ids": ["p1"], "answer": "Call (830) 459-6183."}))
    answer = grounding.grounded_answer("Help", CONTEXT)
    assert "830" not in answer
    assert "Check your award in Self-Service." in answer


def test_rejects_unknown_passage_ids(monkeypatch):
    monkeypatch.setattr(grounding, "chat", lambda **_: json.dumps({"limitation": "none", "passage_ids": ["invented"]}))
    assert "couldn't verify" in grounding.grounded_answer("Help", CONTEXT)


def test_malformed_selection_has_safe_fallback(monkeypatch):
    monkeypatch.setattr(grounding, "chat", lambda **_: "not JSON")
    assert "couldn't verify" in grounding.grounded_answer("Help", CONTEXT)


def test_verified_passage_keeps_original_source(monkeypatch):
    other = "https://onestop.txst.edu/other.html"
    context = CONTEXT + f"\n\nSource: {other}\nYou must complete a FAFSA."
    monkeypatch.setattr(grounding, "chat", lambda **_: json.dumps({"limitation": "none", "passage_ids": ["p2"]}))
    answer = grounding.grounded_answer("How to apply?", context)
    assert "You must complete a FAFSA." in answer
    assert f"[Source]({other})" in answer
    assert URL not in answer


def test_cannot_recast_refund_advice_as_requirement(monkeypatch):
    context = f"Source: {URL}\nTo receive your refund faster, sign up for e-Refunds."
    monkeypatch.setattr(grounding, "chat", lambda **_: json.dumps({
        "limitation": "none", "passage_ids": ["p1"], "answer": "You must sign up for e-Refunds to receive financial aid."}))
    answer = grounding.grounded_answer("What is required?", context)
    assert "You must sign up" not in answer
    assert "To receive your refund faster" in answer


def test_personal_question_discloses_no_account_access(monkeypatch):
    monkeypatch.setattr(grounding, "chat", lambda **_: json.dumps({"limitation": "personal_account", "passage_ids": ["p1"]}))
    assert "can’t access your personal aid record" in grounding.grounded_answer("What is my award?", CONTEXT)


def test_us_abbreviation_does_not_cut_off_condition():
    passages = grounding.source_passages(f"Source: {URL}\nIf selected by the U.S. Department of Education, submit the requested documents. Check Self-Service.")
    assert passages["p1"]["text"] == "If selected by the U.S. Department of Education, submit the requested documents."
