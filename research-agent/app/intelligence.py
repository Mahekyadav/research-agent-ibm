"""
Research Intelligence Engine — LangChain 1.x LCEL implementation.
RetrievalQA / ConversationalRetrievalChain no longer exist in langchain 1.x;
replaced with LCEL: retriever | prompt | llm | parser chains.
"""
from __future__ import annotations

import json
import logging
import re
from operator import itemgetter
from typing import List, Dict, Any, Optional, Tuple

from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from app.config import settings
from app.vector_store import get_vector_store, similarity_search_with_score
from app.llm_client import get_llm

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _format_docs(docs: List[Document]) -> str:
    return "\n\n---\n\n".join(
        f"[{d.metadata.get('title', 'Paper')} | {d.metadata.get('year', '')}]\n{d.page_content}"
        for d in docs
    )


def _extract_sources(docs: List[Document]) -> List[Dict[str, Any]]:
    seen: set = set()
    sources = []
    for d in docs:
        key = d.metadata.get("source", "unknown")
        if key not in seen:
            seen.add(key)
            sources.append({
                "source": key,
                "title": d.metadata.get("title", ""),
                "authors": d.metadata.get("authors", ""),
                "year": d.metadata.get("year", ""),
                "source_type": d.metadata.get("source_type", "paper"),
                "citation_count": d.metadata.get("citation_count", 0),
            })
    return sources


def _get_retriever():
    return get_vector_store().as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.top_k_retrieval},
    )


def _invoke_rag(prompt_template: PromptTemplate, question: str) -> Dict[str, Any]:
    """
    Run a RAG chain: retrieve → format → prompt → LLM → parse.
    Returns {"result": str, "source_documents": List[Document]}.
    """
    retriever = _get_retriever()
    docs = retriever.invoke(question)
    context = _format_docs(docs)

    prompt_vars = {"context": context}
    # The prompt template uses either "question" or "query" — detect which
    if "question" in prompt_template.input_variables:
        prompt_vars["question"] = question
    else:
        prompt_vars["query"] = question

    prompt_text = prompt_template.format(**prompt_vars)
    llm = get_llm()
    result = llm.invoke(prompt_text)
    answer = result.strip() if isinstance(result, str) else str(result)
    return {"result": answer, "source_documents": docs}


# ══════════════════════════════════════════════════════════════════════════════
# PROMPT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

LITERATURE_REVIEW_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are ResearchMind — an expert academic AI assistant powered by IBM WatsonX Granite.
Your role is to synthesize academic literature into structured, insightful reviews.

RETRIEVED RESEARCH CONTEXT:
{context}

RESEARCH QUERY:
{question}

Write a comprehensive literature review that includes:

## Overview
[Brief overview of the research landscape]

## Key Findings & Themes
[Major findings grouped by theme, with paper references]

## Methodological Approaches
[Research methods used across the literature]

## Agreements & Debates
[Where researchers agree and where there are open debates]

## Research Gaps
[Notable gaps in current literature]

## Conclusion
[Synthesis and overall assessment]

LITERATURE REVIEW:
""",
)

RESEARCH_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are ResearchMind, powered by IBM WatsonX Granite. Provide a concise, accurate
research summary answering the user's specific question.

RETRIEVED CONTEXT:
{context}

QUESTION: {question}

Provide a structured answer including:
- Direct answer to the question
- Supporting evidence from the literature
- Key authors/papers referenced
- Confidence level (High/Medium/Low) and reasoning
- Suggested follow-up questions

RESEARCH SUMMARY:
""",
)

PAPER_CRITIQUE_PROMPT = PromptTemplate(
    input_variables=["context", "paper_title"],
    template="""You are ResearchMind, powered by IBM WatsonX Granite. Provide a critical analysis
of the following research paper.

PAPER CONTEXT:
{context}

PAPER: {paper_title}

## Critical Analysis

### Strengths
- [Key methodological/conceptual strengths]

### Limitations
- [Identified weaknesses or constraints]

### Novelty Assessment
[How novel is this contribution to the field? High/Medium/Low with justification]

### Reproducibility
[Can the work be reproduced? What would be needed?]

### Impact Assessment
[Likely influence on the field]

### Recommended Follow-Up Studies
- [Study 1]
- [Study 2]

CRITICAL ANALYSIS:
""",
)

TREND_ANALYSIS_PROMPT = PromptTemplate(
    input_variables=["context", "domain"],
    template="""You are ResearchMind, an IBM WatsonX Granite-powered research intelligence system.
Analyze the following research corpus for trends and emerging directions.

RESEARCH CORPUS:
{context}

RESEARCH DOMAIN: {domain}

## Emerging Trends (Last 2 Years)
[List top 5-7 emerging trends with evidence]

## Declining Research Areas
[Topics losing traction with reasons]

## Hot Topics & High-Citation Areas
[Most-cited themes and why they matter]

## Methodological Shifts
[Changes in research methods or tools]

## Interdisciplinary Connections
[Cross-domain influences and collaborations]

## Predicted Directions (Next 3-5 Years)
[Evidence-based predictions for future research]

TREND ANALYSIS:
""",
)

CITATION_GAP_PROMPT = PromptTemplate(
    input_variables=["context", "topic"],
    template="""You are ResearchMind, powered by IBM WatsonX Granite. Detect citation gaps and
underexplored research opportunities in the following literature.

LITERATURE CONTEXT:
{context}

RESEARCH TOPIC: {topic}

## Understudied Sub-Topics
[Areas with few or no papers despite clear relevance]

## Missing Connections
[Pairs of concepts/methods that should be studied together but aren't]

## Demographic / Geographic Gaps
[Populations, regions, or contexts that lack representation]

## Methodological Gaps
[Methods that have not been applied to this domain]

## Replication Needs
[Key findings that need independent replication]

## Recommended Research Directions (Priority Ranked)
1. [Highest priority gap]
2. [Second priority]
3. [Third priority]

CITATION GAP ANALYSIS:
""",
)

KNOWLEDGE_GRAPH_PROMPT = PromptTemplate(
    input_variables=["context", "topic"],
    template="""You are ResearchMind, powered by IBM WatsonX Granite. Extract a knowledge graph
from the research context below.

RESEARCH CONTEXT:
{context}

TOPIC: {topic}

Extract a JSON knowledge graph with entities and relationships:

{{
  "entities": [
    {{"id": "e1", "label": "concept/method/author/paper", "type": "concept|method|author|institution|dataset", "weight": 1-10}},
    ...
  ],
  "relationships": [
    {{"source": "e1", "target": "e2", "relation": "uses|proposes|cites|extends|contradicts|collaborates", "weight": 1-5}},
    ...
  ],
  "clusters": [
    {{"id": "c1", "name": "cluster name", "entities": ["e1", "e2"]}},
    ...
  ]
}}

Return ONLY valid JSON, no explanation:
""",
)


# ══════════════════════════════════════════════════════════════════════════════
# INTELLIGENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def generate_literature_review(query: str) -> Dict[str, Any]:
    logger.info("Generating literature review for: %s", query[:100])
    out = _invoke_rag(LITERATURE_REVIEW_PROMPT, query)
    return {
        "review": out["result"],
        "sources": _extract_sources(out["source_documents"]),
        "query": query,
        "type": "literature_review",
    }


def analyze_trends(domain: str) -> Dict[str, Any]:
    logger.info("Analyzing trends for domain: %s", domain)
    docs_with_scores = similarity_search_with_score(domain, k=settings.top_k_retrieval)
    context = "\n\n---\n\n".join(
        f"[{d.metadata.get('title', 'Paper')} | {d.metadata.get('year', '')}]\n{d.page_content}"
        for d, _ in docs_with_scores
    )
    llm = get_llm()
    analysis = llm.invoke(TREND_ANALYSIS_PROMPT.format(context=context, domain=domain))

    year_dist: Dict[str, int] = {}
    source_dist: Dict[str, int] = {}
    for d, _ in docs_with_scores:
        year = d.metadata.get("year", "unknown")
        src  = d.metadata.get("source_type", "unknown")
        year_dist[year]   = year_dist.get(year, 0) + 1
        source_dist[src]  = source_dist.get(src, 0) + 1

    return {
        "analysis": analysis.strip() if isinstance(analysis, str) else str(analysis),
        "domain": domain,
        "year_distribution": year_dist,
        "source_distribution": source_dist,
        "papers_analyzed": len(docs_with_scores),
        "type": "trend_analysis",
    }


def detect_citation_gaps(topic: str) -> Dict[str, Any]:
    logger.info("Detecting citation gaps for: %s", topic)
    docs_with_scores = similarity_search_with_score(topic, k=settings.top_k_retrieval)
    context = "\n\n---\n\n".join(d.page_content for d, _ in docs_with_scores)
    llm = get_llm()
    gaps = llm.invoke(CITATION_GAP_PROMPT.format(context=context, topic=topic))

    all_citations = [
        d.metadata.get("citation_count", 0)
        for d, _ in docs_with_scores
        if isinstance(d.metadata.get("citation_count"), (int, float))
    ]
    avg_citations = sum(all_citations) / len(all_citations) if all_citations else 0

    return {
        "gaps": gaps.strip() if isinstance(gaps, str) else str(gaps),
        "topic": topic,
        "avg_citation_count": round(avg_citations, 1),
        "papers_analyzed": len(docs_with_scores),
        "sources": _extract_sources([d for d, _ in docs_with_scores]),
        "type": "citation_gap",
    }


def answer_research_question(question: str) -> Dict[str, Any]:
    logger.info("Research Q&A: %s", question[:100])
    out = _invoke_rag(RESEARCH_SUMMARY_PROMPT, question)
    return {
        "answer": out["result"],
        "sources": _extract_sources(out["source_documents"]),
        "query": question,
        "type": "research_qa",
    }


def build_knowledge_graph(topic: str) -> Dict[str, Any]:
    logger.info("Building knowledge graph for: %s", topic)
    docs_with_scores = similarity_search_with_score(topic, k=min(settings.top_k_retrieval, 6))
    context = "\n\n---\n\n".join(d.page_content[:600] for d, _ in docs_with_scores)
    llm = get_llm()
    raw = llm.invoke(KNOWLEDGE_GRAPH_PROMPT.format(context=context, topic=topic))
    raw_text = raw if isinstance(raw, str) else str(raw)
    graph = _safe_parse_json(raw_text, fallback=_fallback_graph(topic, docs_with_scores))
    return {
        "graph": graph,
        "topic": topic,
        "papers_used": len(docs_with_scores),
        "type": "knowledge_graph",
    }


def critique_paper(paper_title: str) -> Dict[str, Any]:
    docs = similarity_search_with_score(paper_title, k=5)
    context = "\n\n---\n\n".join(d.page_content for d, _ in docs)
    llm = get_llm()
    critique = llm.invoke(PAPER_CRITIQUE_PROMPT.format(context=context, paper_title=paper_title))
    return {
        "critique": critique.strip() if isinstance(critique, str) else str(critique),
        "paper_title": paper_title,
        "sources": _extract_sources([d for d, _ in docs]),
        "type": "paper_critique",
    }


def cluster_topics(domain: str, n_clusters: int = 5) -> Dict[str, Any]:
    try:
        import numpy as np
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import normalize
    except ImportError:
        return {"error": "scikit-learn required for clustering", "clusters": []}

    docs = get_vector_store().similarity_search(domain, k=30)
    if not docs:
        return {"clusters": [], "domain": domain, "total_papers": 0, "n_clusters": 0, "type": "topic_clusters"}
    if len(docs) < n_clusters:
        n_clusters = max(2, len(docs))

    from app.vector_store import get_embeddings
    embedder = get_embeddings()
    texts     = [d.page_content[:300] for d in docs]
    embeddings = embedder.embed_documents(texts)
    matrix     = normalize(np.array(embeddings))

    km     = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(matrix)

    clusters: Dict[int, List[str]] = {}
    for i, label in enumerate(labels):
        clusters.setdefault(int(label), []).append(
            docs[i].metadata.get("title") or docs[i].page_content[:80]
        )

    return {
        "clusters": [
            {"cluster_id": k, "size": len(v), "sample_papers": v[:3]}
            for k, v in clusters.items()
        ],
        "domain": domain,
        "total_papers": len(docs),
        "n_clusters": n_clusters,
        "type": "topic_clusters",
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _safe_parse_json(raw: str, fallback: dict) -> dict:
    try:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except (json.JSONDecodeError, AttributeError):
        pass
    return fallback


def _fallback_graph(topic: str, docs_with_scores: List[Tuple]) -> dict:
    entities = [{"id": "e0", "label": topic, "type": "concept", "weight": 10}]
    relationships = []
    for i, (doc, score) in enumerate(docs_with_scores[:6]):
        eid   = f"e{i + 1}"
        title = doc.metadata.get("title", f"Paper {i + 1}")[:60]
        entities.append({"id": eid, "label": title, "type": "paper", "weight": max(1, int(score * 10))})
        relationships.append({"source": "e0", "target": eid, "relation": "related_to", "weight": max(1, int(score * 5))})
    return {"entities": entities, "relationships": relationships, "clusters": []}
