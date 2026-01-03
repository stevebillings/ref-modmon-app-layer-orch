from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from domain.validation import validate_cart_item_quantity


@dataclass(frozen=True)
class CartItem:
    id: UUID
    product_id: UUID
    product_name: str
    unit_price: Decimal
    quantity: int

    @classmethod
    def create(
        cls,
        product_id: UUID,
        product_name: str,
        unit_price: Decimal,
        quantity: int,
    ) -> "CartItem":
        """
        Factory method to create a new CartItem with validation.

        Raises:
            ValidationError: If quantity is invalid
        """
        return cls(
            id=uuid4(),
            product_id=product_id,
            product_name=product_name,
            unit_price=unit_price,
            quantity=validate_cart_item_quantity(quantity),
        )

    @property
    def subtotal(self) -> Decimal:
        return self.unit_price * self.quantity

    def with_quantity(self, new_quantity: int) -> "CartItem":
        """
        Return a new CartItem with updated quantity.

        Raises:
            ValidationError: If quantity is invalid
        """
        return CartItem(
            id=self.id,
            product_id=self.product_id,
            product_name=self.product_name,
            unit_price=self.unit_price,
            quantity=validate_cart_item_quantity(new_quantity),
        )


@dataclass(frozen=True)
class Cart:
    id: UUID
    items: List[CartItem]
    created_at: datetime

    @classmethod
    def create(cls) -> "Cart":
        """Factory method to create a new empty Cart."""
        return cls(
            id=uuid4(),
            items=[],
            created_at=datetime.now(),
        )

    @property
    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))

    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def get_item_by_product_id(self, product_id: UUID) -> CartItem | None:
        """Find a cart item by product ID."""
        for item in self.items:
            if item.product_id == product_id:
                return item
        return None

    def with_items(self, new_items: List[CartItem]) -> "Cart":
        """Return a new Cart with the given items."""
        return Cart(
            id=self.id,
            items=new_items,
            created_at=self.created_at,
        )
