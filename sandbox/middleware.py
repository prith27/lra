"""Sandbox API middleware: auth, rate limiting."""

import os
import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

SANDBOX_API_KEY = os.getenv("SANDBOX_API_KEY", "")

# Simple in-memory rate limiter: client_id -> (count, window_start)
_RATE_LIMIT: dict[str, tuple[int, float]] = defaultdict(lambda: (0, time.time()))
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 100  # requests per window


def _get_client_id(request: Request) -> str:
    """Extract client identifier for rate limiting."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class AuthMiddleware(BaseHTTPMiddleware):
    """Optional API key authentication. Skip if SANDBOX_API_KEY not set."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if SANDBOX_API_KEY:
            auth = request.headers.get("Authorization")
            if not auth or not auth.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Missing or invalid Authorization")
            token = auth.split(" ", 1)[1]
            if token != SANDBOX_API_KEY:
                raise HTTPException(status_code=403, detail="Invalid API key")
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiting per client."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_id = _get_client_id(request)
        now = time.time()
        count, window_start = _RATE_LIMIT[client_id]
        if now - window_start > RATE_LIMIT_WINDOW:
            count, window_start = 0, now
        count += 1
        _RATE_LIMIT[client_id] = (count, window_start)
        if count > RATE_LIMIT_MAX:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_MAX - count))
        return response
