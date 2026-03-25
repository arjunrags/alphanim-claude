from fastapi import APIRouter
from models import SearchRequest, SearchResponse, Paper
from services import llm_service, arxiv_service, chroma_service, membrain_service

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest):
    """
    Main search pipeline:
    1. Expand query with LLM
    2. Fetch papers from ArXiv
    3. Store papers in ChromaDB
    4. Re-rank with ChromaDB semantic search
    5. Store papers in Membrain + full-mesh link them
    6. Return enriched results
    """
    # Step 1: Expand query
    expanded = await llm_service.expand_query(req.query)
    print(f"[Search] Original: '{req.query}' → Expanded: '{expanded}'")

    # Step 2: Fetch from ArXiv
    arxiv_papers = await arxiv_service.fetch_papers(expanded, max_results=req.k + 5)

    if not arxiv_papers:
        return SearchResponse(query=req.query, expanded_query=expanded, papers=[])

    # Step 3: Store in ChromaDB for semantic ranking
    chroma_service.upsert_papers(arxiv_papers)

    # Step 4: Re-rank with ChromaDB (semantic similarity to original query)
    ranked = chroma_service.search_similar(req.query, k=req.k)

    # Map ranked IDs back to full Paper objects
    paper_map = {p.id: p for p in arxiv_papers}
    final_papers: list[Paper] = []
    for r in ranked:
        pid = r["id"]
        if pid in paper_map:
            p = paper_map[pid]
        else:
            # Paper was already in ChromaDB from a previous search
            p = Paper(
                id=pid,
                title=r["title"],
                abstract="",
                authors=r["authors"],
                year=r["year"],
                arxiv_url=r["arxiv_url"],
                tags=r["tags"],
            )
        final_papers.append(p)

    # Step 5: Ingest into Membrain + full-mesh link
    final_papers = await membrain_service.ingest_and_link_papers(final_papers)

    return SearchResponse(
        query=req.query,
        expanded_query=expanded,
        papers=final_papers,
    )
