"""
Academic Source Fusion — Multi-Source Paper Aggregation & Ingestion
LangChain 1.x: langchain.schema.Document -> langchain_core.documents.Document
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    WebBaseLoader,
)

from app.config import settings
from app.vector_store import add_documents

logger = logging.getLogger(__name__)

REGISTRY_PATH = Path(settings.processed_docs_dir) / "research_registry.json"


# ── Registry ─────────────────────────────────────────────────────────────────

def _load_registry() -> Dict[str, Any]:
    if REGISTRY_PATH.exists():
        return json.loads(REGISTRY_PATH.read_text())
    return {}


def _save_registry(reg: Dict[str, Any]) -> None:
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(json.dumps(reg, indent=2))


def _doc_id(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


# ── Text Splitter ─────────────────────────────────────────────────────────────

def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    )


# ── arXiv Source ─────────────────────────────────────────────────────────────

def fetch_arxiv_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
) -> List[Dict[str, Any]]:
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": "descending",
    }
    try:
        resp = requests.get(settings.arxiv_base_url, params=params, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        logger.error("arXiv fetch failed: %s", exc)
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)
    papers = []

    for entry in root.findall("atom:entry", ns):
        title = entry.findtext("atom:title", default="", namespaces=ns).strip().replace("\n", " ")
        abstract = entry.findtext("atom:summary", default="", namespaces=ns).strip()
        published = entry.findtext("atom:published", default="", namespaces=ns)[:10]
        arxiv_id_tag = entry.findtext("atom:id", default="", namespaces=ns)
        arxiv_id = arxiv_id_tag.split("/abs/")[-1] if "/abs/" in arxiv_id_tag else arxiv_id_tag
        authors = [
            a.findtext("atom:name", default="", namespaces=ns)
            for a in entry.findall("atom:author", ns)
        ]
        categories = [c.get("term", "") for c in entry.findall("atom:category", ns)]
        pdf_url = ""
        for link in entry.findall("atom:link", ns):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href", "")

        papers.append({
            "source": "arxiv",
            "id": arxiv_id,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "published": published,
            "categories": categories,
            "pdf_url": pdf_url,
            "url": arxiv_id_tag,
        })

    logger.info("arXiv: fetched %d papers for query '%s'", len(papers), query)
    return papers


# ── Semantic Scholar Source ───────────────────────────────────────────────────

def fetch_semantic_scholar(
    query: str,
    limit: int = 10,
    fields: str = "title,abstract,authors,year,citationCount,externalIds,url",
) -> List[Dict[str, Any]]:
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    headers = {}
    if settings.semantic_scholar_api_key:
        headers["x-api-key"] = settings.semantic_scholar_api_key

    params = {"query": query, "limit": limit, "fields": fields}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json().get("data", [])
    except requests.RequestException as exc:
        logger.error("Semantic Scholar fetch failed: %s", exc)
        return []

    papers = []
    for item in data:
        papers.append({
            "source": "semantic_scholar",
            "id": item.get("paperId", ""),
            "title": item.get("title", ""),
            "abstract": item.get("abstract") or "",
            "authors": [a.get("name", "") for a in item.get("authors", [])],
            "year": str(item.get("year", "")),
            "citation_count": item.get("citationCount", 0),
            "url": item.get("url", ""),
            "doi": (item.get("externalIds") or {}).get("DOI", ""),
        })

    logger.info("Semantic Scholar: fetched %d papers for query '%s'", len(papers), query)
    return papers


# ── CrossRef Source ───────────────────────────────────────────────────────────

def fetch_crossref(query: str, rows: int = 10) -> List[Dict[str, Any]]:
    params = {
        "query": query,
        "rows": rows,
        "select": "title,abstract,author,published,DOI,URL,is-referenced-by-count,type",
        "sort": "relevance",
    }
    try:
        resp = requests.get(
            settings.crossref_base_url,
            params=params,
            timeout=15,
            headers={"User-Agent": "ResearchAgent/1.0 (mailto:research@example.com)"},
        )
        resp.raise_for_status()
        items = resp.json().get("message", {}).get("items", [])
    except requests.RequestException as exc:
        logger.error("CrossRef fetch failed: %s", exc)
        return []

    papers = []
    for item in items:
        title_list = item.get("title", [])
        title = title_list[0] if title_list else ""
        abstract = re.sub(r"<[^>]+>", "", item.get("abstract", ""))
        authors = [
            f"{a.get('given', '')} {a.get('family', '')}".strip()
            for a in item.get("author", [])
        ]
        published = item.get("published", {}).get("date-parts", [[""]])[0]
        year = str(published[0]) if published else ""

        papers.append({
            "source": "crossref",
            "id": item.get("DOI", ""),
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "year": year,
            "citation_count": item.get("is-referenced-by-count", 0),
            "doi": item.get("DOI", ""),
            "url": item.get("URL", ""),
            "type": item.get("type", ""),
        })

    logger.info("CrossRef: fetched %d papers for query '%s'", len(papers), query)
    return papers


# ── Unified Aggregator ────────────────────────────────────────────────────────

def aggregate_sources(
    query: str,
    sources: List[str] = None,
    max_per_source: int = 8,
) -> List[Dict[str, Any]]:
    sources = sources or ["arxiv", "semantic_scholar", "crossref"]
    all_papers: List[Dict[str, Any]] = []

    if "arxiv" in sources:
        all_papers.extend(fetch_arxiv_papers(query, max_results=max_per_source))
        time.sleep(0.3)
    if "semantic_scholar" in sources:
        all_papers.extend(fetch_semantic_scholar(query, limit=max_per_source))
        time.sleep(0.3)
    if "crossref" in sources:
        all_papers.extend(fetch_crossref(query, rows=max_per_source))

    seen_titles: set = set()
    unique: List[Dict[str, Any]] = []
    for p in all_papers:
        key = p["title"].lower()[:80]
        if key and key not in seen_titles:
            seen_titles.add(key)
            unique.append(p)

    logger.info("Aggregated %d unique papers from %s", len(unique), sources)
    return unique


# ── Document Ingestion ────────────────────────────────────────────────────────

def papers_to_documents(papers: List[Dict[str, Any]]) -> List[Document]:
    docs = []
    for p in papers:
        content = (
            f"TITLE: {p.get('title', '')}\n\n"
            f"AUTHORS: {', '.join(p.get('authors', []))}\n\n"
            f"YEAR/DATE: {p.get('published') or p.get('year', 'N/A')}\n\n"
            f"SOURCE: {p.get('source', '').upper()} | {p.get('url') or p.get('doi', '')}\n\n"
            f"ABSTRACT:\n{p.get('abstract', 'Abstract not available.')}\n\n"
            f"CITATION COUNT: {p.get('citation_count', 'N/A')}\n"
            f"CATEGORIES: {', '.join(p.get('categories', []))}\n"
        )
        docs.append(
            Document(
                page_content=content,
                metadata={
                    "source": p.get("url") or p.get("doi") or p.get("id", ""),
                    "source_type": p.get("source", "paper"),
                    "title": p.get("title", ""),
                    "authors": ", ".join(p.get("authors", [])),
                    "year": str(
                        (p.get("published", "") or "")[:4]
                        if p.get("published")
                        else p.get("year", "")
                    ),
                    "citation_count": p.get("citation_count", 0),
                    "doi": p.get("doi", ""),
                    "ingested_at": datetime.utcnow().isoformat(),
                },
            )
        )
    return docs


def ingest_papers(papers: List[Dict[str, Any]], force: bool = False) -> Dict[str, Any]:
    registry = _load_registry()
    new_docs: List[Document] = []
    skipped = 0

    for p in papers:
        pid = _doc_id(p.get("title", "") + p.get("abstract", ""))
        if not force and pid in registry:
            skipped += 1
            continue
        docs = papers_to_documents([p])
        chunks = _splitter().split_documents(docs)
        new_docs.extend(chunks)
        registry[pid] = {
            "title": p.get("title", ""),
            "source": p.get("source", ""),
            "chunks": len(chunks),
            "ingested_at": datetime.utcnow().isoformat(),
        }

    if new_docs:
        add_documents(new_docs)
        _save_registry(registry)

    return {
        "ingested": len(papers) - skipped,
        "skipped": skipped,
        "chunks_added": len(new_docs),
        "total_indexed": len(registry),
    }


def ingest_file(file_path: "str | Path", force: bool = False) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    registry = _load_registry()
    file_hash = hashlib.md5(path.read_bytes()).hexdigest()
    if not force and file_hash in registry:
        return {"status": "skipped", "file": path.name, "reason": "already ingested"}

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        loader = PyPDFLoader(str(path))
    elif suffix in (".docx", ".doc"):
        loader = Docx2txtLoader(str(path))
    else:
        loader = TextLoader(str(path), encoding="utf-8")

    raw_docs = loader.load()
    for d in raw_docs:
        d.metadata.update({
            "source": path.name,
            "source_type": "uploaded_file",
            "ingested_at": datetime.utcnow().isoformat(),
        })

    chunks = _splitter().split_documents(raw_docs)
    add_documents(chunks)

    registry[file_hash] = {
        "file": path.name,
        "chunks": len(chunks),
        "ingested_at": datetime.utcnow().isoformat(),
    }
    _save_registry(registry)
    return {"status": "success", "file": path.name, "chunks": len(chunks)}


def ingest_url(url: str) -> Dict[str, Any]:
    try:
        loader = WebBaseLoader(url)
        raw_docs = loader.load()
        for d in raw_docs:
            d.metadata.update({
                "source": url,
                "source_type": "web",
                "ingested_at": datetime.utcnow().isoformat(),
            })
        chunks = _splitter().split_documents(raw_docs)
        add_documents(chunks)
        return {"status": "success", "url": url, "chunks": len(chunks)}
    except Exception as exc:
        logger.error("URL ingestion failed for %s: %s", url, exc)
        return {"status": "error", "url": url, "error": str(exc)}


def ingest_text(text: str, source_name: str = "user_note") -> Dict[str, Any]:
    doc = Document(
        page_content=text,
        metadata={
            "source": source_name,
            "source_type": "text_note",
            "ingested_at": datetime.utcnow().isoformat(),
        },
    )
    chunks = _splitter().split_documents([doc])
    add_documents(chunks)
    return {"status": "success", "source": source_name, "chunks": len(chunks)}


def get_knowledge_base_stats() -> Dict[str, Any]:
    registry = _load_registry()
    total_chunks = sum(v.get("chunks", 0) for v in registry.values())
    return {
        "documents_indexed": len(registry),
        "total_chunks": total_chunks,
        "collection": settings.chroma_collection_name,
        "sources_breakdown": _source_breakdown(registry),
    }


def _source_breakdown(registry: Dict) -> Dict[str, int]:
    breakdown: Dict[str, int] = {}
    for v in registry.values():
        src = v.get("source", "unknown")
        breakdown[src] = breakdown.get(src, 0) + 1
    return breakdown
