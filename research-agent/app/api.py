"""
FastAPI REST API — Research Agent
Serves the React frontend from /static at the root path.
LangChain 1.x compatible imports.
"""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.sources import (
    aggregate_sources,
    ingest_papers,
    ingest_file,
    ingest_url,
    ingest_text,
    get_knowledge_base_stats,
    fetch_arxiv_papers,
    fetch_semantic_scholar,
    fetch_crossref,
)
from app.intelligence import (
    generate_literature_review,
    analyze_trends,
    detect_citation_gaps,
    answer_research_question,
    build_knowledge_graph,
    critique_paper,
    cluster_topics,
)
from app.conversation import (
    create_session,
    delete_session,
    get_or_create,
    list_sessions,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ResearchMind — IBM WatsonX Research Agent",
    description=(
        "Intelligent research companion that aggregates academic sources, "
        "synthesizes literature, detects citation gaps, predicts research trends, "
        "and builds knowledge graphs — powered by IBM WatsonX Granite + Slate."
    ),
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve React frontend ───────────────────────────────────────────────────────
_STATIC = Path(__file__).parent.parent / "static"
if _STATIC.exists() and (_STATIC / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(_STATIC / "assets")), name="assets")


# ══════════════════════════════════════════════════════════════════════════════
# REQUEST / RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════════════════

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    sources: List[str] = Field(default=["arxiv", "semantic_scholar", "crossref"])
    max_per_source: int = Field(default=8, ge=1, le=25)
    ingest_immediately: bool = Field(default=True)


class IngestTextRequest(BaseModel):
    text: str = Field(..., min_length=20)
    source_name: str = Field(default="user_note")


class IngestUrlRequest(BaseModel):
    url: str


class LiteratureReviewRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class TrendAnalysisRequest(BaseModel):
    domain: str


class CitationGapRequest(BaseModel):
    topic: str


class ResearchQARequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class KnowledgeGraphRequest(BaseModel):
    topic: str


class PaperCritiqueRequest(BaseModel):
    paper_title: str


class ClusterRequest(BaseModel):
    domain: str
    n_clusters: int = Field(default=5, ge=2, le=15)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH & INFO
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api-info", tags=["health"])
def root():
    return {
        "service": "ResearchMind — Intelligent Research Agent",
        "powered_by": "IBM WatsonX Granite + Slate Embeddings",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy", "llm": settings.llm_model_id}


@app.get("/stats", tags=["knowledge-base"])
def kb_stats():
    return get_knowledge_base_stats()


# ══════════════════════════════════════════════════════════════════════════════
# ACADEMIC SOURCE SEARCH & INGESTION
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/search", tags=["sources"])
def search_and_ingest(req: SearchRequest):
    papers = aggregate_sources(
        query=req.query,
        sources=req.sources,
        max_per_source=req.max_per_source,
    )
    result: dict = {"papers_found": len(papers), "papers": papers}
    if req.ingest_immediately and papers:
        result["ingestion"] = ingest_papers(papers)
    return result


@app.get("/search/arxiv", tags=["sources"])
def search_arxiv(
    query: str = Query(...),
    max_results: int = Query(default=10, ge=1, le=50),
):
    papers = fetch_arxiv_papers(query, max_results=max_results)
    return {"source": "arxiv", "count": len(papers), "papers": papers}


@app.get("/search/semantic-scholar", tags=["sources"])
def search_semantic_scholar(
    query: str = Query(...),
    limit: int = Query(default=10, ge=1, le=50),
):
    papers = fetch_semantic_scholar(query, limit=limit)
    return {"source": "semantic_scholar", "count": len(papers), "papers": papers}


@app.get("/search/crossref", tags=["sources"])
def search_crossref(
    query: str = Query(...),
    rows: int = Query(default=10, ge=1, le=50),
):
    papers = fetch_crossref(query, rows=rows)
    return {"source": "crossref", "count": len(papers), "papers": papers}


@app.post("/ingest/file", tags=["ingestion"])
async def upload_file(
    file: UploadFile = File(...),
    force: bool = Query(default=False),
):
    dest = Path(settings.docs_upload_dir) / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        return ingest_file(dest, force=force)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ingest/url", tags=["ingestion"])
def ingest_from_url(req: IngestUrlRequest):
    return ingest_url(req.url)


@app.post("/ingest/text", tags=["ingestion"])
def ingest_raw_text(req: IngestTextRequest):
    return ingest_text(req.text, req.source_name)


# ══════════════════════════════════════════════════════════════════════════════
# RESEARCH INTELLIGENCE
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/research/literature-review", tags=["intelligence"])
def literature_review(req: LiteratureReviewRequest):
    try:
        return generate_literature_review(req.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/research/trends", tags=["intelligence"])
def trend_analysis(req: TrendAnalysisRequest):
    try:
        return analyze_trends(req.domain)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/research/citation-gaps", tags=["intelligence"])
def citation_gaps(req: CitationGapRequest):
    try:
        return detect_citation_gaps(req.topic)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/research/ask", tags=["intelligence"])
def ask_question(req: ResearchQARequest):
    try:
        return answer_research_question(req.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/research/knowledge-graph", tags=["visualization"])
def knowledge_graph(req: KnowledgeGraphRequest):
    try:
        return build_knowledge_graph(req.topic)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/research/critique", tags=["intelligence"])
def paper_critique(req: PaperCritiqueRequest):
    try:
        return critique_paper(req.paper_title)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/research/clusters", tags=["visualization"])
def topic_clusters(req: ClusterRequest):
    try:
        return cluster_topics(req.domain, req.n_clusters)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ══════════════════════════════════════════════════════════════════════════════
# CONVERSATIONAL CHAT
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/chat", tags=["conversation"])
def chat(req: ChatRequest):
    session = get_or_create(req.session_id)
    try:
        return session.chat(req.message)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat/session/new", tags=["conversation"])
def new_session():
    sid = create_session()
    return {"session_id": sid}


@app.get("/chat/session/{session_id}/history", tags=["conversation"])
def history(session_id: str):
    session = get_or_create(session_id)
    return {"session_id": session_id, "history": session.get_history()}


@app.delete("/chat/session/{session_id}", tags=["conversation"])
def end_session(session_id: str):
    return {"deleted": delete_session(session_id)}


@app.get("/chat/sessions", tags=["conversation"])
def all_sessions():
    return {"sessions": list_sessions()}


# ── SPA fallback (must be last) ───────────────────────────────────────────────
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """Serve index.html for all non-API routes (React SPA)."""
    # Let FastAPI handle its own routes first; only catch unknown paths here
    index = _STATIC / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "Frontend not built. Run: cd frontend && npm install && npm run build"}
