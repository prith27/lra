"""Entry point to run the agent (when executed directly)."""

import asyncio

from long_running_agents.chat import run_chat_loop

if __name__ == "__main__":
    try:
        asyncio.run(run_chat_loop())
    except KeyboardInterrupt:
        pass
