"""Pure scoring helpers for the golden-set evaluation (no network, easy to test)."""
import json
import re
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parent / "golden.jsonl"
FALLBACK_MARKERS = ("couldn't verify", "cannot verify", "can't verify", "could you clarify")
PERSONAL_MARKERS = ("can’t access", "can't access", "cannot access", "don't have access", "do not have access")


def load_cases(path=GOLDEN_PATH, domain=None, case_type=None):
    cases = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if domain:
        cases = [c for c in cases if c["domain"] == domain]
    if case_type:
        cases = [c for c in cases if c["type"] == case_type]
    return cases


def source_matches(url, expected):
    return any(fragment in url for fragment in expected)


def first_relevant_rank(retrieved_urls, expected):
    """1-based rank of the first retrieved URL matching an expected source, else None."""
    for rank, url in enumerate(retrieved_urls, start=1):
        if source_matches(url, expected):
            return rank
    return None


def hit_at_k(retrieved_urls, expected, k):
    rank = first_relevant_rank(retrieved_urls[:k], expected)
    return rank is not None


def reciprocal_rank(retrieved_urls, expected):
    rank = first_relevant_rank(retrieved_urls, expected)
    return 1.0 / rank if rank else 0.0


def normalize(text):
    """Lower-case, drop Markdown escapes and collapse whitespace for fact matching."""
    text = text.replace("\\", "").replace("’", "'")
    return " ".join(text.lower().split())


def facts_present(answer, must_include):
    """Fraction of required facts present; each fact may list accepted alternatives."""
    if not must_include:
        return None
    text = normalize(answer)
    found = 0
    for fact in must_include:
        alternatives = [fact] if isinstance(fact, str) else fact
        if any(normalize(alt) in text for alt in alternatives):
            found += 1
    return found / len(must_include)


def citations(answer):
    return re.findall(r"\]\((https?://[^\s)]+)\)", answer)


def citations_grounded(answer, supplied_urls):
    """True when every cited link came from retrieved material (None if nothing cited)."""
    cited = citations(answer)
    if not cited:
        return None
    return set(cited).issubset(set(supplied_urls))


def is_fallback(answer):
    lowered = answer.lower()
    return any(marker in lowered for marker in FALLBACK_MARKERS)


def discloses_no_access(answer):
    lowered = answer.lower().replace("’", "'")
    return any(marker.replace("’", "'") in lowered for marker in PERSONAL_MARKERS)


def mean(values):
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 3) if values else None
