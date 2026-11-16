import logging
from functools import lru_cache
from pathlib import Path
from rag.ranking import rank_documents

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _backend():
    import chromadb
    from chromadb.utils import embedding_functions

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path=str(Path(__file__).resolve().parents[1] / "chroma_db"))
    return client, embedding_fn


def retrieve_records(query: str, collection_name: str, n_results: int = 3) -> list[dict]:
    """Top chunks as dicts with text, source and retrieved_at (used by evaluations)."""
    client, embedding_fn = _backend()
    collection = client.get_collection(name=collection_name, embedding_function=embedding_fn)
    count = collection.count()
    if count == 0:
        return []
    results = collection.query(query_texts=[query], n_results=min(20, count))
    # Keywords retain specific meaning (e.g. disbursement versus eligibility)
    # when the embedding model ranks broad eligibility text more highly.
    records = collection.get(include=["documents", "metadatas"])
    ranked = rank_documents(query, records["documents"], records["ids"], results["ids"][0])
    metadatas = records["metadatas"] or [{}] * count
    return [{
        "text": records["documents"][i],
        "source": (metadatas[i] or {}).get("source", "unknown"),
        "retrieved_at": (metadatas[i] or {}).get("retrieved_at", "unknown"),
    } for i in ranked[:n_results]]


def retrieve(query: str, collection_name: str, n_results: int = 3) -> str:
    try:
        records = retrieve_records(query, collection_name, n_results)
    except Exception:
        logger.exception("Knowledge retrieval failed for %s", collection_name)
        return ""
    return "\n\n".join(
        f"Source: {r['source']}\nRetrieved: {r['retrieved_at']}\n{r['text']}" for r in records
    )
