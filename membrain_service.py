import httpx
import os
import asyncio
from models import Paper

MEMBRAIN_BASE = os.getenv("MEMBRAIN_BASE_URL", "https://your-membrain-host.com")
MEMBRAIN_KEY = os.getenv("MEMBRAIN_API_KEY", "")

HEADERS = {
    "X-API-Key": MEMBRAIN_KEY,
    "Content-Type": "application/json",
}


# ─── Core helpers ────────────────────────────────────────────────────────────

async def _post(path: str, body: dict) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(f"{MEMBRAIN_BASE}/api/v1{path}", json=body, headers=HEADERS)
        r.raise_for_status()
        return r.json()


async def _get(path: str, params: dict = None) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{MEMBRAIN_BASE}/api/v1{path}", params=params, headers=HEADERS)
        r.raise_for_status()
        return r.json()


async def _poll_job(job_id: str, max_attempts: int = 20) -> dict | None:
    """
    Poll a Membrain ingest job until completed or failed.
    Returns the result dict or None on failure.
    """
    for _ in range(max_attempts):
        await asyncio.sleep(1.5)
        data = await _get(f"/memories/jobs/{job_id}")
        status = data.get("status") or data.get("job_status")
        if status == "completed":
            return data.get("result", {})
        if status == "failed":
            print(f"[Membrain] Job {job_id} failed: {data.get('error')}")
            return None
    print(f"[Membrain] Job {job_id} timed out.")
    return None


# ─── Store a paper as a Membrain memory ──────────────────────────────────────

async def store_paper_memory(paper: Paper) -> str | None:
    """
    Store a research paper as an atomic Membrain memory.
    Returns the memory_id string or None on failure.

    The content is a concise factual statement about the paper.
    Tags encode topic, year, and type so we can filter later.
    """
    content = (
        f"Research paper: \"{paper.title}\" "
        f"by {', '.join(paper.authors[:3])}{'et al.' if len(paper.authors) > 3 else ''}. "
        f"Published {paper.year}. "
        f"Abstract: {paper.abstract[:400]}"
    )

    tags = list(paper.tags)  # topic.cs.AI etc. from ArXiv
    tags += [
        "type.research_paper",
        f"arxiv.{paper.id.replace('/', '_')}",
    ]
    if paper.year:
        tags.append(f"year.{paper.year}")

    try:
        job_data = await _post("/memories", {
            "content": content,
            "tags": tags[:50],
            "category": "research_paper",
        })
        job_id = job_data.get("job_id")
        if not job_id:
            return None

        result = await _poll_job(job_id)
        if result:
            return result.get("memory_id")
    except Exception as e:
        print(f"[Membrain] store_paper_memory failed for {paper.id}: {e}")

    return None


# ─── Full-mesh link all top search results ───────────────────────────────────

async def link_papers_full_mesh(memory_ids: list[str]) -> None:
    """
    After a search, link every paper to every other paper (full mesh).
    This is done by searching Membrain with each paper's memory ID
    and letting Membrain's Guardian logic handle relationship creation.

    We use the /memories/search endpoint to find relationships between
    already-stored memories, which triggers Membrain's graph linking.
    """
    if len(memory_ids) < 2:
        return

    # Search for each memory by ID to trigger graph linking
    # Membrain's Guardian will propose links between semantically similar memories
    tasks = []
    for memory_id in memory_ids:
        tasks.append(_link_single_paper_to_others(memory_id, memory_ids))

    await asyncio.gather(*tasks, return_exceptions=True)
    print(f"[Membrain] Full-mesh linking triggered for {len(memory_ids)} papers.")


async def _link_single_paper_to_others(memory_id: str, all_ids: list[str]) -> None:
    """
    Search Membrain using this paper's memory content, which surfaces
    related memories and triggers Guardian linking.
    """
    try:
        # Fetch the memory content first
        mem = await _get(f"/memories/{memory_id}")
        content = mem.get("content", "")
        if not content:
            return

        # Search with the paper's content — this surfaces similar papers
        # and allows Membrain to create relationship edges
        await _post("/memories/search", {
            "query": content[:500],
            "k": len(all_ids),
            "response_format": "raw",
            "keyword_filter": "type\\.research_paper",
        })
    except Exception as e:
        print(f"[Membrain] _link_single_paper failed for {memory_id}: {e}")


# ─── Full pipeline: store + link ─────────────────────────────────────────────

async def ingest_and_link_papers(papers: list[Paper]) -> list[Paper]:
    """
    1. Store each paper as a Membrain memory (in parallel)
    2. Full-mesh link all resulting memory IDs
    3. Return papers with memory_id set
    """
    # Store all papers concurrently
    memory_ids = await asyncio.gather(
        *[store_paper_memory(p) for p in papers],
        return_exceptions=True,
    )

    enriched = []
    valid_memory_ids = []

    for paper, mid in zip(papers, memory_ids):
        if isinstance(mid, str):
            paper.memory_id = mid
            valid_memory_ids.append(mid)
        enriched.append(paper)

    # Full-mesh link all successfully stored memories
    if len(valid_memory_ids) >= 2:
        await link_papers_full_mesh(valid_memory_ids)

    return enriched


# ─── Graph export for frontend ───────────────────────────────────────────────

async def get_graph() -> dict:
    """
    Export the full Membrain graph (nodes + edges) for the frontend.
    Filters to only research_paper memories.
    """
    try:
        data = await _get("/graph/export")
        nodes = []
        edges = []

        for node in data.get("nodes", []):
            tags = node.get("tags", [])
            if "type.research_paper" in tags:
                nodes.append({
                    "id": node["id"],
                    "title": node.get("content", "")[:80],
                    "tags": tags,
                    "year": next((t.replace("year.", "") for t in tags if t.startswith("year.")), ""),
                })

        node_ids = {n["id"] for n in nodes}
        for edge in data.get("edges", []):
            src = edge.get("source_id") or edge.get("source")
            tgt = edge.get("target_id") or edge.get("target")
            if src in node_ids and tgt in node_ids:
                edges.append({
                    "source": src,
                    "target": tgt,
                    "description": edge.get("description", ""),
                })

        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"[Membrain] get_graph failed: {e}")
        return {"nodes": [], "edges": []}


async def search_memories(query: str, k: int = 5) -> dict:
    """Search Membrain for related paper memories."""
    try:
        return await _post("/memories/search", {
            "query": query,
            "k": k,
            "response_format": "interpreted",
            "keyword_filter": "type\\.research_paper",
        })
    except Exception as e:
        print(f"[Membrain] search_memories failed: {e}")
        return {}
