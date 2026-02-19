"""Periodic summarization of conversations into structured and vector memory."""

from typing import Any

from memory.structured_store import StructuredMemoryStore
from memory.vector_store import VectorMemoryStore


async def summarize_conversation(
    session_id: str,
    conversations: list[dict[str, Any]],
    structured_store: StructuredMemoryStore,
    vector_store: VectorMemoryStore,
    summary_text: str,
) -> None:
    """
    Store a summary of the conversation in both structured and vector memory.
    Call this after N turns or at session end.
    """
    await structured_store.append_summary(session_id, summary_text)
    vector_store.add(
        id=f"summary_{session_id}_{len(conversations)}",
        text=summary_text,
        metadata={"session_id": session_id, "type": "summary"},
    )
