from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4

from domain.aggregates.product.validation import (
    validate_product_name,
    validate_product_price,
    validate_stock_quantity,
)
from domain.exceptions import InsufficientStockError

if TYPE_CHECKING:
    from domain.events import DomainEvent


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
    deleted_at: datetime | None = None
    _domain_events: List["DomainEvent"] = field(
        default_factory=list, repr=False, compare=False
    )

    @property
    def is_deleted(self) -> bool:
        """Check if product is soft-deleted."""
        return self.deleted_at is not None

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

    def reserve_stock(self, quantity: int, actor_id: str = "anonymous") -> None:
        """
        Reserve stock by decrementing stock_quantity.

        Raises:
            InsufficientStockError: If not enough stock available
        """
        from domain.aggregates.product.events import StockReserved

        if not self.has_sufficient_stock(quantity):
            raise InsufficientStockError(
                self.name, self.stock_quantity, quantity
            )
        self.stock_quantity -= quantity

        self._raise_event(
            StockReserved(
                product_id=self.id,
                product_name=self.name,
                quantity_reserved=quantity,
                remaining_stock=self.stock_quantity,
                actor_id=actor_id,
            )
        )

    def release_stock(self, quantity: int, actor_id: str = "anonymous") -> None:
        """Release previously reserved stock by incrementing stock_quantity."""
        from domain.aggregates.product.events import StockReleased

        self.stock_quantity += quantity

        self._raise_event(
            StockReleased(
                product_id=self.id,
                product_name=self.name,
                quantity_released=quantity,
                new_stock=self.stock_quantity,
                actor_id=actor_id,
            )
        )

    def soft_delete(self, actor_id: str = "anonymous") -> None:
        """
        Mark product as soft-deleted.

        Raises:
            ProductAlreadyDeletedError: If product is already deleted
        """
        from domain.aggregates.product.events import ProductDeleted
        from domain.exceptions import ProductAlreadyDeletedError

        if self.is_deleted:
            raise ProductAlreadyDeletedError(str(self.id))

        self.deleted_at = datetime.now(timezone.utc)

        self._raise_event(
            ProductDeleted(
                product_id=self.id,
                product_name=self.name,
                actor_id=actor_id,
            )
        )

    def restore(self, actor_id: str = "anonymous") -> None:
        """
        Restore a soft-deleted product.

        Raises:
            ProductNotDeletedError: If product is not deleted
        """
        from domain.aggregates.product.events import ProductRestored
        from domain.exceptions import ProductNotDeletedError

        if not self.is_deleted:
            raise ProductNotDeletedError(str(self.id))

        self.deleted_at = None

        self._raise_event(
            ProductRestored(
                product_id=self.id,
                product_name=self.name,
                actor_id=actor_id,
            )
        )

    def _raise_event(self, event: "DomainEvent") -> None:
        """Record a domain event."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List["DomainEvent"]:
        """Return all collected events."""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clear collected events after dispatch."""
        self._domain_events = []
