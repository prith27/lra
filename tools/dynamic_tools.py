"""Dynamic tool generation: agent creates new tools at runtime."""

import ast
import uuid
from pathlib import Path
from typing import Any

from pydantic_ai import RunContext, Tool
from pydantic_ai.toolsets import FunctionToolset

from agents.deps import AgentDeps

# Registry of dynamically created tools (name -> (func, metadata))
_dynamic_tool_registry: dict[str, tuple[Any, dict[str, Any]]] = {}

# Path for persisting dynamic tool source
DYNAMIC_TOOLS_DIR = Path(__file__).parent / "dynamic"

# Dangerous AST node types
FORBIDDEN_NODE_TYPES = (
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    ast.Nonlocal,
    ast.Lambda,
    ast.AsyncFunctionDef,
    ast.ClassDef,
)

# Forbidden names in code
FORBIDDEN_NAMES = {"os", "sys", "subprocess", "eval", "exec", "compile", "__import__", "open"}


def _validate_ast(code: str) -> None:
    """Validate generated code via AST. Raise ValueError if dangerous."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        raise ValueError(f"Invalid syntax: {e}") from e

    for node in ast.walk(tree):
        if type(node) in FORBIDDEN_NODE_TYPES:
            raise ValueError(f"Forbidden construct: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            raise ValueError(f"Forbidden name: {node.id}")
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in FORBIDDEN_NAMES:
                raise ValueError(f"Forbidden attribute: {node.value.id}.{node.attr}")


def _assemble_function(name: str, args: str, code: str, doc: str) -> str:
    """Assemble a Python function from components."""
    indented = "\n    ".join(code.strip().split("\n"))
    return f'def {name}({args}):\n    """{doc}"""\n    {indented}\n'


def _compile_and_create_tool(name: str, args: str, code: str, doc: str):
    """Compile code into a function and wrap as Tool."""
    full_code = _assemble_function(name, args, code, doc)
    _validate_ast(full_code)
    local: dict[str, Any] = {}
    exec(full_code, {"__builtins__": __builtins__}, local)
    func = local[name]
    return Tool(func, takes_ctx=False)


async def generate_tool(
    ctx: RunContext[AgentDeps],
    name: str,
    args: str,
    code: str,
    doc: str,
) -> str:
    """Generate and register a new tool. Only use when absolutely necessary. Never override existing tools.

    Args:
        name: Function name (valid Python identifier)
        args: Comma-separated arguments, e.g. "x: int, y: int"
        code: Function body (indented code, e.g. "return x + y")
        doc: Docstring for the tool
    """
    if name in _dynamic_tool_registry:
        return f"Error: Tool '{name}' already exists. Choose a different name."
    if not name.isidentifier():
        return f"Error: '{name}' is not a valid Python identifier."
    try:
        tool = _compile_and_create_tool(name, args, code, doc)
    except ValueError as e:
        return f"Validation failed: {e}"
    except Exception as e:
        return f"Compilation failed: {e}"

    tool_id = str(uuid.uuid4())[:8]
    _dynamic_tool_registry[name] = (tool, {"args": args, "doc": doc, "created_at": tool_id})

    # Persist source
    DYNAMIC_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    source_path = DYNAMIC_TOOLS_DIR / f"{name}_{tool_id}.py"
    source_path.write_text(_assemble_function(name, args, code, doc), encoding="utf-8")

    return f"Tool '{name}' registered successfully. It will be available in future runs."


def get_dynamic_tools() -> list[Tool]:
    """Return list of dynamically registered tools for use in agent."""
    return [t[0] for t in _dynamic_tool_registry.values()]


def list_dynamic_tools() -> list[dict[str, Any]]:
    """List metadata of all dynamic tools."""
    return [
        {"name": name, **meta}
        for name, (_, meta) in _dynamic_tool_registry.items()
    ]


def get_dynamic_toolset() -> FunctionToolset:
    """Return a FunctionToolset of dynamic tools for use in agent.run(toolsets=[...])."""
    tools = get_dynamic_tools()
    if not tools:
        return FunctionToolset(tools=[])
    return FunctionToolset(tools=tools)
