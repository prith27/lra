#!/usr/bin/env python3
"""CLI for managing tools and memory."""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


def cmd_list_tools(args: argparse.Namespace) -> None:
    """List all tools (static + dynamic)."""
    from tools.dynamic_tools import list_dynamic_tools

    dynamic = list_dynamic_tools()
    static = [
        "search_memory",
        "write_memory",
        "get_recent_conversations",
        "get_task_state",
        "create_task",
        "update_task_status",
        "list_tasks",
        "create_sandbox",
        "execute_code",
        "generate_tool",
        "delegate_code_task",
        "delegate_research_task",
    ]
    print("Static tools:", ", ".join(static))
    if dynamic:
        print("Dynamic tools:")
        for t in dynamic:
            print(f"  - {t.get('name', '?')}: {t.get('doc', '')[:50]}...")
    else:
        print("Dynamic tools: (none)")


def cmd_inspect_tool(args: argparse.Namespace) -> None:
    """Inspect a dynamic tool by name."""
    from tools.dynamic_tools import _dynamic_tool_registry

    name = args.name
    if name not in _dynamic_tool_registry:
        print(f"Tool '{name}' not found in dynamic registry.")
        return
    _, meta = _dynamic_tool_registry[name]
    print(json.dumps({"name": name, **meta}, indent=2))


def cmd_list_memory(args: argparse.Namespace) -> None:
    """List memory entries for a session."""

    async def _run() -> None:
        from memory.structured_store import StructuredMemoryStore

        store = StructuredMemoryStore()
        await store.init_db()
        session_id = args.session or "default"
        convs = await store.get_conversations(session_id, limit=args.limit)
        tasks = await store.get_tasks(session_id)
        summaries = await store.get_summaries(session_id, limit=args.limit)
        print(f"Session: {session_id}")
        print(f"Conversations: {len(convs)}")
        for c in convs[-5:]:
            print(f"  [{c['role']}] {c['content'][:60]}...")
        print(f"Tasks: {len(tasks)}")
        for t in tasks:
            print(f"  - {t['id']}: {t['title']} ({t['status']})")
        print(f"Summaries: {len(summaries)}")
        await store.close()

    asyncio.run(_run())


def cmd_init(args: argparse.Namespace) -> None:
    """Create .env from template and print setup instructions."""
    env_path = Path.cwd() / ".env"
    if env_path.exists() and not getattr(args, "force", False):
        print(".env already exists. Use --force to overwrite.")
        return

    template = """# OpenAI API key (required for LLM)
OPENAI_API_KEY=

# Sandbox API URL (optional, for code execution)
SANDBOX_URL=http://localhost:8000

# Database URL (optional)
# DATABASE_URL=sqlite+aiosqlite:///./data/agent_memory.db

# Vector store path (optional)
# VECTOR_STORE_PATH=./data/chroma_db
"""
    env_path.write_text(template.strip() + "\n", encoding="utf-8")
    print("Created .env in current directory.\n")
    print("Next steps:")
    print("  1. Edit .env and set OPENAI_API_KEY=sk-your-key-here")
    print("     Get a key at https://platform.openai.com/api-keys")
    print("  2. Run: lra chat")
    print("")
    print("Optional (for code execution):")
    print("  - Start sandbox: python -m uvicorn sandbox.server:app --port 8000")
    print("  - Requires Docker")


def cmd_chat(args: argparse.Namespace) -> None:
    """Start the agent chat loop."""
    from long_running_agents.chat import run_chat_loop

    try:
        asyncio.run(run_chat_loop())
    except KeyboardInterrupt:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Long Running Agents CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create .env and show setup instructions")
    init.add_argument("--force", "-f", action="store_true", help="Overwrite existing .env")
    init.set_defaults(func=cmd_init)

    chat = sub.add_parser("chat", help="Start the agent chat loop")
    chat.set_defaults(func=cmd_chat)

    list_tools = sub.add_parser("list-tools", help="List available tools")
    list_tools.set_defaults(func=cmd_list_tools)

    inspect = sub.add_parser("inspect-tool", help="Inspect a dynamic tool")
    inspect.add_argument("name", help="Tool name")
    inspect.set_defaults(func=cmd_inspect_tool)

    list_mem = sub.add_parser("list-memory", help="List memory for a session")
    list_mem.add_argument("--session", "-s", default="default", help="Session ID")
    list_mem.add_argument("--limit", "-n", type=int, default=10, help="Limit")
    list_mem.set_defaults(func=cmd_list_memory)

    # Framework commands
    from cli_framework import (
        cmd_config,
        cmd_create_agent,
        cmd_create_tool,
        cmd_export_tools,
        cmd_list_agents,
        cmd_run,
        cmd_validate_tool,
    )

    create_agent = sub.add_parser("create-agent", help="Create a new agent with custom system prompt")
    create_agent.add_argument("name", nargs="?", default="my_agent", help="Agent directory name")
    create_agent.add_argument("--prompt", "-p", help="System prompt (or enter interactively)")
    create_agent.set_defaults(func=cmd_create_agent)

    run = sub.add_parser("run", help="Run a custom agent")
    run.add_argument("path", nargs="?", default=".", help="Path to agent directory or main.py")
    run.set_defaults(func=cmd_run)

    create_tool = sub.add_parser("create-tool", help="Create a tool (interactive or from file)")
    create_tool.add_argument("--file", "-f", help="Path to Python file with function")
    create_tool.set_defaults(func=cmd_create_tool)

    list_agents = sub.add_parser("list-agents", help="List agent directories")
    list_agents.set_defaults(func=cmd_list_agents)

    config = sub.add_parser("config", help="Show config")
    config.set_defaults(func=cmd_config)

    export = sub.add_parser("export-tools", help="Export dynamic tools to static file")
    export.add_argument("--output", "-o", default="tools/custom_tools.py", help="Output path")
    export.set_defaults(func=cmd_export_tools)

    validate = sub.add_parser("validate-tool", help="Validate a tool file in sandbox")
    validate.add_argument("file", help="Path to tool Python file")
    validate.set_defaults(func=cmd_validate_tool)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
