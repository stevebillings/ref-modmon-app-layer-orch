from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from domain.aggregates.product.validation import (
    validate_product_name,
    validate_product_price,
    validate_stock_quantity,
)
from domain.exceptions import InsufficientStockError


@dataclass
class Product:
    """
    Product aggregate root.

    Mutable aggregate that encapsulates product data and stock management.
    Use create() factory for new products with validation.
    Use constructor directly for reconstitution from persistence.
    """

    id: UUID
    name: str
    price: Decimal
    stock_quantity: int
    created_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        price: Decimal | str | float,
        stock_quantity: int,
    ) -> "Product":
        """
        Factory method to create a new Product with validation.

        Raises:
            ValidationError: If any field fails validation
        """
        return cls(
            id=uuid4(),
            name=validate_product_name(name),
            price=validate_product_price(price),
            stock_quantity=validate_stock_quantity(stock_quantity),
            created_at=datetime.now(),
        )

    def has_sufficient_stock(self, quantity: int) -> bool:
        """Check if the requested quantity can be reserved."""
        return quantity <= self.stock_quantity

    def reserve_stock(self, quantity: int) -> None:
        """
        Reserve stock by decrementing stock_quantity.

        Raises:
            InsufficientStockError: If not enough stock available
        """
        if not self.has_sufficient_stock(quantity):
            raise InsufficientStockError(
                self.name, self.stock_quantity, quantity
            )
        self.stock_quantity -= quantity

    def release_stock(self, quantity: int) -> None:
        """Release previously reserved stock by incrementing stock_quantity."""
        self.stock_quantity += quantity
