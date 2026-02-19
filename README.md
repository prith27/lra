# Long Running Agents

A **chat-driven AI agent** with persistent memory, code execution, and task tracking. You interact via a terminal loop: type a message, the agent responds using its tools, and context is saved across runs.

**What it is:** A general-purpose conversational agent built with Pydantic AI. It remembers past conversations, can run Python in isolated sandboxes, delegate to specialist subagents, and track multi-step work via tasks.

**What it is not:** A workflow automation engine (no schedules, triggers, or DAGs). It’s an interactive assistant, not Zapier or Airflow.

## How it works

1. Run `python main.py` to start the chat loop.
2. Type a message; the agent may call tools (search memory, run code, create tasks, delegate to subagents).
3. Each turn is persisted to SQLite and ChromaDB so the agent can recall past context in future runs.
4. Each run gets a new session ID, but `get_recent_conversations(all_sessions=True)` and `search_memory` allow cross-session recall.

## Features

- **Persistent memory**: Structured store (SQLite) for conversations and tasks; vector store (ChromaDB) for semantic search. Recall past turns across sessions.
- **Code execution**: Sandbox API spins up isolated Docker containers for secure Python execution.
- **Task tracking**: Create, update, and list tasks to manage multi-step work.
- **Subagent delegation**: Delegate code tasks or research tasks to specialized subagents.
- **Dynamic tools**: Agent can generate and register new tools at runtime when needed.

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

## Setup

1. **Create virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY
```

4. **Start the sandbox API** (for code execution)

```bash
# Option A: Run locally (requires Docker)
python -m uvicorn sandbox.server:app --reload --port 8000

# Option B: Docker Compose
docker compose up sandbox
```

5. **Run the agent**

```bash
python main.py
```

## Project Structure

```
├── agents/           # Main agent and subagents
├── tools/            # Memory, sandbox, task tools
├── sandbox/          # Sandbox API and kernel
├── memory/           # Structured and vector stores
├── schemas/          # Pydantic models
├── config.py
├── main.py
└── requirements.txt
```

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| SANDBOX_URL | Sandbox API base URL | http://localhost:8000 |
| OPENAI_API_KEY | OpenAI API key | (required) |
| DATABASE_URL | SQLAlchemy async URL | sqlite+aiosqlite:///./data/agent_memory.db |
| VECTOR_STORE_PATH | ChromaDB path | ./data/chroma_db |

## CLI

```bash
python -m cli list-tools       # List static and dynamic tools
python -m cli inspect-tool X  # Inspect dynamic tool
python -m cli list-memory -s SESSION  # List memory for session
```

## Development

```bash
# Run tests
pytest tests/ -v

# Type check
mypy agents tools memory schemas
```

## License

MIT
