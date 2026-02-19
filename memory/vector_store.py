"""Vector (semantic) memory store using ChromaDB."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from config import VECTOR_STORE_PATH


class VectorMemoryStore:
    """Semantic memory store using ChromaDB with embeddings."""

    def __init__(self, persist_path: str | None = None) -> None:
        path = Path(persist_path or VECTOR_STORE_PATH)
        path.mkdir(parents=True, exist_ok=True)
        # Use sentence-transformers for embeddings (runs locally)
        self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self._client = chromadb.PersistentClient(
            path=str(path),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="agent_memory",
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add(
        self,
        id: str,
        text: str,
        metadata: dict[str, str | int | float] | None = None,
    ) -> None:
        """Add or upsert a text entry with embedding."""
        meta = metadata or {}
        self._collection.upsert(
            ids=[id],
            documents=[text],
            metadatas=[meta],
        )

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Search for semantically similar entries."""
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        if not results["ids"] or not results["ids"][0]:
            return []
        documents = results["documents"][0] or []
        metadatas = results["metadatas"][0] or []
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(documents)
        return [
            {
                "text": doc,
                "metadata": meta or {},
                "distance": dist,
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

    def delete(self, id: str) -> None:
        """Delete an entry by ID."""
        self._collection.delete(ids=[id])
