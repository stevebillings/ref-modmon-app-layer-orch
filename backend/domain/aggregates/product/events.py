"""
Domain events for the Product aggregate.
"""

from dataclasses import dataclass
from uuid import UUID

from domain.events import DomainEvent


@dataclass(frozen=True, kw_only=True)
class StockReserved(DomainEvent):
    """Raised when stock is reserved for a cart item."""

    product_id: UUID
    product_name: str
    quantity_reserved: int
    remaining_stock: int
    actor_id: str


@dataclass(frozen=True, kw_only=True)
class StockReleased(DomainEvent):
    """Raised when previously reserved stock is released."""

    product_id: UUID
    product_name: str
    quantity_released: int
    new_stock: int
    actor_id: str
