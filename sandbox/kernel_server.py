"""
Minimal HTTP server that runs inside sandbox containers.
Accepts POST /execute with code and returns output as NDJSON.
"""

import io
import json
import sys
from contextlib import redirect_stdout, redirect_stderr

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class ExecuteRequest(BaseModel):
    """Request body for code execution."""

    code: str


def run_code(code: str) -> tuple[str, str, bool]:
    """Execute code and capture stdout, stderr, and success status."""
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    success = True

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(compile(code, "<sandbox>", "exec"))
    except Exception as e:
        stderr_capture.write(str(e))
        success = False

    return stdout_capture.getvalue(), stderr_capture.getvalue(), success


@app.post("/execute")
def execute(request: ExecuteRequest) -> dict:
    """Execute Python code and return output as NDJSON-style events."""
    stdout, stderr, success = run_code(request.code)

    # Return as single response (client can parse as NDJSON if we send multiple lines)
    return {
        "type": "result",
        "stdout": stdout,
        "stderr": stderr,
        "success": success,
    }


@app.get("/health")
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
