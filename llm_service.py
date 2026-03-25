import httpx
import os

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

async def expand_query(query: str) -> str:
    """
    Takes a short user query and expands it into a richer
    search string using the local Ollama LLM.
    Falls back to the original query if Ollama is unavailable.
    """
    prompt = (
        f"You are a research assistant. A user is searching for academic papers.\n"
        f"Expand this short query into a detailed search phrase that will find "
        f"relevant academic papers. Include related technical terms, synonyms, and "
        f"key concepts. Return ONLY the expanded query, nothing else.\n\n"
        f"Query: {query}\n"
        f"Expanded query:"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            expanded = data.get("response", "").strip()
            return expanded if expanded else query
    except Exception as e:
        print(f"[LLM] Ollama unavailable, using original query. Error: {e}")
        return query


async def summarize_abstract(abstract: str) -> str:
    """
    Summarizes a long abstract into 2 sentences.
    Falls back to the first 300 chars if Ollama is unavailable.
    """
    prompt = (
        f"Summarize this academic paper abstract in exactly 2 concise sentences. "
        f"Return ONLY the summary, nothing else.\n\nAbstract: {abstract}\n\nSummary:"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            summary = data.get("response", "").strip()
            return summary if summary else abstract[:300]
    except Exception:
        return abstract[:300]
