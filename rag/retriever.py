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


def retrieve(query: str, collection_name: str, n_results: int = 3) -> str:
    try:
        client, embedding_fn = _backend()
        collection = client.get_collection(name=collection_name, embedding_function=embedding_fn)
        count = collection.count()
        if count == 0:
            return ""
        results = collection.query(query_texts=[query], n_results=min(20, count))
        # Keywords retain specific meaning (e.g. disbursement versus eligibility)
        # when the embedding model ranks broad eligibility text more highly.
        records = collection.get(include=["documents", "metadatas"])
        ranked = rank_documents(query, records["documents"], records["ids"], results["ids"][0])
        selected = ranked[:n_results]
        chunks = [records["documents"][i] for i in selected]
        metadata = [(records["metadatas"] or [{}] * count)[i] for i in selected]
        return "\n\n".join(
            f"Source: {(meta or {}).get('source', 'unknown')}\n"
            f"Retrieved: {(meta or {}).get('retrieved_at', 'unknown')}\n{chunk}"
            for chunk, meta in zip(chunks, metadata)
        )
    except Exception:
        logger.exception("Knowledge retrieval failed for %s", collection_name)
        return ""
