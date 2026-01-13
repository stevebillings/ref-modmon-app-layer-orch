"""
Domain events for the Product aggregate.

Note: All fields have defaults for Python 3.9 dataclass inheritance compatibility.
When constructing events, always provide all field values as keyword arguments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from domain.events import DomainEvent, _now_utc


@dataclass(frozen=True)
class StockReserved(DomainEvent):
    """Raised when stock is reserved for a cart item."""

    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    quantity_reserved: int = 0
    remaining_stock: int = 0
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class StockReleased(DomainEvent):
    """Raised when previously reserved stock is released."""

    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    quantity_released: int = 0
    new_stock: int = 0
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class ProductDeleted(DomainEvent):
    """Raised when a product is soft-deleted."""

    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class ProductRestored(DomainEvent):
    """Raised when a soft-deleted product is restored."""

    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)
