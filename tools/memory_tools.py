"""Memory tools for the agent: search, write, get task state."""

import uuid

from pydantic_ai import RunContext
from schemas.memory import TaskState

from agents.deps import AgentDeps


async def search_memory(ctx: RunContext[AgentDeps], query: str) -> list[str]:
    """Search semantic memory for relevant entries. Use for recalling past summaries or facts."""
    results = ctx.deps.vector_store.search(query, top_k=5)
    return [r["text"] for r in results]


async def write_memory(
    ctx: RunContext[AgentDeps],
    content: str,
    memory_type: str = "fact",
) -> str:
    """Store content in memory (structured + vector). Use for saving important facts or summaries."""
    store = ctx.deps.structured_store
    vector_store = ctx.deps.vector_store
    mem_id = str(uuid.uuid4())
    await store.append_summary(ctx.deps.session_id, content)
    vector_store.add(mem_id, content, {"session_id": ctx.deps.session_id, "type": memory_type})
    return f"Stored in memory (id={mem_id})"


async def get_recent_conversations(
    ctx: RunContext[AgentDeps],
    limit: int = 10,
    all_sessions: bool = False,
) -> list[dict[str, str]]:
    """Get recent conversation turns. Use for 'what was our last conversation?' or recalling prior turns.
    Set all_sessions=True to get recent turns across all sessions (e.g. when current session is empty or user asks about 'last convo' from past runs)."""
    if all_sessions:
        return await ctx.deps.structured_store.get_conversations_all_sessions(limit=limit)
    return await ctx.deps.structured_store.get_conversations(
        ctx.deps.session_id, limit=limit
    )


async def get_task_state(ctx: RunContext[AgentDeps], task_id: str) -> TaskState | None:
    """Get task state by ID. Returns None if not found."""
    task = await ctx.deps.structured_store.get_task(ctx.deps.session_id, task_id)
    if task is None:
        return None
    return TaskState(
        id=task["id"],
        title=task["title"],
        status=task["status"],
        metadata=task["metadata"],
        created_at=task["created_at"],
    )
