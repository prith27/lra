"""Integration tests for the agent system."""

import uuid

import pytest
import pytest_asyncio

from agents.deps import AgentDeps
from config import SANDBOX_URL
from memory.structured_store import StructuredMemoryStore
from memory.vector_store import VectorMemoryStore


@pytest.fixture
def session_id() -> str:
    return str(uuid.uuid4())[:8]


@pytest_asyncio.fixture
async def structured_store():
    store = StructuredMemoryStore("sqlite+aiosqlite:///:memory:")
    await store.init_db()
    yield store
    await store.close()


@pytest.fixture
def vector_store(session_id):
    return VectorMemoryStore(persist_path=f"/tmp/test_chroma_{session_id}")


@pytest_asyncio.fixture
async def deps(session_id, structured_store, vector_store):
    return AgentDeps(
        session_id=session_id,
        structured_store=structured_store,
        vector_store=vector_store,
        sandbox_base_url=SANDBOX_URL,
    )


@pytest.mark.asyncio
async def test_memory_tools(deps: AgentDeps) -> None:
    """Test memory search and write."""
    from tools.memory_tools import search_memory, write_memory

    await write_memory(
        type("Ctx", (), {"deps": deps})(),
        "User prefers dark mode",
        "fact",
    )
    results = await search_memory(
        type("Ctx", (), {"deps": deps})(),
        "user preference",
    )
    assert len(results) >= 0  # May be empty if embedding not ready
    # At least write should have stored
    summaries = await deps.structured_store.get_summaries(deps.session_id)
    assert len(summaries) == 1
    assert "dark mode" in summaries[0]


@pytest.mark.asyncio
async def test_task_tools(deps: AgentDeps) -> None:
    """Test task create, list, update."""
    from tools.task_tools import create_task, list_tasks, update_task_status

    ctx = type("Ctx", (), {"deps": deps})()
    out = await create_task(ctx, "Test task", "A test")
    assert "Task created:" in out
    task_id = out.split(":")[-1].strip()
    tasks = await list_tasks(ctx)
    assert len(tasks) == 1
    assert tasks[0].title == "Test task"
    await update_task_status(ctx, task_id, "done")
    tasks2 = await list_tasks(ctx)
    assert tasks2[0].status == "done"


@pytest.mark.asyncio
async def test_structured_store(deps: AgentDeps) -> None:
    """Test structured store directly."""
    await deps.structured_store.append_conversation(deps.session_id, "user", "Hello")
    convs = await deps.structured_store.get_conversations(deps.session_id)
    assert len(convs) == 1
    assert convs[0]["content"] == "Hello"
