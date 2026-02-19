"""Sandbox tools: execute code and create sandbox."""

import httpx
from pydantic_ai import RunContext

from agents.deps import AgentDeps
from config import SANDBOX_URL


async def execute_code(ctx: RunContext[AgentDeps], code: str) -> str:
    """Execute Python code in the sandbox and return output (stdout + stderr)."""
    sandbox_id = ctx.deps.get_sandbox_id()
    if not sandbox_id:
        return "Error: No sandbox created. Call create_sandbox first."
    url = f"{ctx.deps.sandbox_base_url}/sandboxes/{sandbox_id}/execute"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json={"code": code})
            resp.raise_for_status()
            data = resp.json()
            stdout = data.get("stdout", "")
            stderr = data.get("stderr", "")
            success = data.get("success", True)
            parts = []
            if stdout:
                parts.append(stdout)
            if stderr:
                parts.append(f"stderr: {stderr}")
            if not success and not parts:
                parts.append("Execution failed")
            return "\n".join(parts) if parts else "No output"
    except httpx.HTTPError as e:
        return f"Sandbox error: {e}"


async def create_sandbox(ctx: RunContext[AgentDeps]) -> str:
    """Create a new sandbox for code execution. Store the sandbox ID in session for execute_code."""
    url = f"{ctx.deps.sandbox_base_url}/sandboxes"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"lang": "python"})
            resp.raise_for_status()
            data = resp.json()
            sandbox_id = data.get("id", "")
            ctx.deps.set_sandbox_id(sandbox_id)
            return f"Sandbox created: {sandbox_id}. Ready for execute_code."
    except httpx.HTTPError as e:
        return f"Failed to create sandbox: {e}"
