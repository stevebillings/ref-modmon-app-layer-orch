"""
Domain events for the Cart aggregate.

Note: All fields have defaults for Python 3.9 dataclass inheritance compatibility.
When constructing events, always provide all field values as keyword arguments.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from domain.events import DomainEvent, _now_utc


@dataclass(frozen=True)
class CartItemAdded(DomainEvent):
    """Raised when an item is added to the cart."""

    cart_id: UUID = field(default_factory=uuid4)
    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    quantity: int = 0
    unit_price: Decimal = Decimal("0")
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class CartItemQuantityUpdated(DomainEvent):
    """Raised when a cart item's quantity is updated."""

    cart_id: UUID = field(default_factory=uuid4)
    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    old_quantity: int = 0
    new_quantity: int = 0
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class CartItemRemoved(DomainEvent):
    """Raised when an item is removed from the cart."""

    cart_id: UUID = field(default_factory=uuid4)
    product_id: UUID = field(default_factory=uuid4)
    product_name: str = ""
    quantity_removed: int = 0
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)


@dataclass(frozen=True)
class CartSubmitted(DomainEvent):
    """Raised when the cart is submitted for order creation."""

    cart_id: UUID = field(default_factory=uuid4)
    total: Decimal = Decimal("0")
    item_count: int = 0
    actor_id: str = ""
    # Re-declare parent fields to maintain field order
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=_now_utc)
