"""Combine semantic results with keyword matching for specific campus terms."""
from collections import Counter
from math import log
import re

STOP_WORDS = set("a an and are as at be by can do does for from how i in is it me my of on or that the their this to university texas state txst what when where which will with you your financial aid".split())


def tokens(text):
    result = []
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        if word in STOP_WORDS:
            continue
        if word.startswith("disburs"):
            word = "disburs"
        elif word.startswith("requir"):
            word = "requir"
        elif word.endswith("s") and len(word) > 4:
            word = word[:-1]
        result.append(word)
    return result


def rank_documents(query, documents, ids, semantic_ids):
    counts = [Counter(tokens(document)) for document in documents]
    average_length = sum(sum(count.values()) for count in counts) / max(1, len(counts))
    scores = [0.0] * len(documents)
    for term in set(tokens(query)):
        frequency = sum(term in count for count in counts)
        idf = log(1 + (len(counts) - frequency + 0.5) / (frequency + 0.5))
        for index, count in enumerate(counts):
            tf = count[term]
            if tf:
                norm = 1.2 * (0.25 + 0.75 * sum(count.values()) / max(1, average_length))
                scores[index] += idf * tf * 2.2 / (tf + norm)
    maximum = max(scores, default=0) or 1
    semantic = {doc_id: 6 / (6 + rank) for rank, doc_id in enumerate(semantic_ids)}
    return sorted(range(len(documents)), key=lambda i: (
        0.65 * scores[i] / maximum + 0.35 * semantic.get(ids[i], 0)
    ), reverse=True)
