"""Example: Single-turn query using the long-running-agents library.

Ask one question, get a response, then exit. Useful for scripts or automation.
"""

import asyncio
import sys

from long_running_agents import run_agent, AgentDeps, StructuredMemoryStore, VectorMemoryStore
from config import OPENAI_API_KEY, SANDBOX_URL


async def main() -> None:
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        print("  export OPENAI_API_KEY=sk-your-key-here", file=sys.stderr)
        sys.exit(1)

    structured = StructuredMemoryStore()
    vector = VectorMemoryStore()
    await structured.init_db()

    deps = AgentDeps(
        session_id="single-turn",
        structured_store=structured,
        vector_store=vector,
        sandbox_base_url=SANDBOX_URL,
    )

    # Single question (or use sys.argv for CLI args)
    question = "What tools do you have access to? List them briefly."
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    output, _ = await run_agent(question, deps)
    print(output)
    await structured.close()


if __name__ == "__main__":
    asyncio.run(main())
