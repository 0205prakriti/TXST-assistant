from unittest.mock import Mock

import pytest
import requests

import scrape_context
from rag.embedder import chunk_text
from rag.ranking import rank_documents


def test_extract_keeps_accordion_answers_and_removes_navigation():
    body = "Complete your application and check your outstanding requirements. " * 5
    html = f'<title>Aid</title><nav>Outside navigation</nav><main><nav>Menu</nav><h1>Verification</h1><div hidden>{body}</div></main>'
    title, content = scrape_context.extract_content(html)
    assert title == "Aid"
    assert body.strip() in content
    assert "navigation" not in content and "Menu" not in content


def test_failed_refresh_preserves_existing_snapshot(monkeypatch, tmp_path):
    monkeypatch.setattr(scrape_context, "ROOT", tmp_path)
    output = tmp_path / "context" / "financial_aid.txt"
    output.parent.mkdir()
    output.write_text("existing knowledge")
    monkeypatch.setattr(scrape_context, "scrape_page", Mock(side_effect=[
        {"url": "https://onestop.txst.edu/one", "title": "One", "text": "Content", "retrieved_at": "today"},
        requests.HTTPError("Unavailable"),
    ]))
    with pytest.raises(requests.HTTPError):
        scrape_context.refresh("context/financial_aid.txt", ["one", "two"])
    assert output.read_text() == "existing knowledge"


def test_empty_page_is_rejected():
    with pytest.raises(ValueError):
        scrape_context.extract_content("<main>Not found</main>")


def test_chunks_overlap_without_losing_words():
    words = " ".join(f"Sentence {i} has some words." for i in range(50)).split()
    chunks = chunk_text(" ".join(words), chunk_size=160, overlap=35)
    assert len(chunks) > 1
    assert set(" ".join(chunks).split()) == set(words)
    for left, right in zip(chunks, chunks[1:]):
        assert left.split()[-1] in right.split()
        assert left.endswith(".") and right.startswith("Sentence")


def test_bad_overlap_is_rejected():
    with pytest.raises(ValueError):
        chunk_text("data", chunk_size=100, overlap=100)


def test_disbursement_terms_can_outrank_generic_eligibility():
    documents = [
        "Financial aid eligibility requirements: students must be enrolled in a degree program.",
        "Before aid can be disbursed, accept your offers and meet disbursement requirements.",
        "Financial aid grants and scholarships at Texas State University.",
    ]
    ranked = rank_documents("financial aid disbursement requirements Texas State University", documents,
                            ["eligibility", "receive", "grants"], ["eligibility", "grants", "receive"])
    assert ranked[0] == 1
