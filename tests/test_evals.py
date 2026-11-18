"""Keep the golden set honest: every required fact must appear in its cited source."""
import re
from pathlib import Path

import pytest

from evals import metrics
from scripts import run_eval

ROOT = Path(__file__).resolve().parents[1]
CASES = metrics.load_cases()


def _source_texts():
    texts = {}
    for domain in ("academics", "campus", "financial_aid"):
        raw = (ROOT / "context" / f"{domain}.txt").read_text(encoding="utf-8")
        parts = re.split(r"--- SOURCE: (\S+) ---", raw)
        for url, body in zip(parts[1::2], parts[2::2]):
            texts[url] = metrics.normalize(body)
    return texts


def test_golden_set_shape():
    assert len(CASES) >= 150
    assert len({c["id"] for c in CASES}) == len(CASES)
    for case in CASES:
        assert case["domain"] in {"ACADEMICS", "CAMPUS", "FINANCIAL_AID", "GENERAL"}
        assert case["question"].strip()
        if case["type"] == "follow_up":
            assert case["history"] and case["standalone"]


@pytest.mark.parametrize("case", [c for c in CASES if c["expected_sources"]], ids=lambda c: c["id"])
def test_expected_sources_exist_and_contain_required_facts(case):
    texts = _source_texts()
    matching = [url for url in texts if metrics.source_matches(url, case["expected_sources"])]
    assert matching, f"No indexed page matches {case['expected_sources']}"
    blob = " ".join(texts[url] for url in matching)
    for fact in case["must_include"]:
        alternatives = [fact] if isinstance(fact, str) else fact
        assert any(metrics.normalize(alt) in blob for alt in alternatives), f"{alternatives} not in sources"


def test_ranking_metrics():
    urls = ["https://a/other", "https://onestop.txst.edu/financial-aid/how.html", "https://b"]
    assert metrics.first_relevant_rank(urls, ["financial-aid/how.html"]) == 2
    assert not metrics.hit_at_k(urls, ["financial-aid/how.html"], 1)
    assert metrics.hit_at_k(urls, ["financial-aid/how.html"], 3)
    assert metrics.reciprocal_rank(urls, ["financial-aid/how.html"]) == 0.5
    assert metrics.reciprocal_rank(urls, ["missing"]) == 0.0


def test_fact_matching_ignores_markdown_escapes_and_accepts_alternatives():
    answer = r"Complete 67% of attempted hours \(see SAP\). Open until midnight."
    assert metrics.facts_present(answer, ["67%", "(see sap)", ["12:00am", "midnight"]]) == 1.0
    assert metrics.facts_present(answer, ["2.0", "67%"]) == 0.5
    assert metrics.facts_present(answer, []) is None


def test_citation_checks():
    answer = "Apply now [How to Apply](https://onestop.txst.edu/financial-aid/how.html)."
    assert metrics.citations(answer) == ["https://onestop.txst.edu/financial-aid/how.html"]
    assert metrics.citations_grounded(answer, ["https://onestop.txst.edu/financial-aid/how.html"])
    assert metrics.citations_grounded(answer, ["https://other"]) is False
    assert metrics.citations_grounded("no links", []) is None


def test_fallback_and_personal_markers():
    assert metrics.is_fallback("I couldn't verify an answer from the available material.")
    assert metrics.discloses_no_access("I can’t access your personal aid record.")
    assert not metrics.discloses_no_access("Your award is $5,000.")


def test_quality_gates_report_failures():
    class Args:
        min_routing, min_hit3, min_facts = 0.9, None, 0.8
    failures = run_eval.check_gates({"routing_accuracy": 0.85, "fact_recall": 0.9}, Args)
    assert failures == ["routing_accuracy 0.85 < 0.9"]


def test_retrieval_stage_scores_with_stubbed_index(monkeypatch):
    def fake_urls(query, domain, k):
        return ["https://onestop.txst.edu/financial-aid/learn-more/maintain.html"]
    monkeypatch.setattr(run_eval, "retrieved_urls", fake_urls)

    class Args:
        k = 5
    cases = [c for c in CASES if c["id"] == "financial_aid-037"]
    rows, summary = run_eval.eval_retrieval(cases, Args)
    assert summary["hit@1"] == 1.0 and rows[0]["rr"] == 1.0


def test_rate_limited_call_is_retried(monkeypatch):
    import httpx
    from groq import RateLimitError
    monkeypatch.setattr(run_eval, "sleep", lambda seconds: None)
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RateLimitError("limit", response=httpx.Response(429, request=httpx.Request("POST", "https://x")), body=None)
        return "ok"

    assert run_eval.with_rate_limit_retry(flaky) == "ok" and len(calls) == 3


def test_routing_resume_skips_done_cases_and_checkpoints(monkeypatch, tmp_path):
    import json as _json
    import orchestrator
    seen = []

    def fake_plan(message, history=None):
        seen.append(message)
        return {"agent": "GENERAL", "confidence": 0.9, "query": message, "tool": "none"}

    monkeypatch.setattr(orchestrator, "plan", fake_plan)
    general = [c for c in CASES if c["domain"] == "GENERAL"][:3]
    previous = tmp_path / "routing.json"
    previous.write_text(_json.dumps({"stage": "routing", "rows": [
        {"id": general[0]["id"], "type": "general", "expected": "GENERAL", "agent": "GENERAL",
         "confidence": 0.9, "query": "q", "tool": "none", "correct": True, "seconds": 0.1}]}))
    monkeypatch.setattr(run_eval.metrics, "load_cases", lambda **_: general)
    assert run_eval.main(["--stage", "routing", "--resume", str(previous)]) == 0
    assert seen == [c["question"] for c in general[1:]]
    report = _json.loads(previous.read_text())
    assert report["summary"]["cases"] == 3 and report["summary"]["routing_accuracy"] == 1.0
