"""Registry for subagent types - map task type to agent for delegation."""

from typing import Any, Callable

from pydantic_ai import Agent

# Map task_type -> (agent, delegate_tool_func)
_subagent_registry: dict[str, tuple[Agent[Any, str], Callable[..., Any]]] = {}


def register_subagent(
    task_type: str,
    agent: Agent[Any, str],
    delegate_func: Callable[..., Any],
) -> None:
    """Register a subagent for a task type."""
    _subagent_registry[task_type] = (agent, delegate_func)


def get_subagent(task_type: str) -> tuple[Agent[Any, str], Callable[..., Any]] | None:
    """Get agent and delegate function for a task type."""
    _ensure_initialized()
    return _subagent_registry.get(task_type)


def list_subagents() -> list[str]:
    """List registered task types."""
    _ensure_initialized()
    return list(_subagent_registry.keys())


# Built-in subagents are registered when first accessed
_initialized = False


def _ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return
    from tools.subagent_tools import delegate_code_task, delegate_research_task

    from agents.subagents.code_execution_agent import code_execution_agent
    from agents.subagents.research_agent import research_agent

    register_subagent("code", code_execution_agent, delegate_code_task)
    register_subagent("research", research_agent, delegate_research_task)
    _initialized = True
