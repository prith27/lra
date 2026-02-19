"""Tools for delegating to subagents."""

from pydantic_ai import RunContext, UsageLimits

from agents.deps import AgentDeps
from agents.subagents.code_execution_agent import code_execution_agent
from agents.subagents.research_agent import research_agent

USAGE_LIMITS = UsageLimits(request_limit=10, total_tokens_limit=50000, tool_calls_limit=20)


async def delegate_code_task(ctx: RunContext[AgentDeps], task: str) -> str:
    """Delegate a code execution task to the code specialist. Use for: running code, writing scripts, debugging code."""
    result = await code_execution_agent.run(
        task,
        deps=ctx.deps,
        usage=ctx.usage,
        usage_limits=USAGE_LIMITS,
    )
    return result.output if result.output else "No output"


async def delegate_research_task(ctx: RunContext[AgentDeps], task: str) -> str:
    """Delegate a research task to the research specialist. Use for: searching memory, synthesizing past info, recalling facts."""
    result = await research_agent.run(
        task,
        deps=ctx.deps,
        usage=ctx.usage,
        usage_limits=USAGE_LIMITS,
    )
    return result.output if result.output else "No output"
