import chromadb
from chromadb.utils import embedding_functions
from models import Paper
import os

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_data")

# Use sentence-transformers for local embeddings (no API key needed)
# Model downloads automatically on first run (~90MB)
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name="research_papers",
    embedding_function=_embed_fn,
    metadata={"hnsw:space": "cosine"},
)


def _paper_to_document(paper: Paper) -> str:
    """Combine title + abstract for embedding."""
    return f"{paper.title}. {paper.abstract}"


def upsert_papers(papers: list[Paper]) -> None:
    """
    Add or update papers in ChromaDB.
    Uses paper.id as the document ID so duplicates are handled automatically.
    """
    if not papers:
        return

    ids = [p.id for p in papers]
    documents = [_paper_to_document(p) for p in papers]
    metadatas = [
        {
            "title": p.title,
            "authors": ", ".join(p.authors),
            "year": p.year or "",
            "arxiv_url": p.arxiv_url or "",
            "tags": ",".join(p.tags),
        }
        for p in papers
    ]

    _collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[ChromaDB] Upserted {len(papers)} papers.")


def search_similar(query: str, k: int = 8) -> list[dict]:
    """
    Search ChromaDB for papers semantically similar to query.
    Returns list of dicts with id, title, score, metadata.
    """
    results = _collection.query(
        query_texts=[query],
        n_results=min(k, _collection.count() or 1),
        include=["documents", "metadatas", "distances"],
    )

    papers_out = []
    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for pid, meta, dist in zip(ids, metadatas, distances):
        papers_out.append(
            {
                "id": pid,
                "title": meta.get("title", ""),
                "authors": meta.get("authors", "").split(", "),
                "year": meta.get("year", ""),
                "arxiv_url": meta.get("arxiv_url", ""),
                "tags": [t for t in meta.get("tags", "").split(",") if t],
                "similarity_score": round(1 - dist, 4),  # cosine → similarity
            }
        )

    return papers_out


def collection_count() -> int:
    return _collection.count()
