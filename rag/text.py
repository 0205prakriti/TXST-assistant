"""Keep source sentences intact, including common abbreviations."""
import re


def sentences(text):
    return re.split(r"(?<!U\.S\.)(?<!e\.g\.)(?<!i\.e\.)(?<=[.!?])\s+(?=[A-Z])", " ".join(text.split()))
