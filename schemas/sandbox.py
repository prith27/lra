"""Sandbox API request and response models."""

from pydantic import BaseModel, Field


class CreateSandboxRequest(BaseModel):
    """Request to create a new sandbox."""

    lang: str = Field(default="python", description="Programming language")


class SandboxResponse(BaseModel):
    """Response for sandbox creation/listing."""

    id: str
    status: str
    port: int | None = None


class ExecuteRequest(BaseModel):
    """Request to execute code in a sandbox."""

    code: str = Field(..., description="Python code to execute")


class ExecuteEvent(BaseModel):
    """NDJSON event from code execution."""

    type: str = "result"
    stdout: str = ""
    stderr: str = ""
    success: bool = True
