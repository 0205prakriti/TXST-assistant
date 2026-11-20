"""Keep source sentences intact, including common abbreviations.

Section headings are marked so that a sentence such as "For 2026-2027, the maximum
award is $5,300." keeps the name of the grant it belongs to after chunking.
"""
import re

HEADING_MARK = "## "
_TERMINAL = (".", "!", "?", ":", ";", ",")
# Generic labels repeat under every item; keeping them would hide the real section
# ("2 - Starbucks" -> "Hours of Operation").
_NOT_HEADINGS = {"expand", "faq list", "learn more", "apply now", "contact info", "important", "closed",
                 "hours of operation", "operating hours", "suggested deadline", "please note",
                 "more information", "sign in", "small group lecture"}
_DANGLING = {"a", "an", "the", "of", "to", "and", "or", "for", "in", "on", "at", "with", "by", "visit", "your"}
# Hours, dates and day names are table cells, not section titles.
_TABLE_CELL = re.compile(
    r"\d{1,2}(:\d{2})?\s?(am|pm)\b|\d{1,2}:\d{2}|\b(19|20)\d{2}\b|:"
    r"|^(mon|tues|wednes|thurs|fri|satur|sun)day"
    r"|^(january|february|march|april|may|june|july|august|september|october|november|december)\b",
    re.IGNORECASE)


def sentences(text):
    return re.split(r"(?<!U\.S\.)(?<!e\.g\.)(?<!i\.e\.)(?<=[.!?])\s+(?=[A-Z#])", " ".join(text.split()))


def is_heading_line(line, previous="", following=""):
    """A short title-like line that starts a section rather than continuing a sentence."""
    line = line.strip()
    words = line.split()
    if not 2 <= len(words) <= 12 or len(line) > 90 or line.endswith(_TERMINAL):
        return False
    if not (line[0].isupper() or line[0].isdigit()) or line.lower() in _NOT_HEADINGS:
        return False
    if words[-1].lower() in _DANGLING or _TABLE_CELL.search(line):
        return False
    # Headings are title-like: most longer words are capitalized ("Texas State Tuition
    # Grant"), unlike sentence fragments ("To view the criteria, visit the").
    content = [w.strip("(),") for w in words if len(w.strip("(),")) > 3]
    if content and sum(w[:1].isupper() or w[:1].isdigit() for w in content) / len(content) < 0.5:
        return False
    # Link text split across lines ("visit the / Coordinating Board / .") is not a heading.
    previous = previous.strip()
    if (previous and not previous.endswith((".", "!", "?", ":")) and previous.lower() not in _NOT_HEADINGS
            and not is_heading_line(previous)):
        return False
    following = following.strip()
    return not following or not (following[0] in ".,;:)" or following[0].islower())


def mark_headings(text):
    """Turn heading lines into '## Heading.' sentences; leave all other text unchanged."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    marked = []
    for index, line in enumerate(lines):
        previous = lines[index - 1] if index else ""
        following = lines[index + 1] if index + 1 < len(lines) else ""
        marked.append(f"{HEADING_MARK}{line}." if is_heading_line(line, previous, following) else line)
    return "\n".join(marked)


def heading_text(sentence):
    """The heading name for a marked sentence, else None."""
    if not sentence.startswith(HEADING_MARK):
        return None
    return sentence[len(HEADING_MARK):].rstrip(".").strip() or None
