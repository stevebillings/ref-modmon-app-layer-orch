"""
Domain events for the Order aggregate.

Note: All fields have defaults for Python 3.9 dataclass inheritance compatibility.
When constructing events, always provide all field values as keyword arguments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from domain.events import DomainEvent, _now_utc


@dataclass(frozen=True)
class OrderCreated(DomainEvent):
    """Raised when an order is created from a cart submission."""

    order_id: UUID = field(default_factory=uuid4)
    cart_id: UUID = field(default_factory=uuid4)
    total: Decimal = Decimal("0")
    item_count: int = 0
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)
