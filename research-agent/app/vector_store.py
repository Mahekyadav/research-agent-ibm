"""
Vector Store — ChromaDB backed by IBM WatsonX Slate Embeddings.

langchain-chroma>=0.2 / chromadb>=1.0:
  - chromadb.PersistentClient(path=...) is the correct way to get a persistent client.
  - Pass client= to langchain_chroma.Chroma (no persist_directory kwarg needed).
"""
from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional, Tuple

import chromadb
from langchain_chroma import Chroma
from langchain_ibm import WatsonxEmbeddings
from langchain_core.documents import Document
from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames as EmbedParams

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_embeddings() -> WatsonxEmbeddings:
    """Singleton IBM WatsonX Slate embeddings model."""
    logger.info("Initializing WatsonX Embeddings: %s", settings.embedding_model_id)
    return WatsonxEmbeddings(
        model_id=settings.embedding_model_id,
        url=settings.watsonx_url,
        apikey=settings.watsonx_api_key,
        project_id=settings.watsonx_project_id,
        params={
            EmbedParams.TRUNCATE_INPUT_TOKENS: 512,
            EmbedParams.RETURN_OPTIONS: {"input_text": False},
        },
    )


@lru_cache(maxsize=1)
def _get_chroma_client() -> chromadb.PersistentClient:
    """Persistent ChromaDB client (chromadb>=1.0 API)."""
    return chromadb.PersistentClient(path=settings.vector_store_path)


@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    """Singleton LangChain Chroma wrapper backed by the persistent client."""
    logger.info(
        "Loading ChromaDB '%s' from %s",
        settings.chroma_collection_name,
        settings.vector_store_path,
    )
    return Chroma(
        client=_get_chroma_client(),
        collection_name=settings.chroma_collection_name,
        embedding_function=get_embeddings(),
    )


def add_documents(docs: List[Document]) -> None:
    """Index a list of documents into the vector store."""
    vs = get_vector_store()
    vs.add_documents(docs)
    logger.debug("Indexed %d document chunks.", len(docs))


def similarity_search(
    query: str,
    k: int = None,
    filter_meta: Optional[dict] = None,
) -> List[Document]:
    k = k or settings.top_k_retrieval
    return get_vector_store().similarity_search(query, k=k, filter=filter_meta)


def similarity_search_with_score(
    query: str,
    k: int = None,
) -> List[Tuple[Document, float]]:
    k = k or settings.top_k_retrieval
    return get_vector_store().similarity_search_with_relevance_scores(query, k=k)


def reset_collection() -> None:
    vs = get_vector_store()
    vs.delete_collection()
    get_vector_store.cache_clear()
    _get_chroma_client.cache_clear()
    logger.warning("Research vector store cleared.")
