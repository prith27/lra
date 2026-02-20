"""Framework CLI commands: create-agent, run, create-tool, etc."""

import argparse
import asyncio
import importlib.util
import sys
import uuid
from pathlib import Path

from pydantic_ai import Tool

_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


def _get_tools_help() -> str:
    return """

You have access to these tools:
- search_memory, write_memory, get_recent_conversations: Memory and recall
- create_task, update_task_status, list_tasks: Task management
- create_sandbox, execute_code: Run Python in isolated containers
- generate_tool: Create new tools (allowed imports: json, math, datetime, re, requests, httpx)
- delegate_code_task, delegate_research_task: Delegate to specialists
"""


def cmd_create_agent(args: argparse.Namespace) -> None:
    """Create a new agent project with custom system prompt."""
    name = getattr(args, "name", None) or "my_agent"
    system_prompt = getattr(args, "prompt", None)

    if system_prompt is None:
        print("Enter a system prompt describing your agent (e.g. 'You are a coding assistant').")
        print("Press Enter twice when done:\n")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "" and lines and lines[-1] == "":
                lines.pop()
                break
            lines.append(line)
        system_prompt = "\n".join(lines).strip() if lines else "You are a helpful AI assistant."

    if not system_prompt:
        system_prompt = "You are a helpful AI assistant."

    agent_dir = Path.cwd() / name
    if agent_dir.exists():
        print(f"Error: '{name}' already exists. Choose a different name or remove it.")
        return

    agent_dir.mkdir(parents=True)
    instructions = system_prompt.rstrip() + _get_tools_help()
    instructions_escaped = instructions.replace('"""', '\\"\\"\\"')

    agent_py = f'''"""Custom agent - edit agent.py to customize."""

import uuid
from pydantic_ai import Agent, UsageLimits

from agents.deps import AgentDeps
from agents.observability import configure_logfire, log_audit_async
from tools.dynamic_tools import generate_tool, get_dynamic_tools, get_dynamic_toolset
from tools.memory_tools import (
    get_recent_conversations,
    get_task_state,
    search_memory,
    write_memory,
)
from tools.sandbox_tools import create_sandbox, execute_code
from tools.subagent_tools import delegate_code_task, delegate_research_task
from tools.task_tools import create_task, list_tasks, update_task_status

INSTRUCTIONS = """{instructions_escaped}"""

agent = Agent(
    "openai:gpt-4o",
    deps_type=AgentDeps,
    output_type=str,
    instructions=INSTRUCTIONS,
    tools=[
        search_memory,
        write_memory,
        get_recent_conversations,
        get_task_state,
        create_task,
        update_task_status,
        list_tasks,
        create_sandbox,
        execute_code,
        generate_tool,
        delegate_code_task,
        delegate_research_task,
    ],
)


async def run_agent(prompt: str, deps: AgentDeps, message_history: list | None = None) -> tuple[str, list]:
    """Run the agent with the given prompt."""
    configure_logfire()
    run_id = str(uuid.uuid4())[:8]
    toolsets = [get_dynamic_toolset()] if get_dynamic_tools() else []
    usage_limits = UsageLimits(request_limit=15, total_tokens_limit=100000, tool_calls_limit=30)
    run_kwargs = {{"deps": deps, "toolsets": toolsets, "usage_limits": usage_limits}}
    if message_history:
        run_kwargs["message_history"] = message_history
    result = await agent.run(prompt, **run_kwargs)
    output = result.output if result.output else ""
    await log_audit_async(deps.structured_store, run_id, deps.session_id, "agent_output", {{"output": output}})
    return output, result.all_messages()
'''

    main_py = '''"""Run this agent: python main.py or lra run ."""

import asyncio
import sys
import uuid

from agent import run_agent
from agents.deps import AgentDeps
from config import OPENAI_API_KEY, SANDBOX_URL
from memory.structured_store import StructuredMemoryStore
from memory.vector_store import VectorMemoryStore


def _check_config():
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        print("Error: OPENAI_API_KEY is not set. Run lra init or set in .env", file=sys.stderr)
        sys.exit(1)


async def _persist_turn(session_id, prompt, output, structured, vector):
    await structured.append_conversation(session_id, "user", prompt)
    await structured.append_conversation(session_id, "assistant", output)
    turn_id = str(uuid.uuid4())
    turn_text = f"User: {prompt}\\nAssistant: {output}"
    vector.add(turn_id, turn_text, {"session_id": session_id, "type": "conversation"})


async def main():
    _check_config()
    session_id = str(uuid.uuid4())[:8]
    structured = StructuredMemoryStore()
    vector = VectorMemoryStore()
    await structured.init_db()
    deps = AgentDeps(session_id=session_id, structured_store=structured, vector_store=vector, sandbox_base_url=SANDBOX_URL)
    print("Agent ready. Type your message and press Enter. Type 'q' to quit.\\n")
    message_history = []
    while True:
        try:
            prompt = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\\nGoodbye!")
            break
        if prompt.lower() == "q":
            print("Goodbye!")
            break
        if not prompt:
            continue
        try:
            output, message_history = await run_agent(prompt, deps, message_history or None)
            print(f"Agent: {output}\\n")
            await _persist_turn(session_id, prompt, output, structured, vector)
        except KeyboardInterrupt:
            print("\\nInterrupted.")
            break
    await structured.close()


if __name__ == "__main__":
    asyncio.run(main())
'''

    env_example = """# OpenAI API key (required)
OPENAI_API_KEY=

# Sandbox URL (optional, for code execution)
SANDBOX_URL=http://localhost:8000
"""

    readme = f"""# {name}

Custom LRA agent. Edit `agent.py` to change the system prompt or tools.

## Run

```bash
cd {name}
lra init   # if you need .env
lra run .
```

Or: `python main.py` (from this directory)
"""

    (agent_dir / "agent.py").write_text(agent_py, encoding="utf-8")
    (agent_dir / "main.py").write_text(main_py, encoding="utf-8")
    (agent_dir / ".env.example").write_text(env_example.strip() + "\n", encoding="utf-8")
    (agent_dir / "README.md").write_text(readme, encoding="utf-8")

    print(f"Created agent '{name}' at {agent_dir}")
    print("\nNext steps:")
    print(f"  cd {name}")
    print("  lra init          # create .env, add OPENAI_API_KEY")
    print("  lra run .        # run your agent")
    print("\nEdit agent.py to customize the system prompt.")


def cmd_run(args: argparse.Namespace) -> None:
    """Run a custom agent."""
    path = getattr(args, "path", ".") or "."
    agent_path = Path(path).resolve()

    if agent_path.is_dir():
        main_file = agent_path / "main.py"
        agent_file = agent_path / "agent.py"
        if main_file.exists():
            to_run = main_file
        elif agent_file.exists():
            to_run = agent_file
        else:
            print(f"Error: No agent.py or main.py in {agent_path}")
            return
    else:
        to_run = agent_path
        if not to_run.exists():
            print(f"Error: {to_run} not found")
            return

    run_dir = to_run.parent
    if str(run_dir) not in sys.path:
        sys.path.insert(0, str(run_dir))
    sys.path.insert(0, str(_PROJECT_ROOT))

    env_file = run_dir / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)

    spec = importlib.util.spec_from_file_location("lra_agent", to_run)
    if spec is None or spec.loader is None:
        print(f"Error: Could not load {to_run}")
        return

    module = importlib.util.module_from_spec(spec)
    sys.modules["lra_agent"] = module

    import os
    orig_cwd = os.getcwd()
    os.chdir(run_dir)

    try:
        spec.loader.exec_module(module)
        if hasattr(module, "main"):
            asyncio.run(module.main())
        else:
            print("Error: Agent module must define main()")
    finally:
        os.chdir(orig_cwd)


def cmd_create_tool(args: argparse.Namespace) -> None:
    """Create a tool interactively or from file."""
    from tools.dynamic_tools import (
        ALLOWED_IMPORTS,
        DYNAMIC_TOOLS_DIR,
        _assemble_function,
        _compile_and_create_tool,
        _dynamic_tool_registry,
        _validate_ast,
    )
    from tools.sandbox_tools import _execute_in_sandbox_raw
    from agents.deps import AgentDeps
    from config import SANDBOX_URL
    from memory.structured_store import StructuredMemoryStore
    from memory.vector_store import VectorMemoryStore

    file_path = getattr(args, "file", None)
    if file_path:
        path = Path(file_path)
        if not path.exists():
            print(f"Error: {path} not found")
            return
        code = path.read_text(encoding="utf-8")
        local: dict = {}
        try:
            exec(code, {"__builtins__": __builtins__}, local)
        except Exception as e:
            print(f"Error executing file: {e}")
            return
        funcs = [v for k, v in local.items() if callable(v) and not k.startswith("_")]
        if len(funcs) != 1:
            print("Error: File must define exactly one function at module level")
            return
        func = funcs[0]
        name = func.__name__
        if name in _dynamic_tool_registry:
            print(f"Error: Tool '{name}' already exists")
            return
        import inspect
        sig = inspect.signature(func)
        args_str = ", ".join(f"{p.name}: str" for p in sig.parameters.values())
        doc = inspect.getdoc(func) or f"Tool {name}"
        full_code = code
    else:
        print("Create a new tool. Allowed imports:", ", ".join(sorted(ALLOWED_IMPORTS)))
        name = input("Tool name: ").strip()
        if not name or not name.isidentifier():
            print("Error: Invalid name")
            return
        if name in _dynamic_tool_registry:
            print(f"Error: Tool '{name}' already exists")
            return
        args_str = input("Arguments (e.g. x: str, y: int): ").strip() or "query: str"
        doc = input("Docstring: ").strip() or f"Tool {name}"
        print("Function body (paste code, end with empty line):")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "" and lines:
                break
            lines.append(line)
        code_body = "\n".join(lines).strip()
        if not code_body:
            print("Error: Empty body")
            return
        full_code = _assemble_function(name, args_str, code_body, doc)
        try:
            _validate_ast(full_code)
            tool = _compile_and_create_tool(name, args_str, code_body, doc)
        except ValueError as e:
            print(f"Validation failed: {e}")
            return

    class Ctx:
        pass
    ctx = Ctx()

    async def _setup():
        structured = StructuredMemoryStore()
        vector = VectorMemoryStore()
        await structured.init_db()
        ctx.deps = AgentDeps(session_id="cli", structured_store=structured, vector_store=vector, sandbox_base_url=SANDBOX_URL)
        success, stdout, stderr = await _execute_in_sandbox_raw(ctx, full_code)
        await structured.close()
        return success, stdout, stderr

    success, stdout, stderr = asyncio.run(_setup())
    if not success:
        print(f"Sandbox validation failed: {stderr or 'Execution error'}")
        return

    if file_path:
        tool = Tool(func, takes_ctx=False)
    # else: tool already set from _compile_and_create_tool in interactive flow

    _dynamic_tool_registry[name] = (tool, {"args": args_str, "doc": doc, "created_at": str(uuid.uuid4())[:8]})
    DYNAMIC_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    (DYNAMIC_TOOLS_DIR / f"{name}_{str(uuid.uuid4())[:8]}.py").write_text(full_code, encoding="utf-8")
    print(f"Tool '{name}' created and registered.")


def cmd_list_agents(args: argparse.Namespace) -> None:
    """List agent directories in current path."""
    cwd = Path.cwd()
    found = []
    for d in cwd.iterdir():
        if d.is_dir() and (d / "agent.py").exists():
            found.append(str(d.relative_to(cwd)))
    if found:
        for p in sorted(found):
            print(p)
    else:
        print("No agents found. Run 'lra create-agent <name>' to create one.")


def cmd_config(args: argparse.Namespace) -> None:
    """Show config."""
    from config import OPENAI_API_KEY, SANDBOX_URL, DATABASE_URL, VECTOR_STORE_PATH
    print("Current config (from .env / environment):")
    print(f"  OPENAI_API_KEY: {'(set)' if OPENAI_API_KEY else '(not set)'}")
    print(f"  SANDBOX_URL: {SANDBOX_URL}")
    print(f"  DATABASE_URL: {DATABASE_URL}")
    print(f"  VECTOR_STORE_PATH: {VECTOR_STORE_PATH}")


def cmd_export_tools(args: argparse.Namespace) -> None:
    """Export dynamic tools to a static Python file."""
    from tools.dynamic_tools import DYNAMIC_TOOLS_DIR, list_dynamic_tools

    tools = list_dynamic_tools()
    if not tools:
        print("No dynamic tools to export.")
        return
    out_path = Path(getattr(args, "output", "tools/custom_tools.py") or "tools/custom_tools.py")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    parts = ['"""Auto-exported dynamic tools."""\n']
    for f in sorted(DYNAMIC_TOOLS_DIR.glob("*.py")):
        if f.name.startswith("."):
            continue
        parts.append(f.read_text(encoding="utf-8"))
        parts.append("\n\n")
    out_path.write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")
    print(f"Exported {len(tools)} tools to {out_path}")


def cmd_validate_tool(args: argparse.Namespace) -> None:
    """Validate a tool file in the sandbox without registering."""
    path = Path(args.file)
    if not path.exists():
        print(f"Error: {path} not found")
        return
    code = path.read_text(encoding="utf-8")

    class Ctx:
        pass
    ctx = Ctx()

    async def _run():
        from tools.sandbox_tools import _execute_in_sandbox_raw
        from agents.deps import AgentDeps
        from config import SANDBOX_URL
        from memory.structured_store import StructuredMemoryStore
        from memory.vector_store import VectorMemoryStore

        structured = StructuredMemoryStore()
        vector = VectorMemoryStore()
        await structured.init_db()
        ctx.deps = AgentDeps(session_id="validate", structured_store=structured, vector_store=vector, sandbox_base_url=SANDBOX_URL)
        return await _execute_in_sandbox_raw(ctx, code)

    success, stdout, stderr = asyncio.run(_run())
    if success:
        print("Validation passed.")
        if stdout:
            print(stdout)
    else:
        print("Validation failed:")
        print(stderr)
