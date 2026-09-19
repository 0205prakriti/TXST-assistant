"""Compact presentation of verified excerpts and previously saved replies."""
import re

GUIDANCE_PREFIX = "TXST’s published guidance:\n\n"
PERSONAL_PREFIX = "I can’t access your personal aid record or determine your award. TXST explains how to check it:\n\n"
PERSONAL_NOTICE = "I can’t access your personal aid record or determine your award."


def format_evidence(items, personal_account=False):
    """Items contain already-escaped text, a source title, and its URL."""
    sources = {}
    for item in items:
        sources.setdefault(item["source"], item["title"])
    numbers = {url: index + 1 for index, url in enumerate(sources)}
    multiple = len(sources) > 1
    lines = []
    for index, item in enumerate(items, start=1):
        reference = f" [{numbers[item['source']]}]" if multiple else ""
        lines.append(f"{index}. {item['text']}{reference}")
    links = " · ".join(
        f"[{str(numbers[url]) + '. ' if multiple else ''}{title}]({url})"
        for url, title in sources.items()
    )
    label = "Sources" if multiple else "Source"
    notice = PERSONAL_NOTICE + "\n\n" if personal_account else ""
    return notice + "\n".join(lines) + f"\n\n**{label}:** {links}"


def compact_saved_answer(answer):
    """Restyle only the exact excerpt format emitted by earlier app versions."""
    prefix = next((p for p in (GUIDANCE_PREFIX, PERSONAL_PREFIX) if answer.startswith(p)), None)
    if prefix is None:
        return answer
    body = answer[len(prefix):].strip()
    pattern = r"> ([^\n]+)\n\n\[([^\]\n]+)\]\((https?://[^\s)]+)\)"
    matches = list(re.finditer(pattern, body))
    if not matches or "\n\n".join(match[0] for match in matches) != body:
        return answer
    items = [{"text": match[1], "title": match[2], "source": match[3]} for match in matches]
    return format_evidence(items, personal_account=prefix == PERSONAL_PREFIX)
