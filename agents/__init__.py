"""Agents package."""

from agents.deps import AgentDeps


def __getattr__(name: str):
    if name == "create_agent":
        from agents.main_agent import create_agent
        return create_agent
    if name == "run_agent":
        from agents.main_agent import run_agent
        return run_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["AgentDeps", "create_agent", "run_agent"]
