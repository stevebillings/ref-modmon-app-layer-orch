from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from domain.aggregates.order.value_objects import VerifiedAddress
from domain.validation import validate_positive_quantity


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
            quantity=validate_positive_quantity(quantity),
        )

    def get_subtotal(self) -> Decimal:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Order:
    id: UUID
    user_id: UUID
    items: List[OrderItem]
    shipping_address: VerifiedAddress
    submitted_at: datetime | None

    @classmethod
    def create(
        cls,
        user_id: UUID,
        items: List[OrderItem],
        shipping_address: VerifiedAddress,
    ) -> "Order":
        """
        Factory method to create a new Order.

        Args:
            user_id: The ID of the user who placed the order
            items: List of OrderItems (should be created via OrderItem.create())
            shipping_address: Verified shipping address for delivery
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            items=items,
            shipping_address=shipping_address,
            submitted_at=None,
        )

    def get_total(self) -> Decimal:
        return sum((item.get_subtotal() for item in self.items), Decimal("0"))
