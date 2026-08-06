"""
Configuration — Research Agent
IBM WatsonX + multi-source academic aggregation settings.
"""
from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── IBM WatsonX ──────────────────────────────────────────────────────────
    watsonx_api_key: str = Field(default="", validation_alias="WATSONX_API_KEY")
    watsonx_project_id: str = Field(default="", validation_alias="WATSONX_PROJECT_ID")
    watsonx_url: str = Field(
        default="https://us-south.ml.cloud.ibm.com",
        validation_alias="WATSONX_URL",
    )

    # ── IBM Models ───────────────────────────────────────────────────────────
    llm_model_id: str = Field(
        default="ibm/granite-13b-instruct-v2",
        validation_alias="LLM_MODEL_ID",
    )
    embedding_model_id: str = Field(
        default="ibm/slate-125m-english-rtrvr",
        validation_alias="EMBEDDING_MODEL_ID",
    )

    # ── External APIs ────────────────────────────────────────────────────────
    semantic_scholar_api_key: str = Field(
        default="", validation_alias="SEMANTIC_SCHOLAR_API_KEY"
    )
    arxiv_base_url: str = Field(
        default="http://export.arxiv.org/api/query",
        validation_alias="ARXIV_BASE_URL",
    )
    crossref_base_url: str = Field(
        default="https://api.crossref.org/works",
        validation_alias="CROSSREF_BASE_URL",
    )
    core_api_key: str = Field(default="", validation_alias="CORE_API_KEY")

    # ── Vector Store ─────────────────────────────────────────────────────────
    vector_store_path: str = Field(
        default="./data/vector_store",
        validation_alias="VECTOR_STORE_PATH",
    )
    chroma_collection_name: str = Field(
        default="research_knowledge_base",
        validation_alias="CHROMA_COLLECTION_NAME",
    )

    # ── Document Storage ─────────────────────────────────────────────────────
    docs_upload_dir: str = Field(
        default="./data/documents",
        validation_alias="DOCS_UPLOAD_DIR",
    )
    processed_docs_dir: str = Field(
        default="./data/processed",
        validation_alias="PROCESSED_DOCS_DIR",
    )

    # ── API ──────────────────────────────────────────────────────────────────
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")

    # ── RAG ──────────────────────────────────────────────────────────────────
    chunk_size: int = Field(default=1000, validation_alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, validation_alias="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=8, validation_alias="TOP_K_RETRIEVAL")
    temperature: float = Field(default=0.5, validation_alias="TEMPERATURE")
    max_new_tokens: int = Field(default=2000, validation_alias="MAX_NEW_TOKENS")

    # ── Langflow ─────────────────────────────────────────────────────────────
    langflow_host: str = Field(
        default="http://localhost:7860",
        validation_alias="LANGFLOW_HOST",
    )

    def ensure_dirs(self) -> None:
        for d in [
            self.vector_store_path,
            self.docs_upload_dir,
            self.processed_docs_dir,
        ]:
            Path(d).mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
