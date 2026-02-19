"""Task tools: create, update, list tasks."""

import uuid

from pydantic_ai import RunContext
from schemas.memory import TaskState

from agents.deps import AgentDeps


async def create_task(
    ctx: RunContext[AgentDeps],
    title: str,
    description: str = "",
) -> str:
    """Create a new task. Returns the task ID."""
    task_id = str(uuid.uuid4())[:8]
    await ctx.deps.structured_store.upsert_task(
        session_id=ctx.deps.session_id,
        task_id=task_id,
        title=title,
        status="pending",
        metadata={"description": description},
    )
    return f"Task created: {task_id}"


async def update_task_status(
    ctx: RunContext[AgentDeps],
    task_id: str,
    status: str,
) -> str:
    """Update a task's status (pending, in_progress, done)."""
    task = await ctx.deps.structured_store.get_task(ctx.deps.session_id, task_id)
    if task is None:
        return f"Task {task_id} not found"
    await ctx.deps.structured_store.upsert_task(
        session_id=ctx.deps.session_id,
        task_id=task_id,
        title=task["title"],
        status=status,
        metadata=task["metadata"],
    )
    return f"Task {task_id} updated to {status}"


async def list_tasks(ctx: RunContext[AgentDeps]) -> list[TaskState]:
    """List all tasks for the current session."""
    tasks = await ctx.deps.structured_store.get_tasks(ctx.deps.session_id)
    return [
        TaskState(
            id=t["id"],
            title=t["title"],
            status=t["status"],
            metadata=t["metadata"],
            created_at=t["created_at"],
        )
        for t in tasks
    ]
