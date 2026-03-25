import httpx
import xml.etree.ElementTree as ET
from models import Paper
import re

ARXIV_API = "https://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _parse_arxiv_id(url: str) -> str:
    """Extract arxiv ID from URL like http://arxiv.org/abs/2301.12345v1"""
    match = re.search(r"abs/(.+?)(?:v\d+)?$", url)
    return match.group(1) if match else url


async def fetch_papers(query: str, max_results: int = 10) -> list[Paper]:
    """
    Fetch papers from ArXiv API using the expanded query.
    Returns a list of Paper objects.
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(ARXIV_API, params=params)
            response.raise_for_status()
    except Exception as e:
        print(f"[ArXiv] Fetch failed: {e}")
        return []

    root = ET.fromstring(response.text)
    papers = []

    for entry in root.findall("atom:entry", NS):
        # Extract fields
        title_el = entry.find("atom:title", NS)
        abstract_el = entry.find("atom:summary", NS)
        published_el = entry.find("atom:published", NS)
        id_el = entry.find("atom:id", NS)

        if not title_el or not id_el:
            continue

        title = _clean_text(title_el.text or "")
        abstract = _clean_text(abstract_el.text or "") if abstract_el else ""
        arxiv_url = (id_el.text or "").strip()
        arxiv_id = _parse_arxiv_id(arxiv_url)
        year = (published_el.text or "")[:4] if published_el else ""

        # Authors
        authors = []
        for author_el in entry.findall("atom:author", NS):
            name_el = author_el.find("atom:name", NS)
            if name_el and name_el.text:
                authors.append(name_el.text.strip())

        # Categories as tags
        tags = []
        for cat_el in entry.findall("atom:category", NS):
            term = cat_el.get("term", "")
            if term:
                tags.append(f"topic.{term}")

        papers.append(
            Paper(
                id=arxiv_id,
                title=title,
                abstract=abstract,
                authors=authors[:5],  # cap at 5 authors
                year=year,
                arxiv_url=arxiv_url,
                tags=tags,
            )
        )

    return papers
