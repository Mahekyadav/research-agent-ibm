# 🔬 ResearchMind — IBM WatsonX Intelligent Research Agent

> **Agentic AI Research Companion — Problem Statement #7**
> IBM WatsonX Hackathon Solution

## Overview

ResearchMind is a production-grade **agentic AI research companion** that aggregates papers from arXiv, Semantic Scholar, and CrossRef; indexes them in a persistent vector knowledge base; and provides literature synthesis, trend prediction, citation gap detection, knowledge graph construction, and multi-turn conversational Q&A — all powered by **IBM WatsonX Granite LLM** and **IBM Slate Embeddings**.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     ResearchMind — Research Agent                         │
├─────────────────────┬────────────────────────────────────────────────────┤
│  SOURCE FUSION      │  arXiv API + Semantic Scholar API + CrossRef API   │
│                     │  PDF / DOCX upload + Web URLs + Raw text notes     │
│                     │  → Deduplication by title hash                     │
│                     │  → Ingestion Registry (JSON)                       │
├─────────────────────┼────────────────────────────────────────────────────┤
│  EMBEDDING LAYER    │  IBM WatsonX Slate-125M (slate-125m-english-rtrvr) │
│                     │  → RecursiveCharacterTextSplitter (1000/200)        │
│                     │  → ChromaDB persistent vector store                │
├─────────────────────┼────────────────────────────────────────────────────┤
│  LLM LAYER          │  IBM WatsonX Granite-13B-Instruct-v2               │
│                     │  → Greedy decoding, T=0.5, max_tokens=2000         │
├─────────────────────┼────────────────────────────────────────────────────┤
│  INTELLIGENCE       │  Literature Review (RetrievalQA + Granite)         │
│                     │  Trend Analysis (corpus-level LLM synthesis)       │
│                     │  Citation Gap Detection (coverage analysis)        │
│                     │  Knowledge Graph Extraction (JSON graph)           │
│                     │  Topic Clustering (KMeans on embedding space)      │
│                     │  Paper Critique (critical analysis chain)          │
├─────────────────────┼────────────────────────────────────────────────────┤
│  CONVERSATION       │  ConversationalRetrievalChain (session memory k=12)│
│                     │  Multi-turn context with question condensation     │
├─────────────────────┼────────────────────────────────────────────────────┤
│  API LAYER          │  FastAPI REST — 20 endpoints + Swagger docs        │
├─────────────────────┼────────────────────────────────────────────────────┤
│  VISUAL FLOW        │  IBM Langflow — 15-node pipeline JSON              │
│                     │  Import at localhost:7860                          │
└─────────────────────┴────────────────────────────────────────────────────┘
```

---

## IBM Models Used

| Role | Model | Provider |
|------|-------|----------|
| LLM (Research Synthesis) | `ibm/granite-13b-instruct-v2` | IBM WatsonX |
| Embeddings (Retrieval) | `ibm/slate-125m-english-rtrvr` | IBM WatsonX |

---

## Quick Start

### 1. Configure Credentials

```bash
cp .env.example .env
# Edit .env: set WATSONX_API_KEY, WATSONX_PROJECT_ID
```

### 2. Install & Run

```bash
pip install -r requirements.txt
python main.py
# → http://localhost:8000/docs
```

### 3. Docker Compose (Full Stack)

```bash
docker-compose up -d
# API: localhost:8000 | Langflow: localhost:7860 | ChromaDB: localhost:8001
```

---

## API Usage Examples

### Search & Ingest Papers

```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "large language models for code generation",
    "sources": ["arxiv", "semantic_scholar", "crossref"],
    "max_per_source": 10,
    "ingest_immediately": true
  }'
```

### Generate Literature Review

```bash
curl -X POST "http://localhost:8000/research/literature-review" \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer models for protein folding"}'
```

### Analyze Emerging Trends

```bash
curl -X POST "http://localhost:8000/research/trends" \
  -H "Content-Type: application/json" \
  -d '{"domain": "federated learning in healthcare"}'
```

### Detect Citation Gaps

```bash
curl -X POST "http://localhost:8000/research/citation-gaps" \
  -H "Content-Type: application/json" \
  -d '{"topic": "explainability in deep reinforcement learning"}'
```

### Build Knowledge Graph

```bash
curl -X POST "http://localhost:8000/research/knowledge-graph" \
  -H "Content-Type: application/json" \
  -d '{"topic": "graph neural networks for drug discovery"}'
```

### Multi-Turn Research Chat

```bash
# Create session
curl -X POST "http://localhost:8000/chat/session/new"
# → {"session_id": "abc-123"}

# Ask question
curl -X POST "http://localhost:8000/chat" \
  -d '{"message": "What are the main approaches to continual learning?", "session_id": "abc-123"}'

# Follow-up in context
curl -X POST "http://localhost:8000/chat" \
  -d '{"message": "Which of those works best with limited data?", "session_id": "abc-123"}'
```

### Upload a PDF Paper

```bash
curl -X POST "http://localhost:8000/ingest/file" \
  -F "file=@my_research_paper.pdf"
```

---

## Langflow Integration

1. `docker-compose up langflow -d`
2. Open `http://localhost:7860`
3. Import `langflow/research_agent_flow.json`
4. Set WatsonX credentials in IBM Granite + Slate node inputs
5. Visual pipeline: 4 Source Loaders → Splitter → Chroma → Retriever → Granite → Intelligence Chains

---

## Project Structure

```
research-agent/
├── app/
│   ├── __init__.py
│   ├── config.py           # Pydantic settings — WatsonX + API keys + RAG params
│   ├── llm_client.py       # IBM WatsonX Granite LLM singleton
│   ├── vector_store.py     # ChromaDB + IBM Slate embeddings
│   ├── sources.py          # arXiv + Semantic Scholar + CrossRef aggregation + ingestion
│   ├── intelligence.py     # Literature review, trends, gaps, KG, clustering, critique
│   ├── conversation.py     # Multi-turn session management
│   └── api.py              # FastAPI REST endpoints (20 routes)
├── langflow/
│   └── research_agent_flow.json  # IBM Langflow pipeline (15 nodes)
├── data/
│   ├── documents/          # Uploaded papers
│   ├── vector_store/       # ChromaDB persistent index
│   └── processed/          # Ingestion registry
├── tests/
│   └── test_research_agent.py   # 40+ unit tests
├── main.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Feature → Requirement Mapping

| Requirement | Implementation |
|-------------|---------------|
| Fuse Academic Sources | arXiv + Semantic Scholar + CrossRef APIs + file/URL/text upload |
| Multimodal Research Input | PDF, DOCX, TXT, HTML, URLs, raw text, structured notes |
| Predictive & Agentic Layer | Trend analysis, citation gap detection, future direction prediction |
| Visualize Research Insights | Knowledge graphs, topic clusters, literature reviews with citations |
| IBM Langflow | 15-node visual pipeline JSON, importable into Langflow UI |
| IBM Models | Granite-13B for generation, Slate-125M for embeddings |
