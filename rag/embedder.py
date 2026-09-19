import argparse
import json
import re
from pathlib import Path

try:
    from rag.text import sentences
except ModuleNotFoundError:
    from text import sentences  # Direct invocation: python rag/embedder.py

ROOT = Path(__file__).resolve().parents[1]


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list:
    if chunk_size <= 0 or not 0 <= overlap < chunk_size:
        raise ValueError("Require chunk_size > overlap >= 0")
    parts = [part for part in sentences(text) if part]
    chunks = []
    start = 0
    while start < len(parts):
        end, size = start, 0
        while end < len(parts) and (end == start or size + len(parts[end]) + 1 <= chunk_size):
            size += len(parts[end]) + 1
            end += 1
        chunks.append(" ".join(parts[start:end]))
        if end == len(parts):
            break
        next_start, size = end, 0
        while next_start > start + 1 and size < overlap:
            next_start -= 1
            size += len(parts[next_start]) + 1
        start = next_start
    return chunks


def embed_file(filepath: str, collection_name: str):
    import chromadb
    from chromadb.utils import embedding_functions

    print(f"Embedding {filepath} into '{collection_name}'...")
    path = ROOT / filepath
    with path.open("r", encoding="utf-8") as f:
        text = f.read()

    metadata_path = path.with_suffix(".sources.json")
    sources = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else []
    metadata = {source["url"]: source for source in sources}

    sections = re.split(r"--- SOURCE: (https?://[^\s]+) ---", text)
    if len(sections) > 1:
        records = [(chunk, url) for url, body in zip(sections[1::2], sections[2::2]) for chunk in chunk_text(body)]
    else:
        records = [(chunk, "") for chunk in chunk_text(text)]

    if not records:
        raise ValueError("Refusing to replace an index with empty source material")
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    client = chromadb.PersistentClient(path=str(ROOT / "chroma_db"))
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    ids = [f"{collection_name}_{i}" for i in range(len(records))]
    stale_ids = set(collection.get(include=[])["ids"]) - set(ids)
    # Chroma computes embeddings before writing. Keep old data if embedding fails.
    collection.upsert(
        documents=[f"{metadata.get(url, {}).get('title', collection_name)}\n{chunk}" for chunk, url in records],
        metadatas=[{"source": url, "retrieved_at": metadata.get(url, {}).get("retrieved_at", "unknown")}
                   for _, url in records],
        ids=ids,
    )
    if stale_ids:
        collection.delete(ids=list(stale_ids))

    print(f"  ✅ {len(records)} chunks stored")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build source-attributed search indexes")
    parser.add_argument("--domain", choices=["academics", "campus", "financial_aid"])
    args = parser.parse_args()
    for domain in ([args.domain] if args.domain else ["academics", "campus", "financial_aid"]):
        embed_file(f"context/{domain}.txt", domain)
