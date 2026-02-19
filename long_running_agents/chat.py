"""Chat loop for the agent."""

import asyncio
import sys
import uuid

from agents.deps import AgentDeps
from agents.main_agent import run_agent
from config import OPENAI_API_KEY, SANDBOX_URL
from memory.structured_store import StructuredMemoryStore
from memory.vector_store import VectorMemoryStore


def _check_config() -> None:
    """Validate required config. Exit with clear message if missing."""
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        print("Error: OPENAI_API_KEY is not set.", file=sys.stderr)
        print("", file=sys.stderr)
        print("Set it via:", file=sys.stderr)
        print("  export OPENAI_API_KEY=sk-your-key-here", file=sys.stderr)
        print("", file=sys.stderr)
        print("Or run 'lra init' to create .env, then add your key.", file=sys.stderr)
        print("Get a key at https://platform.openai.com/api-keys", file=sys.stderr)
        sys.exit(1)


async def _persist_turn(
    session_id: str,
    prompt: str,
    output: str,
    structured: StructuredMemoryStore,
    vector: VectorMemoryStore,
) -> None:
    """Persist a conversation turn to structured and vector stores."""
    await structured.append_conversation(session_id, "user", prompt)
    await structured.append_conversation(session_id, "assistant", output)
    turn_id = str(uuid.uuid4())
    turn_text = f"User: {prompt}\nAssistant: {output}"
    vector.add(turn_id, turn_text, {"session_id": session_id, "type": "conversation"})


async def run_chat_loop() -> None:
    """Run the agent in a chat loop until user types 'q' to quit or Ctrl+C."""
    _check_config()

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

    print("Agent ready. Type your message and press Enter. Type 'q' to quit.\n")

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

        try:
            output, message_history = await run_agent(
                prompt, deps, message_history=message_history or None
            )
            print(f"Agent: {output}\n")
            await _persist_turn(session_id, prompt, output, structured, vector)
        except KeyboardInterrupt:
            print("\nInterrupted.")
            break

    await structured.close()
