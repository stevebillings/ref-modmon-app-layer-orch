"""
Domain events for the Cart aggregate.
"""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class CartItemAdded(DomainEvent):
    """Raised when an item is added to the cart."""

    cart_id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    actor_id: str


@dataclass(frozen=True, kw_only=True)
class CartItemQuantityUpdated(DomainEvent):
    """Raised when a cart item's quantity is updated."""

    cart_id: UUID
    product_id: UUID
    product_name: str
    old_quantity: int
    new_quantity: int
    actor_id: str


@dataclass(frozen=True, kw_only=True)
class CartItemRemoved(DomainEvent):
    """Raised when an item is removed from the cart."""

    cart_id: UUID
    product_id: UUID
    product_name: str
    quantity_removed: int
    actor_id: str


@dataclass(frozen=True, kw_only=True)
class CartSubmitted(DomainEvent):
    """Raised when the cart is submitted for order creation."""

    cart_id: UUID
    total: Decimal
    item_count: int
    actor_id: str
