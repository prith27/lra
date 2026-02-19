"""Hybrid retrieval: combine vector (semantic) and keyword search."""

import re
from typing import Any

from memory.vector_store import VectorMemoryStore


def _tokenize(text: str) -> set[str]:
    """Simple tokenization for keyword matching."""
    text_lower = text.lower()
    tokens = re.findall(r"\b\w+\b", text_lower)
    return set(tokens)


def _keyword_score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    """Jaccard-like keyword overlap score."""
    if not query_tokens:
        return 0.0
    overlap = len(query_tokens & doc_tokens) / len(query_tokens)
    return overlap


class HybridRetriever:
    """Combine vector search with keyword matching for better accuracy."""

    def __init__(self, vector_store: VectorMemoryStore) -> None:
        self._vector_store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ) -> list[dict[str, Any]]:
        """
        Hybrid search: fetch more from vector store, then re-rank by
        combined vector + keyword score.
        """
        # Get more candidates from vector search
        candidates = self._vector_store.search(query, top_k=top_k * 2)
        if not candidates:
            return []

        query_tokens = _tokenize(query)

        def score(item: dict[str, Any]) -> float:
            text = item.get("text", "")
            doc_tokens = _tokenize(text)
            kw_score = _keyword_score(query_tokens, doc_tokens)
            # Vector distance: lower is better (cosine). Normalize to 0-1.
            dist = item.get("distance", 1.0)
            vec_score = max(0, 1 - dist) if dist else 1.0
            return vector_weight * vec_score + keyword_weight * kw_score

        scored = [(score(c), c) for c in candidates]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:top_k]]
