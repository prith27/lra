"""
Sandbox manager: FastAPI service that creates and manages isolated code execution containers.
"""

import os
import re
import uuid
from typing import Any

import docker
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Dangerous patterns to reject before execution
DANGEROUS_PATTERNS = [
    r"\bos\.system\s*\(",
    r"\bsubprocess\s*\.\s*",
    r"\bexec\s*\(",
    r"\beval\s*\(",
    r"__import__\s*\(",
    r"open\s*\(\s*['\"]/",
    r"rm\s+-rf",
    r"rm\s+-r\s+/",
    r"\bimport\s+os\b",
    r"\bimport\s+subprocess\b",
    r"\bimport\s+sys\b",
    r"__builtins__",
    r"breakpoint\s*\(",
    r"compile\s*\(",
]
DANGEROUS_REGEX = re.compile("|".join(f"({p})" for p in DANGEROUS_PATTERNS), re.IGNORECASE)

# Idle sandbox TTL (seconds)
SANDBOX_TTL = 30 * 60  # 30 minutes

# Container resource limits
MEMORY_LIMIT = "512m"
CPU_QUOTA = 50000  # 50% of one CPU

# Kernel image name (built from sandbox/Dockerfile)
KERNEL_IMAGE = "longrunningagents-kernel:latest"


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

    code: str


class ExecuteEvent(BaseModel):
    """NDJSON event from code execution."""

    type: str
    stdout: str = ""
    stderr: str = ""
    success: bool = True


def validate_code(code: str) -> None:
    """Reject code containing dangerous patterns."""
    if DANGEROUS_REGEX.search(code):
        raise HTTPException(status_code=400, detail="Code contains forbidden patterns")


# In-memory sandbox registry (in production, use Redis or DB)
sandboxes: dict[str, dict[str, Any]] = {}
docker_client: docker.DockerClient | None = None


def get_docker_client() -> docker.DockerClient:
    """Get Docker client, raising if unavailable."""
    global docker_client
    if docker_client is None:
        try:
            docker_client = docker.from_env()
            docker_client.ping()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Docker unavailable: {e}",
            ) from e
    return docker_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure kernel image exists. Shutdown: cleanup."""
    client = get_docker_client()
    try:
        client.images.get(KERNEL_IMAGE)
    except docker.errors.ImageNotFound:
        # Build from Dockerfile
        import os

        dockerfile_dir = os.path.dirname(os.path.abspath(__file__))
        client.images.build(path=dockerfile_dir, tag=KERNEL_IMAGE)
    yield
    # Cleanup all sandboxes on shutdown
    for sid, info in list(sandboxes.items()):
        try:
            container = info.get("container")
            if container:
                container.stop(timeout=2)
                container.remove()
        except Exception:
            pass
    sandboxes.clear()


app = FastAPI(title="Sandbox API", lifespan=lifespan)

# Optional auth and rate limiting (add SANDBOX_API_KEY to enable auth)
try:
    from sandbox.middleware import AuthMiddleware, RateLimitMiddleware

    app.add_middleware(RateLimitMiddleware)
    if os.environ.get("SANDBOX_API_KEY"):
        app.add_middleware(AuthMiddleware)
except ImportError:
    pass


def _find_free_port() -> int:
    """Find a free port for the container."""
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@app.post("/sandboxes", response_model=SandboxResponse)
def create_sandbox(request: CreateSandboxRequest) -> SandboxResponse:
    """Create a new isolated sandbox container."""
    if request.lang != "python":
        raise HTTPException(status_code=400, detail="Only python is supported")
    client = get_docker_client()
    port = _find_free_port()
    sandbox_id = str(uuid.uuid4())[:8]
    try:
        # Use bridge network so host can connect to container's /execute endpoint.
        # User code runs inside container; validation rejects dangerous patterns.
        container = client.containers.run(
            KERNEL_IMAGE,
            detach=True,
            name=f"sandbox-{sandbox_id}",
            mem_limit=MEMORY_LIMIT,
            cpu_quota=CPU_QUOTA,
            ports={"8000/tcp": port},
            remove=False,
        )
        sandboxes[sandbox_id] = {
            "id": sandbox_id,
            "container": container,
            "port": port,
            "status": "running",
        }
        return SandboxResponse(id=sandbox_id, status="running", port=port)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/sandboxes", response_model=list[SandboxResponse])
def list_sandboxes() -> list[SandboxResponse]:
    """List all active sandboxes."""
    result = []
    for sid, info in sandboxes.items():
        status = "running"
        try:
            container = info.get("container")
            if container:
                container.reload()
                status = container.status
        except Exception:
            status = "unknown"
        result.append(
            SandboxResponse(
                id=sid,
                status=status,
                port=info.get("port"),
            )
        )
    return result


@app.get("/sandboxes/{sandbox_id}", response_model=SandboxResponse)
def get_sandbox(sandbox_id: str) -> SandboxResponse:
    """Get sandbox details."""
    if sandbox_id not in sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    info = sandboxes[sandbox_id]
    status = "running"
    try:
        container = info.get("container")
        if container:
            container.reload()
            status = container.status
    except Exception:
        status = "unknown"
    return SandboxResponse(
        id=sandbox_id,
        status=status,
        port=info.get("port"),
    )


@app.post("/sandboxes/{sandbox_id}/execute")
async def execute_code(sandbox_id: str, request: ExecuteRequest) -> dict:
    """Execute code in the sandbox and return output."""
    validate_code(request.code)
    if sandbox_id not in sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    info = sandboxes[sandbox_id]
    port = info.get("port")
    if not port:
        raise HTTPException(status_code=500, detail="Sandbox port not available")
    import httpx

    url = f"http://127.0.0.1:{port}/execute"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json={"code": request.code})
            resp.raise_for_status()
            data = resp.json()
            return {
                "type": data.get("type", "result"),
                "stdout": data.get("stdout", ""),
                "stderr": data.get("stderr", ""),
                "success": data.get("success", True),
            }
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Sandbox unreachable: {e}") from e


@app.delete("/sandboxes/{sandbox_id}")
def delete_sandbox(sandbox_id: str) -> dict:
    """Stop and remove a sandbox."""
    if sandbox_id not in sandboxes:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    info = sandboxes.pop(sandbox_id)
    try:
        container = info.get("container")
        if container:
            container.stop(timeout=5)
            container.remove()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"status": "deleted"}


# Background cleanup task (simplified: run on each request via middleware or separate thread)
# For MVP we rely on manual DELETE and shutdown cleanup.
