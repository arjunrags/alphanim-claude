# Semantic Research Explorer

A research paper explorer powered by ArXiv, ChromaDB, Membrain, and a local LLM (Ollama).

## How it works

1. You type a search query (e.g. "attention mechanisms in transformers")
2. Ollama expands your query into richer search terms
3. ArXiv API fetches real matching papers
4. ChromaDB ranks them by semantic similarity
5. Membrain stores each paper as a memory and **full-mesh links** all results together
6. The frontend shows paper cards + an interactive D3 graph of linked papers

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com) installed locally
- A Membrain API key

---

### 1. Start Ollama

```bash
# Install from https://ollama.com, then:
ollama pull llama3.2
ollama serve
```

Ollama will run at `http://localhost:11434`.

---

### 2. Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and fill in MEMBRAIN_BASE_URL and MEMBRAIN_API_KEY

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be at `http://localhost:8000`.
Interactive docs at `http://localhost:8000/docs`.

> **Note:** On first run, ChromaDB will download the `all-MiniLM-L6-v2`
> embedding model (~90MB). This is a one-time download.

---

### 3. Frontend

```bash
cd frontend

npm install
npm run dev
```

Open `http://localhost:5173`.

---

## Project structure

```
semantic-explorer/
├── backend/
│   ├── main.py                   # FastAPI app
│   ├── models.py                 # Pydantic schemas
│   ├── requirements.txt
│   ├── .env.example
│   ├── routers/
│   │   ├── search.py             # POST /api/search  ← main pipeline
│   │   ├── graph.py              # GET  /api/graph
│   │   ├── papers.py             # GET  /api/papers/count
│   │   └── memories.py          # POST /api/memories/search
│   └── services/
│       ├── llm_service.py        # Ollama query expansion
│       ├── arxiv_service.py      # ArXiv paper fetching
│       ├── chroma_service.py     # ChromaDB vector store
│       └── membrain_service.py  # Membrain memory + graph
└── frontend/
    └── src/
        ├── App.jsx
        └── components/
            ├── SearchBar.jsx
            ├── PaperCard.jsx
            ├── GraphCanvas.jsx   # D3 force-directed graph
            └── InsightPanel.jsx  # Membrain insights sidebar
```

---

## The search pipeline (step by step)

```
User query
   ↓
llm_service.expand_query()       Ollama rewrites query into richer terms
   ↓
arxiv_service.fetch_papers()     Fetches up to 13 papers from ArXiv
   ↓
chroma_service.upsert_papers()   Stores papers as vectors in ChromaDB
   ↓
chroma_service.search_similar()  Re-ranks by cosine similarity to original query
   ↓
membrain_service.ingest_and_link_papers()
   ├── store_paper_memory()      Stores each paper as a Membrain memory (async)
   └── link_papers_full_mesh()   Searches Membrain with each paper's content,
                                  triggering Guardian to link similar papers
   ↓
Frontend receives enriched papers with memory_id set
```

---

## Membrain tag scheme

Every paper stored in Membrain gets these tags:

| Tag | Example | Purpose |
|-----|---------|---------|
| `type.research_paper` | — | Filters in graph/search queries |
| `topic.<arxiv_cat>` | `topic.cs.AI` | ArXiv category |
| `year.<year>` | `year.2024` | Time filtering |
| `arxiv.<id>` | `arxiv.2301_12345` | Unique paper identifier |

---

## Viewing the graph

After running at least one search, click the **Graph** tab. You'll see:

- **Nodes** = research papers (showing year in the circle)
- **Edges** = semantic links Membrain created between similar papers
- Scroll to zoom, drag to pan, drag individual nodes

The graph grows richer with every search you run.

---

## Swapping the LLM

To use a different Ollama model, change `OLLAMA_MODEL` in `.env`:

```
OLLAMA_MODEL=mistral
OLLAMA_MODEL=phi3
OLLAMA_MODEL=gemma2
```

If Ollama is unavailable, the app falls back gracefully to using the original query directly.
