import chromadb
from chromadb.utils import embedding_functions

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="chroma_db")

def chunk_text(text: str, chunk_size: int = 500) -> list:
    words = text.split()
    chunks = []
    current = []
    current_len = 0

    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current))
            current = []
            current_len = 0

    if current:
        chunks.append(" ".join(current))

    return chunks

def embed_file(filepath: str, collection_name: str):
    print(f"Embedding {filepath} into '{collection_name}'...")

    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    chunks = chunk_text(text)

    try:
        client.delete_collection(collection_name)
    except:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_fn
    )

    collection.add(
        documents=chunks,
        ids=[f"{collection_name}_{i}" for i in range(len(chunks))]
    )

    print(f"  ✅ {len(chunks)} chunks stored")

if __name__ == "__main__":
    embed_file("context/academics.txt", "academics")
    embed_file("context/campus.txt", "campus")
    embed_file("context/financial_aid.txt", "financial_aid")
    print("\n✅ All files embedded.")