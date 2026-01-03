from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from domain.validation import (
    validate_product_name,
    validate_product_price,
    validate_stock_quantity,
)


@dataclass(frozen=True)
class Product:
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

    def with_stock_quantity(self, new_quantity: int) -> "Product":
        """Return a new Product with updated stock quantity."""
        return Product(
            id=self.id,
            name=self.name,
            price=self.price,
            stock_quantity=new_quantity,
            created_at=self.created_at,
        )
