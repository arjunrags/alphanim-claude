from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search, papers, graph, memories

app = FastAPI(title="Semantic Research Explorer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api")
app.include_router(papers.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(memories.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok"}
