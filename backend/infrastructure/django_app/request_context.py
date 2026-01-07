"""
Request context management using contextvars.

Provides a way to track request IDs and other request-scoped data
across the entire request lifecycle, including in domain events and logs.
"""

from contextvars import ContextVar
from typing import Optional
from uuid import uuid4

# Context variable for the current request ID
_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Get the current request ID, or None if not in a request context."""
    return _request_id.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    _request_id.set(request_id)


def generate_request_id() -> str:
    """Generate a new unique request ID."""
    return str(uuid4())


def clear_request_id() -> None:
    """Clear the request ID from the current context."""
    _request_id.set(None)
