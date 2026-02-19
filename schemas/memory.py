"""Memory API request and response models."""

from typing import Any

from pydantic import BaseModel, Field


class MemorySearchResult(BaseModel):
    """Single result from semantic memory search."""

    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    distance: float = 0.0


class MemoryWriteRequest(BaseModel):
    """Request to write to memory."""

    content: str = Field(..., description="Content to store")
    memory_type: str = Field(default="fact", description="Type: fact, summary, etc.")


class TaskState(BaseModel):
    """Task state and metadata."""

    id: str
    title: str
    status: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = ""
