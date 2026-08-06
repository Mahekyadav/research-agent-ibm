"""
IBM WatsonX LLM Client — Research Agent
Granite LLM for synthesis, summarisation, and predictive analysis.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from langchain_ibm import WatsonxLLM
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_llm() -> WatsonxLLM:
    """
    Singleton IBM WatsonX Granite LLM.
    Tuned for research synthesis: lower temperature, more tokens.
    """
    logger.info("Initializing WatsonX LLM: %s", settings.llm_model_id)
    return WatsonxLLM(
        model_id=settings.llm_model_id,
        url=settings.watsonx_url,
        apikey=settings.watsonx_api_key,
        project_id=settings.watsonx_project_id,
        params={
            GenParams.DECODING_METHOD: "greedy",
            GenParams.MAX_NEW_TOKENS: settings.max_new_tokens,
            GenParams.MIN_NEW_TOKENS: 80,
            GenParams.TEMPERATURE: settings.temperature,
            GenParams.TOP_K: 40,
            GenParams.TOP_P: 0.85,
            GenParams.REPETITION_PENALTY: 1.15,
            GenParams.STOP_SEQUENCES: ["Human:", "User:", "\n\n---END---"],
        },
    )
