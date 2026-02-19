"""Research subagent: specialized for memory search and synthesis."""

from pydantic_ai import Agent

from agents.deps import AgentDeps
from tools.memory_tools import search_memory, write_memory

research_agent = Agent(
    "openai:gpt-4o",
    deps_type=AgentDeps,
    output_type=str,
    instructions="""You are a research specialist. Your job is to:
- Search memory for relevant past information using search_memory
- Synthesize findings into a clear summary
- Store important new facts with write_memory when appropriate
Only handle research and memory-related tasks. Do not execute code.""",
    tools=[search_memory, write_memory],
)
