"""Example: Chat loop using the long-running-agents library.

Run multiple turns; memory persists across runs. Uses the same agent as `lra chat`.
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

    session_id = "example-session"
    structured = StructuredMemoryStore()
    vector = VectorMemoryStore()
    await structured.init_db()

    deps = AgentDeps(
        session_id=session_id,
        structured_store=structured,
        vector_store=vector,
        sandbox_base_url=SANDBOX_URL,
    )

    print("Chat with the agent. Type 'q' to quit.\n")
    message_history: list = []

    while True:
        try:
            prompt = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if prompt.lower() == "q":
            print("Goodbye!")
            break

        if not prompt:
            continue

        output, message_history = await run_agent(
            prompt, deps, message_history=message_history or None
        )
        print(f"Agent: {output}\n")

    await structured.close()


if __name__ == "__main__":
    asyncio.run(main())
