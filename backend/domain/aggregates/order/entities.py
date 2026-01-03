from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from domain.validation import validate_cart_item_quantity


@dataclass(frozen=True)
class OrderItem:
    id: UUID
    order_id: UUID
    product_id: UUID
    product_name: str
    unit_price: Decimal
    quantity: int

    @classmethod
    def create(
        cls,
        order_id: UUID,
        product_id: UUID,
        product_name: str,
        unit_price: Decimal,
        quantity: int,
    ) -> "OrderItem":
        """
        Factory method to create a new OrderItem with validation.

        Raises:
            ValidationError: If quantity is invalid
        """
        return cls(
            id=uuid4(),
            order_id=order_id,
            product_id=product_id,
            product_name=product_name,
            unit_price=unit_price,
            quantity=validate_cart_item_quantity(quantity),
        )

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Order:
    id: UUID
    items: List[OrderItem]
    submitted_at: datetime | None

    @classmethod
    def create(cls, items: List[OrderItem]) -> "Order":
        """
        Factory method to create a new Order.

        Args:
            items: List of OrderItems (should be created via OrderItem.create())
        """
        return cls(
            id=uuid4(),
            items=items,
            submitted_at=None,
        )

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))
