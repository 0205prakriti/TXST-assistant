import sys

try:
    import chromadb
    from chromadb.utils import embedding_functions

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    client = chromadb.PersistentClient(path="chroma_db")

    def retrieve(query: str, collection_name: str, n_results: int = 3) -> str:
        try:
            collection = client.get_collection(
                name=collection_name,
                embedding_function=embedding_fn
            )
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            chunks = results["documents"][0]
            return "\n\n".join(chunks)
        except Exception as e:
            print(f"Retrieval error: {e}")
            return ""
except Exception:
    # chromadb or its heavy dependencies aren't available (or failing to import).
    # Provide a lightweight stub used during tests and quick local runs.
    def retrieve(query: str, collection_name: str, n_results: int = 3) -> str:
        return ""