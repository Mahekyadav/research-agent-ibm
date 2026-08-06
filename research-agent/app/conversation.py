"""
Multi-turn Conversation Manager — LangChain 1.x LCEL implementation.
langchain.memory and langchain.chains no longer exist in LangChain 1.x.
We implement session memory manually using ChatMessageHistory + LCEL.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

from app.config import settings
from app.vector_store import get_vector_store
from app.llm_client import get_llm

logger = logging.getLogger(__name__)

_sessions: Dict[str, "ResearchSession"] = {}

# ── In-memory message store (keyed by session_id) ────────────────────────────
_history_store: Dict[str, ChatMessageHistory] = {}


def _get_history(session_id: str) -> ChatMessageHistory:
    if session_id not in _history_store:
        _history_store[session_id] = ChatMessageHistory()
    return _history_store[session_id]


class ResearchSession:
    def __init__(self, session_id: str, meta: Optional[Dict] = None):
        self.session_id    = session_id
        self.created_at    = datetime.utcnow()
        self.last_active   = datetime.utcnow()
        self.meta          = meta or {}
        self.message_count = 0
        self.research_topics: List[str] = []

        # Ensure history exists
        _get_history(session_id)

    def chat(self, message: str) -> Dict[str, Any]:
        self.last_active = datetime.utcnow()
        self.message_count += 1
        self.research_topics.append(message[:60])

        # 1. Retrieve relevant docs
        retriever = get_vector_store().as_retriever(
            search_kwargs={"k": settings.top_k_retrieval}
        )
        docs = retriever.invoke(message)
        context = "\n\n---\n\n".join(
            f"[{d.metadata.get('title', 'Paper')}]\n{d.page_content}"
            for d in docs
        )

        # 2. Build conversation history string
        history = _get_history(self.session_id)
        history_text = ""
        for msg in history.messages[-10:]:  # last 10 turns
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            history_text += f"{role}: {msg.content}\n"

        # 3. Build prompt
        prompt = (
            "You are ResearchMind — an expert academic AI assistant powered by IBM WatsonX Granite.\n"
            "Use the retrieved research context and conversation history to answer precisely.\n\n"
            f"RESEARCH CONTEXT:\n{context}\n\n"
            f"CONVERSATION HISTORY:\n{history_text}\n"
            f"User: {message}\n\n"
            "Provide a scholarly answer with evidence from the retrieved papers.\n\n"
            "Assistant:"
        )

        # 4. Call LLM
        llm    = get_llm()
        answer = llm.invoke(prompt)
        answer = answer.strip() if isinstance(answer, str) else str(answer)

        # 5. Save to history
        history.add_user_message(message)
        history.add_ai_message(answer)

        # 6. Build sources
        seen: set = set()
        sources   = []
        for d in docs:
            key = d.metadata.get("source", "")
            if key not in seen:
                seen.add(key)
                sources.append({
                    "source": key,
                    "title":          d.metadata.get("title", ""),
                    "authors":        d.metadata.get("authors", ""),
                    "year":           d.metadata.get("year", ""),
                    "citation_count": d.metadata.get("citation_count", 0),
                })

        return {
            "session_id":    self.session_id,
            "answer":        answer,
            "sources":       sources,
            "message_count": self.message_count,
        }

    def get_history(self) -> List[Dict[str, str]]:
        msgs = _get_history(self.session_id).messages
        return [
            {
                "role":    "user"      if isinstance(m, HumanMessage) else "assistant",
                "content": m.content,
            }
            for m in msgs
        ]

    def clear(self):
        _get_history(self.session_id).clear()
        self.message_count = 0


# ── Session Management ────────────────────────────────────────────────────────

def create_session(meta: Optional[Dict] = None) -> str:
    sid = str(uuid.uuid4())
    _sessions[sid] = ResearchSession(sid, meta)
    _cleanup()
    return sid


def get_session(sid: str) -> Optional[ResearchSession]:
    return _sessions.get(sid)


def get_or_create(sid: Optional[str], meta: Optional[Dict] = None) -> ResearchSession:
    if sid and sid in _sessions:
        return _sessions[sid]
    new_id = create_session(meta)
    return _sessions[new_id]


def delete_session(sid: str) -> bool:
    if sid in _sessions:
        del _sessions[sid]
        _history_store.pop(sid, None)
        return True
    return False


def list_sessions() -> List[Dict[str, Any]]:
    return [
        {
            "session_id":    s.session_id,
            "created_at":    s.created_at.isoformat(),
            "last_active":   s.last_active.isoformat(),
            "message_count": s.message_count,
            "topics":        s.research_topics[-5:],
        }
        for s in _sessions.values()
    ]


def _cleanup(ttl_hours: int = 24):
    cutoff = datetime.utcnow() - timedelta(hours=ttl_hours)
    stale  = [sid for sid, s in _sessions.items() if s.last_active < cutoff]
    for sid in stale:
        del _sessions[sid]
        _history_store.pop(sid, None)
