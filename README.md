# Long Running Agents

> A Pydantic AI agent that remembers across sessions, can create its own tools, and delegates to specialists. Memory, sandbox, and tasks in one stack.

[Source](https://github.com/prith27/lra)

## Why this exists

**Problem:** Most agents forget between runs. They can't recall past conversations, and they can't extend their own tool set.

**Solution:** Long Running Agents gives you persistent memory (SQLite + ChromaDB), cross-session recall, and dynamic tool generation—so your agent remembers, learns, and adapts over time.

**Audience:** Developers building long-lived, memory-aware agents with Pydantic AI.

## What makes it different

| Feature | What it does | Why it stands out |
|---------|--------------|-------------------|
| **Cross-session memory** | `get_recent_conversations(all_sessions=True)` + `search_memory` | Most agents forget between runs. This one recalls past turns across sessions. |
| **Dynamic tool generation** | Agent creates new tools at runtime via `generate_tool` | Extends its own tool set with AST validation and persistence. |
| **Subagent delegation** | Code and research specialists | Routes work to focused subagents instead of one monolithic agent. |
| **Hybrid retrieval** | Vector + keyword module | Optional hybrid search (semantic + keyword) available in the memory layer. |
| **Pydantic AI** | Typed agent framework | Uses Pydantic AI instead of LangChain/LlamaIndex. |
| **Sandbox + memory + tasks** | All in one stack | Memory, code execution, and task tracking in a single package. |

## What it is (and isn't)

- **Is:** A chat-driven AI agent with persistent memory, code execution, and task tracking. You interact via a terminal loop; the agent responds using its tools; context is saved across runs.
- **Isn't:** A workflow automation engine. No schedules, triggers, or DAGs. It's an interactive assistant, not Zapier or Airflow.

## Install

**Prerequisites:** Python 3.10+, [OpenAI API key](https://platform.openai.com/api-keys)

```bash
# From PyPI
pip install long-running-agents

# From GitHub
pip install git+https://github.com/prith27/lra.git

# From source (clone first)
git clone https://github.com/prith27/lra.git
cd lra
pip install -e .
```

## Quick start

```bash
export OPENAI_API_KEY=sk-your-key-here   # or use lra init to create .env
lra chat
```

Or run `lra init` first to create a `.env` file and see setup instructions.

**Note:** Basic chat and memory work without the sandbox. The sandbox is only needed for code execution (see [Sandbox](#sandbox-optional) below).

## How it works

1. Run `lra chat` to start the chat loop.
2. Type a message; the agent may call tools (search memory, run code, create tasks, delegate to subagents).
3. Each turn is persisted to SQLite and ChromaDB so the agent can recall past context in future runs.
4. Each run gets a new session ID, but `get_recent_conversations(all_sessions=True)` and `search_memory` allow cross-session recall.

## Agent tools

| Tool | Purpose |
|------|---------|
| `search_memory` | Semantic search over past summaries and facts (ChromaDB) |
| `write_memory` | Store facts or summaries for later recall |
| `get_recent_conversations` | Fetch recent turns (session or all sessions) |
| `create_task`, `update_task_status`, `list_tasks` | Track multi-step work |
| `create_sandbox`, `execute_code` | Run Python in isolated containers |
| `delegate_code_task`, `delegate_research_task` | Hand off to specialist subagents |
| `generate_tool` | Create new tools at runtime when no existing tool fits |

## Library usage

```python
import asyncio
from long_running_agents import run_agent, AgentDeps, StructuredMemoryStore, VectorMemoryStore
from config import SANDBOX_URL

async def main():
    structured = StructuredMemoryStore()
    vector = VectorMemoryStore()
    await structured.init_db()

    deps = AgentDeps(
        session_id="my-session",
        structured_store=structured,
        vector_store=vector,
        sandbox_base_url=SANDBOX_URL,
    )

    output, messages = await run_agent("What can you do?", deps)
    print(output)
    await structured.close()

asyncio.run(main())
```

## CLI

```bash
lra init              # Create .env and show setup instructions
lra chat              # Start the agent chat loop
lra list-tools        # List static and dynamic tools
lra inspect-tool X    # Inspect a dynamic tool
lra list-memory -s SESSION  # List memory for a session
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | OpenAI API key | (required) |
| SANDBOX_URL | Sandbox API base URL | http://localhost:8000 |
| DATABASE_URL | SQLAlchemy async URL | sqlite+aiosqlite:///./data/agent_memory.db |
| VECTOR_STORE_PATH | ChromaDB path | ./data/chroma_db |

## Sandbox (optional)

The sandbox enables code execution. Basic chat and memory work without it.

```bash
# Option A: Run locally (requires Docker)
python -m uvicorn sandbox.server:app --reload --port 8000

# Option B: Docker Compose
docker compose up sandbox
```

## Project structure

```
├── agents/              # Main agent and subagents
├── tools/               # Memory, sandbox, task tools
├── sandbox/              # Sandbox API and kernel
├── memory/               # Structured and vector stores
├── schemas/              # Pydantic models
├── long_running_agents/  # Package exports
├── cli.py                # CLI entry point
├── config.py
├── main.py
└── pyproject.toml
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
mypy agents tools memory schemas
```

## License

MIT
