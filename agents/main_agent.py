"""Main Pydantic AI agent with memory and sandbox tools."""

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

SYSTEM_PROMPT = """You are a helpful AI assistant with access to:
- search_memory: Search past summaries and facts by semantic similarity (Chroma)
- write_memory: Store important facts or summaries for later recall
- get_recent_conversations: Get recent conversation turns. Use all_sessions=True for "last conversation", "recent chat", or "what did we discuss" queries, since each run may use a new session and the current session can be empty.
- get_task_state: Look up task status by ID
- create_task, update_task_status, list_tasks: Manage tasks
- create_sandbox: Create an isolated environment for code execution
- execute_code: Run Python code in the sandbox (call create_sandbox first if needed)
- generate_tool: Create a new tool when absolutely necessary (only when no existing tool fits). Never override existing tools. Code is validated in the sandbox first. Allowed imports: json, math, datetime, re, requests, httpx. Call create_sandbox before generate_tool if needed.
- delegate_code_task: Delegate code execution tasks (running code, writing scripts) to the code specialist.
- delegate_research_task: Delegate research tasks (searching memory, recalling facts) to the research specialist.

Use delegate_code_task for code execution; delegate_research_task for research. Use these tools as needed. When the user asks to run code, create a sandbox first, then execute.
When recalling past context, use search_memory. When learning something important, use write_memory.
For "last conversation" or "recent chat" queries, call get_recent_conversations(all_sessions=True) first. If it returns empty, use search_memory to find relevant past context.
Use task tools to track multi-step work.
"""

agent = Agent(
    "openai:gpt-4o",
    deps_type=AgentDeps,
    output_type=str,
    instructions=SYSTEM_PROMPT,
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


def create_agent() -> Agent[AgentDeps, str]:
    """Return the configured agent (for reuse or customization)."""
    return agent


async def run_agent(
    prompt: str,
    deps: AgentDeps,
    message_history: list | None = None,
) -> tuple[str, list]:
    """Run the agent with the given prompt and dependencies.
    Returns (output, all_messages) - pass all_messages as message_history to the next run.
    """
    configure_logfire()
    run_id = str(uuid.uuid4())[:8]
    toolsets = [get_dynamic_toolset()] if get_dynamic_tools() else []
    usage_limits = UsageLimits(request_limit=15, total_tokens_limit=100000, tool_calls_limit=30)
    run_kwargs: dict = {
        "deps": deps,
        "toolsets": toolsets,
        "usage_limits": usage_limits,
    }
    if message_history:
        run_kwargs["message_history"] = message_history
    result = await agent.run(prompt, **run_kwargs)
    output = result.output if result.output is not None else ""
    await log_audit_async(
        deps.structured_store,
        run_id,
        deps.session_id,
        "agent_output",
        {
            "output": output,
            "usage": str(result.usage()) if hasattr(result, "usage") and callable(getattr(result, "usage")) else "",
        },
    )
    return output, result.all_messages()
