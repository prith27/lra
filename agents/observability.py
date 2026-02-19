"""Observability: Logfire and audit logging."""

import os
from typing import Any

# Optional Logfire integration
try:
    import logfire

    LOGFIRE_AVAILABLE = True
except ImportError:
    LOGFIRE_AVAILABLE = False


def configure_logfire() -> None:
    """Configure Logfire if available and LOGFIRE_TOKEN is set."""
    if LOGFIRE_AVAILABLE and os.environ.get("LOGFIRE_TOKEN"):
        logfire.configure()
        try:
            logfire.instrument_pydantic_ai()
        except Exception:
            pass


async def log_audit_async(
    structured_store: Any,
    run_id: str,
    session_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    """Log an audit event to structured store (async)."""
    if hasattr(structured_store, "append_audit_log"):
        await structured_store.append_audit_log(run_id, session_id, event_type, payload)
