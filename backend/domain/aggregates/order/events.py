"""
Domain events for the Order aggregate.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class OrderCreated(DomainEvent):
    """Raised when an order is created from a cart submission."""

    order_id: UUID
    cart_id: UUID
    total: Decimal
    item_count: int
    actor_id: str
