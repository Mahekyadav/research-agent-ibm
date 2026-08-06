"""
Tests — ResearchMind Agent
Covers: source fetching, ingestion, intelligence engine, conversation, API.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    monkeypatch.setenv("WATSONX_API_KEY", "test-key")
    monkeypatch.setenv("WATSONX_PROJECT_ID", "test-project")
    monkeypatch.setenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")


@pytest.fixture
def sample_paper():
    return {
        "source": "arxiv",
        "id": "2310.12345",
        "title": "Attention Is All You Need: A Revisit",
        "abstract": "We revisit the transformer architecture and propose improvements to the attention mechanism for large-scale NLP tasks.",
        "authors": ["Alice Smith", "Bob Jones"],
        "published": "2023-10-15",
        "categories": ["cs.LG", "cs.CL"],
        "citation_count": 1250,
        "url": "https://arxiv.org/abs/2310.12345",
        "doi": "",
    }


@pytest.fixture
def sample_papers(sample_paper):
    return [
        sample_paper,
        {
            "source": "semantic_scholar",
            "id": "abc123",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "abstract": "We introduce BERT, a novel language model pre-trained on large corpora using masked language modeling.",
            "authors": ["Jacob Devlin", "Ming-Wei Chang"],
            "year": "2019",
            "citation_count": 50000,
            "url": "https://semanticscholar.org/paper/abc123",
            "doi": "10.1000/example",
        },
    ]


@pytest.fixture
def sample_txt_file(tmp_path):
    f = tmp_path / "research_note.txt"
    f.write_text("This paper explores the use of graph neural networks for molecular property prediction. "
                 "We propose a novel architecture that achieves state-of-the-art results on benchmark datasets.")
    return f


# ══════════════════════════════════════════════════════════════════════════════
# SOURCE AGGREGATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestArxivFetch:
    @patch("app.sources.requests.get")
    def test_fetch_arxiv_success(self, mock_get):
        xml_response = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2310.12345v1</id>
    <title>Test Paper Title</title>
    <summary>This is the abstract of the test paper about deep learning.</summary>
    <published>2023-10-15T00:00:00Z</published>
    <author><name>Alice Smith</name></author>
    <author><name>Bob Jones</name></author>
    <category term="cs.LG"/>
    <link type="application/pdf" href="https://arxiv.org/pdf/2310.12345"/>
  </entry>
</feed>"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = xml_response
        mock_get.return_value.raise_for_status = MagicMock()

        from app.sources import fetch_arxiv_papers
        papers = fetch_arxiv_papers("deep learning", max_results=5)
        assert len(papers) == 1
        assert papers[0]["title"] == "Test Paper Title"
        assert "Alice Smith" in papers[0]["authors"]
        assert papers[0]["source"] == "arxiv"

    @patch("app.sources.requests.get")
    def test_fetch_arxiv_network_error(self, mock_get):
        import requests as req
        mock_get.side_effect = req.RequestException("Network error")
        from app.sources import fetch_arxiv_papers
        result = fetch_arxiv_papers("test query")
        assert result == []


class TestSemanticScholar:
    @patch("app.sources.requests.get")
    def test_fetch_semantic_scholar_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "data": [
                {
                    "paperId": "abc123",
                    "title": "Transformer Architecture Survey",
                    "abstract": "A comprehensive survey of transformer models.",
                    "authors": [{"name": "John Doe"}],
                    "year": 2023,
                    "citationCount": 500,
                    "url": "https://semanticscholar.org/paper/abc123",
                    "externalIds": {"DOI": "10.1000/test"},
                }
            ]
        }
        mock_get.return_value.raise_for_status = MagicMock()

        from app.sources import fetch_semantic_scholar
        papers = fetch_semantic_scholar("transformer survey", limit=5)
        assert len(papers) == 1
        assert papers[0]["citation_count"] == 500
        assert papers[0]["source"] == "semantic_scholar"

    @patch("app.sources.requests.get")
    def test_fetch_semantic_scholar_empty(self, mock_get):
        mock_get.return_value.json.return_value = {"data": []}
        mock_get.return_value.raise_for_status = MagicMock()
        from app.sources import fetch_semantic_scholar
        assert fetch_semantic_scholar("obscure topic") == []


class TestCrossRef:
    @patch("app.sources.requests.get")
    def test_fetch_crossref_success(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "message": {
                "items": [
                    {
                        "title": ["Journal Paper on NLP"],
                        "abstract": "<p>Abstract text here.</p>",
                        "author": [{"given": "Jane", "family": "Doe"}],
                        "published": {"date-parts": [[2022]]},
                        "is-referenced-by-count": 100,
                        "DOI": "10.1000/crossref-test",
                        "URL": "https://doi.org/10.1000/crossref-test",
                        "type": "journal-article",
                    }
                ]
            }
        }
        mock_get.return_value.raise_for_status = MagicMock()

        from app.sources import fetch_crossref
        papers = fetch_crossref("nlp language model", rows=5)
        assert len(papers) == 1
        assert papers[0]["source"] == "crossref"
        assert "Jane Doe" in papers[0]["authors"]
        # HTML should be stripped from abstract
        assert "<p>" not in papers[0]["abstract"]


# ══════════════════════════════════════════════════════════════════════════════
# INGESTION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestIngestion:
    @patch("app.sources.add_documents")
    def test_ingest_papers(self, mock_add, sample_papers, tmp_path, monkeypatch):
        monkeypatch.setenv("PROCESSED_DOCS_DIR", str(tmp_path / "processed"))
        from app.sources import ingest_papers
        result = ingest_papers(sample_papers)
        assert result["ingested"] == 2
        assert result["skipped"] == 0
        assert result["chunks_added"] >= 2
        mock_add.assert_called()

    @patch("app.sources.add_documents")
    def test_ingest_papers_deduplication(self, mock_add, sample_papers, tmp_path, monkeypatch):
        monkeypatch.setenv("PROCESSED_DOCS_DIR", str(tmp_path / "processed2"))
        from app.sources import ingest_papers
        ingest_papers(sample_papers)
        result = ingest_papers(sample_papers, force=False)
        assert result["skipped"] == 2

    @patch("app.sources.add_documents")
    def test_ingest_text(self, mock_add, tmp_path, monkeypatch):
        monkeypatch.setenv("PROCESSED_DOCS_DIR", str(tmp_path / "processed3"))
        from app.sources import ingest_text
        result = ingest_text("Graph neural networks have shown promise in molecular property prediction tasks.", "test_note")
        assert result["status"] == "success"
        assert result["chunks"] >= 1

    @patch("app.sources.add_documents")
    def test_ingest_file_txt(self, mock_add, sample_txt_file, tmp_path, monkeypatch):
        monkeypatch.setenv("PROCESSED_DOCS_DIR", str(tmp_path / "processed4"))
        from app.sources import ingest_file
        result = ingest_file(sample_txt_file)
        assert result["status"] == "success"
        assert result["chunks"] >= 1

    def test_ingest_file_not_found(self):
        from app.sources import ingest_file
        with pytest.raises(FileNotFoundError):
            ingest_file("/nonexistent/path.pdf")

    @patch("app.sources.add_documents")
    def test_papers_to_documents(self, mock_add, sample_paper):
        from app.sources import papers_to_documents
        docs = papers_to_documents([sample_paper])
        assert len(docs) == 1
        assert "Attention Is All You Need" in docs[0].page_content
        assert docs[0].metadata["source_type"] == "arxiv"
        assert docs[0].metadata["citation_count"] == 1250


# ══════════════════════════════════════════════════════════════════════════════
# INTELLIGENCE ENGINE TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestIntelligenceEngine:
    @patch("app.intelligence.get_llm")
    @patch("app.intelligence.get_vector_store")
    def test_literature_review(self, mock_vs, mock_llm):
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = {
            "result": "## Overview\nThis review covers transformer models...",
            "source_documents": [],
        }
        with patch("app.intelligence.RetrievalQA") as mock_qa:
            mock_qa.from_chain_type.return_value = mock_chain
            from app.intelligence import generate_literature_review
            result = generate_literature_review("transformer models for NLP")
            assert "review" in result
            assert "sources" in result
            assert result["type"] == "literature_review"

    @patch("app.intelligence.get_llm")
    @patch("app.intelligence.similarity_search_with_score")
    def test_analyze_trends(self, mock_search, mock_llm):
        from langchain.schema import Document
        mock_search.return_value = [
            (Document(page_content="2023 trend: LLMs are dominating NLP.", metadata={"title": "LLM Survey", "year": "2023", "source_type": "arxiv"}), 0.9),
            (Document(page_content="Emerging: multimodal learning in vision-language models.", metadata={"title": "CLIP Paper", "year": "2022", "source_type": "semantic_scholar"}), 0.8),
        ]
        mock_llm.return_value.invoke.return_value = "## Emerging Trends\n1. Large Language Models\n2. Multimodal Learning"

        from app.intelligence import analyze_trends
        result = analyze_trends("large language models")
        assert "analysis" in result
        assert result["papers_analyzed"] == 2
        assert "2023" in result["year_distribution"]
        assert result["type"] == "trend_analysis"

    @patch("app.intelligence.get_llm")
    @patch("app.intelligence.similarity_search_with_score")
    def test_detect_citation_gaps(self, mock_search, mock_llm):
        from langchain.schema import Document
        mock_search.return_value = [
            (Document(page_content="Few papers address...", metadata={"citation_count": 5, "title": "Rare Topic"}), 0.7),
        ]
        mock_llm.return_value.invoke.return_value = "## Understudied Sub-Topics\n- Low-resource multilingual LLMs"

        from app.intelligence import detect_citation_gaps
        result = detect_citation_gaps("low-resource NLP")
        assert "gaps" in result
        assert result["type"] == "citation_gap"
        assert "avg_citation_count" in result

    @patch("app.intelligence.get_llm")
    @patch("app.intelligence.similarity_search_with_score")
    def test_build_knowledge_graph(self, mock_search, mock_llm):
        from langchain.schema import Document
        mock_search.return_value = [
            (Document(page_content="Transformers use attention mechanisms.", metadata={"title": "Attention Paper"}), 0.95),
        ]
        mock_llm.return_value.invoke.return_value = '{"entities": [{"id": "e1", "label": "transformer", "type": "concept", "weight": 9}], "relationships": [], "clusters": []}'

        from app.intelligence import build_knowledge_graph
        result = build_knowledge_graph("transformer architectures")
        assert "graph" in result
        assert "entities" in result["graph"]
        assert result["type"] == "knowledge_graph"

    @patch("app.intelligence.get_llm")
    @patch("app.intelligence.similarity_search_with_score")
    def test_build_knowledge_graph_invalid_json(self, mock_search, mock_llm):
        """Falls back to metadata-based graph if LLM returns non-JSON."""
        from langchain.schema import Document
        mock_search.return_value = [
            (Document(page_content="Some content.", metadata={"title": "Paper A"}), 0.8),
        ]
        mock_llm.return_value.invoke.return_value = "I cannot generate JSON right now."

        from app.intelligence import build_knowledge_graph
        result = build_knowledge_graph("test topic")
        assert "graph" in result
        assert "entities" in result["graph"]

    @patch("app.intelligence.get_llm")
    @patch("app.intelligence.similarity_search_with_score")
    def test_critique_paper(self, mock_search, mock_llm):
        from langchain.schema import Document
        mock_search.return_value = [
            (Document(page_content="Attention is all you need introduces multi-head attention.", metadata={"title": "Attention Is All You Need"}), 0.99),
        ]
        mock_llm.return_value.invoke.return_value = "## Critical Analysis\n### Strengths\n- Novel architecture"

        from app.intelligence import critique_paper
        result = critique_paper("Attention Is All You Need")
        assert "critique" in result
        assert result["type"] == "paper_critique"


# ══════════════════════════════════════════════════════════════════════════════
# CONVERSATION TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestConversation:
    def test_create_and_get_session(self):
        with patch("app.conversation.get_vector_store"), \
             patch("app.conversation.get_llm"):
            from app.conversation import create_session, get_session
            sid = create_session({"user": "researcher_1"})
            assert len(sid) == 36
            session = get_session(sid)
            assert session is not None
            assert session.session_id == sid

    def test_delete_session(self):
        with patch("app.conversation.get_vector_store"), \
             patch("app.conversation.get_llm"):
            from app.conversation import create_session, delete_session, get_session
            sid = create_session()
            assert delete_session(sid) is True
            assert get_session(sid) is None
            assert delete_session("nonexistent") is False

    def test_list_sessions(self):
        with patch("app.conversation.get_vector_store"), \
             patch("app.conversation.get_llm"):
            from app.conversation import create_session, list_sessions
            create_session()
            sessions = list_sessions()
            assert isinstance(sessions, list)
            assert len(sessions) >= 1
            assert "session_id" in sessions[0]


# ══════════════════════════════════════════════════════════════════════════════
# API ENDPOINT TESTS
# ══════════════════════════════════════════════════════════════════════════════

class TestAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        with patch("app.vector_store.get_embeddings"), \
             patch("app.vector_store.get_vector_store"), \
             patch("app.llm_client.get_llm"):
            from app.api import app
            return TestClient(app)

    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["service"] == "ResearchMind — Intelligent Research Agent"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    @patch("app.api.aggregate_sources")
    @patch("app.api.ingest_papers")
    def test_search_and_ingest(self, mock_ingest, mock_search, client, sample_papers):
        mock_search.return_value = sample_papers
        mock_ingest.return_value = {"ingested": 2, "skipped": 0, "chunks_added": 6}
        resp = client.post("/search", json={
            "query": "transformer models",
            "sources": ["arxiv", "semantic_scholar"],
            "ingest_immediately": True,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["papers_found"] == 2
        assert "ingestion" in data

    @patch("app.api.generate_literature_review")
    def test_literature_review(self, mock_review, client):
        mock_review.return_value = {
            "review": "## Overview\nTransformer models dominate NLP...",
            "sources": [],
            "query": "transformers",
            "type": "literature_review",
        }
        resp = client.post("/research/literature-review", json={"query": "transformers"})
        assert resp.status_code == 200
        assert "review" in resp.json()

    @patch("app.api.analyze_trends")
    def test_trends(self, mock_trends, client):
        mock_trends.return_value = {
            "analysis": "## Emerging Trends\n1. LLMs",
            "domain": "NLP",
            "type": "trend_analysis",
        }
        resp = client.post("/research/trends", json={"domain": "NLP"})
        assert resp.status_code == 200
        assert "analysis" in resp.json()

    @patch("app.api.detect_citation_gaps")
    def test_citation_gaps(self, mock_gaps, client):
        mock_gaps.return_value = {
            "gaps": "## Understudied Areas\n- Low resource",
            "topic": "multilingual NLP",
            "type": "citation_gap",
        }
        resp = client.post("/research/citation-gaps", json={"topic": "multilingual NLP"})
        assert resp.status_code == 200
        assert "gaps" in resp.json()

    @patch("app.api.answer_research_question")
    def test_ask_question(self, mock_ask, client):
        mock_ask.return_value = {
            "answer": "BERT uses masked language modeling...",
            "sources": [],
            "query": "What is BERT?",
            "type": "research_qa",
        }
        resp = client.post("/research/ask", json={"question": "What is BERT?"})
        assert resp.status_code == 200
        assert "answer" in resp.json()

    @patch("app.api.build_knowledge_graph")
    def test_knowledge_graph(self, mock_kg, client):
        mock_kg.return_value = {
            "graph": {"entities": [], "relationships": [], "clusters": []},
            "topic": "transformers",
            "type": "knowledge_graph",
        }
        resp = client.post("/research/knowledge-graph", json={"topic": "transformers"})
        assert resp.status_code == 200
        assert "graph" in resp.json()

    @patch("app.api.critique_paper")
    def test_critique(self, mock_critique, client):
        mock_critique.return_value = {
            "critique": "## Strengths\n- Novel attention mechanism",
            "paper_title": "Attention Is All You Need",
            "type": "paper_critique",
        }
        resp = client.post("/research/critique", json={"paper_title": "Attention Is All You Need"})
        assert resp.status_code == 200
        assert "critique" in resp.json()

    @patch("app.api.create_session", return_value="test-session-abc")
    def test_new_session(self, mock_create, client):
        resp = client.post("/chat/session/new")
        assert resp.status_code == 200
        assert "session_id" in resp.json()
