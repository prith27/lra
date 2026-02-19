"""Agent dependencies - shared context passed to tools."""

from dataclasses import dataclass, field
from typing import Any

from memory.structured_store import StructuredMemoryStore
from memory.vector_store import VectorMemoryStore


@dataclass
class AgentDeps:
    """Runtime dependencies for the main agent."""

    session_id: str
    structured_store: StructuredMemoryStore
    vector_store: VectorMemoryStore
    sandbox_id: str | None = None
    sandbox_base_url: str = "http://localhost:8000"
    # Mutable holder so create_sandbox can update sandbox_id for execute_code
    _sandbox_id_ref: dict[str, str | None] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        if not self._sandbox_id_ref:
            self._sandbox_id_ref = {"id": self.sandbox_id}

    def get_sandbox_id(self) -> str | None:
        """Get current sandbox ID (from ref or direct)."""
        return self._sandbox_id_ref.get("id") or self.sandbox_id

    def set_sandbox_id(self, sid: str) -> None:
        """Set sandbox ID for this session."""
        self._sandbox_id_ref["id"] = sid
