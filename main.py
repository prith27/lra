"""Entry point to run the agent."""

import asyncio
import uuid

from agents.deps import AgentDeps
from agents.main_agent import run_agent
from config import SANDBOX_URL
from memory.structured_store import StructuredMemoryStore
from memory.vector_store import VectorMemoryStore


async def main() -> None:
    """Run the agent with a sample prompt."""
    session_id = str(uuid.uuid4())[:8]
    structured = StructuredMemoryStore()
    vector = VectorMemoryStore()
    await structured.init_db()

    deps = AgentDeps(
        session_id=session_id,
        structured_store=structured,
        vector_store=vector,
        sandbox_base_url=SANDBOX_URL,
    )

    prompt = input("You: ").strip() or "Hello! What can you do?"
    output = await run_agent(prompt, deps)
    print(f"Agent: {output}")

    await structured.close()


if __name__ == "__main__":
    asyncio.run(main())
