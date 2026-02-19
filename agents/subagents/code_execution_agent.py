"""Code execution subagent: specialized for writing and running code."""

from pydantic_ai import Agent

from agents.deps import AgentDeps
from tools.sandbox_tools import create_sandbox, execute_code

code_execution_agent = Agent(
    "openai:gpt-4o",
    deps_type=AgentDeps,
    output_type=str,
    instructions="""You are a code execution specialist. Your job is to:
- Write Python code to solve the user's request
- Create a sandbox if needed, then execute the code
- Return the output clearly. Do not run arbitrary or dangerous code.
Only handle code-related tasks. Delegate other tasks back to the main agent.""",
    tools=[create_sandbox, execute_code],
)
