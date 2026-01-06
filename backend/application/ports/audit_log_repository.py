from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True)
class AuditLogEntry:
    """
    Domain representation of an audit log entry.

    Immutable value object for audit log data.
    """

    id: UUID
    event_type: str
    event_id: UUID
    occurred_at: datetime
    actor_id: str
    aggregate_type: str
    aggregate_id: UUID | None
    event_data: dict[str, Any]
    created_at: datetime


class AuditLogRepository(ABC):
    """
    Repository port for audit log persistence.

    Provides operations for saving audit log entries.
    This is a write-only repository - audit logs are immutable.
    """

    @abstractmethod
    def save(
        self,
        event_type: str,
        event_id: UUID,
        occurred_at: datetime,
        actor_id: str,
        aggregate_type: str,
        aggregate_id: UUID | None,
        event_data: dict[str, Any],
    ) -> AuditLogEntry:
        """
        Save an audit log entry.

        Args:
            event_type: The type of domain event
            event_id: Unique ID of the event
            occurred_at: When the event occurred
            actor_id: ID of the user/actor who caused the event
            aggregate_type: Type of the aggregate (e.g., "Product", "Cart")
            aggregate_id: ID of the aggregate, if applicable
            event_data: Full event data as a dictionary

        Returns:
            The saved audit log entry
        """
        pass
