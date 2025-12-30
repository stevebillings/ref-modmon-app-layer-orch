from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class Product:
    id: UUID
    name: str
    price: Decimal
    stock_quantity: int
    created_at: datetime

    def with_stock_quantity(self, new_quantity: int) -> "Product":
        """Return a new Product with updated stock quantity."""
        return Product(
            id=self.id,
            name=self.name,
            price=self.price,
            stock_quantity=new_quantity,
            created_at=self.created_at,
        )
