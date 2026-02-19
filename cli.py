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
        "get_task_state",
        "create_task",
        "update_task_status",
        "list_tasks",
        "create_sandbox",
        "execute_code",
        "generate_tool",
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Long Running Agents CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    list_tools = sub.add_parser("list-tools", help="List available tools")
    list_tools.set_defaults(func=cmd_list_tools)

    inspect = sub.add_parser("inspect-tool", help="Inspect a dynamic tool")
    inspect.add_argument("name", help="Tool name")
    inspect.set_defaults(func=cmd_inspect_tool)

    list_mem = sub.add_parser("list-memory", help="List memory for a session")
    list_mem.add_argument("--session", "-s", default="default", help="Session ID")
    list_mem.add_argument("--limit", "-n", type=int, default=10, help="Limit")
    list_mem.set_defaults(func=cmd_list_memory)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
