# Long Running Agents

AI agent system with Pydantic AI orchestration, external sandbox API, layered memory (structured + vector), and dynamic tools.

## Features

- **Pydantic AI Agent**: Typed agent with memory, sandbox, and task tools
- **Sandbox API**: Isolated Docker containers for secure code execution
- **Structured Memory**: SQLite/PostgreSQL for conversations, tasks, summaries
- **Vector Memory**: ChromaDB for semantic search
- **Task Tools**: Create, update, list tasks

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
