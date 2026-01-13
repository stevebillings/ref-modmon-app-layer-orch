"""
Base classes for domain events.

Domain events are immutable value objects that represent something
that happened in the domain. They are framework-agnostic and belong
to the domain layer.
"""

from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict
from uuid import UUID, uuid4


def _now_utc() -> datetime:
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events.

    Events are immutable and include a unique ID and timestamp.
    Subclasses should add fields specific to the event type.

    Note: Subclasses must ensure their required fields come before
    inherited default fields by redeclaring base class fields last.
    """

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)

    def get_event_type(self) -> str:
        """Return the event type name for serialization/routing."""
        return self.__class__.__name__

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        result: Dict[str, Any] = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = str(value)
            result[f.name] = value
        result["event_type"] = self.get_event_type()
        return result
