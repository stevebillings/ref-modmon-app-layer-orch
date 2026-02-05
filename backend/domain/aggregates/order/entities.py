from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

from domain.aggregates.order.value_objects import VerifiedAddress
from domain.validation import validate_positive_quantity

if TYPE_CHECKING:
    from domain.events import DomainEvent


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


@dataclass
class Order:
    """
    Order aggregate root.

    Mutable aggregate that represents a submitted order. Use create() factory
    for new orders with validation and event raising.
    Use constructor directly for reconstitution from persistence.
    """

    id: UUID
    user_id: UUID
    items: List[OrderItem]
    shipping_address: VerifiedAddress
    submitted_at: Optional[datetime]
    _domain_events: List["DomainEvent"] = field(
        default_factory=list, repr=False, compare=False
    )

    @classmethod
    def create(
        cls,
        user_id: UUID,
        items: List[OrderItem],
        shipping_address: VerifiedAddress,
        cart_id: UUID,
        actor_id: str = "anonymous",
        order_id: Optional[UUID] = None,
    ) -> "Order":
        """
        Factory method to create a new Order.

        Args:
            user_id: The ID of the user who placed the order
            items: List of OrderItems (should be created via OrderItem.create())
            shipping_address: Verified shipping address for delivery
            cart_id: The ID of the cart this order was created from
            actor_id: ID of the actor creating the order
            order_id: Optional pre-generated order ID (used when OrderItems
                      need to reference the order ID before creation)
        """
        from domain.aggregates.order.events import OrderCreated

        order = cls(
            id=order_id if order_id is not None else uuid4(),
            user_id=user_id,
            items=list(items),  # Make a copy to avoid shared state
            shipping_address=shipping_address,
            submitted_at=datetime.now(),
        )

        order._raise_event(
            OrderCreated(
                order_id=order.id,
                cart_id=cart_id,
                total=order.get_total(),
                item_count=sum(item.quantity for item in order.items),
                actor_id=actor_id,
            )
        )

        return order

    def get_total(self) -> Decimal:
        return sum((item.get_subtotal() for item in self.items), Decimal("0"))

    def _raise_event(self, event: "DomainEvent") -> None:
        """Record a domain event."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List["DomainEvent"]:
        """Return all collected events."""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clear collected events after dispatch."""
        self._domain_events = []
