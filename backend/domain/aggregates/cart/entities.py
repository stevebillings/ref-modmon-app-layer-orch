from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List
from uuid import UUID, uuid4

from domain.exceptions import CartItemNotFoundError, EmptyCartError
from domain.validation import validate_positive_quantity

if TYPE_CHECKING:
    from domain.events import DomainEvent


@dataclass(frozen=True)
class CartItem:
    """
    Immutable value object representing an item in a cart.

    Snapshots product data (name, price) at the time of adding to cart.
    """

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
            quantity=validate_positive_quantity(quantity),
        )

    def get_subtotal(self) -> Decimal:
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
            quantity=validate_positive_quantity(new_quantity),
        )


@dataclass
class Cart:
    """
    Cart aggregate root.

    Mutable aggregate that manages cart items. Use create() factory for new carts.
    Use constructor directly for reconstitution from persistence.
    """

    id: UUID
    user_id: UUID
    items: List[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    _domain_events: List["DomainEvent"] = field(
        default_factory=list, repr=False, compare=False
    )

    @classmethod
    def create(cls, user_id: UUID) -> "Cart":
        """Factory method to create a new empty Cart for a user."""
        return cls(
            id=uuid4(),
            user_id=user_id,
            items=[],
            created_at=datetime.now(),
        )

    def get_total(self) -> Decimal:
        return sum((item.get_subtotal() for item in self.items), Decimal("0"))

    def get_item_count(self) -> int:
        return sum(item.quantity for item in self.items)

    def get_item_by_product_id(self, product_id: UUID) -> CartItem | None:
        """Find a cart item by product ID."""
        for item in self.items:
            if item.product_id == product_id:
                return item
        return None

    def add_item(
        self,
        product_id: UUID,
        product_name: str,
        unit_price: Decimal,
        quantity: int,
        actor_id: str = "anonymous",
    ) -> None:
        """
        Add an item to the cart, or merge if product already exists.

        Raises:
            ValidationError: If quantity is invalid
        """
        from domain.aggregates.cart.events import CartItemAdded

        validate_positive_quantity(quantity)
        existing = self.get_item_by_product_id(product_id)

        if existing:
            # Merge: replace with updated quantity
            new_quantity = existing.quantity + quantity
            new_item = existing.with_quantity(new_quantity)
            self.items = [
                new_item if i.id == existing.id else i for i in self.items
            ]
        else:
            # Add new item
            new_item = CartItem.create(
                product_id, product_name, unit_price, quantity
            )
            self.items.append(new_item)

        self._raise_event(
            CartItemAdded(
                cart_id=self.id,
                product_id=product_id,
                product_name=product_name,
                quantity=quantity,
                unit_price=unit_price,
                actor_id=actor_id,
            )
        )

    def update_item_quantity(
        self,
        product_id: UUID,
        quantity: int,
        actor_id: str = "anonymous",
    ) -> int:
        """
        Update the quantity of an item in the cart.

        Returns:
            The quantity difference (new - old) for stock adjustment.

        Raises:
            CartItemNotFoundError: If item not in cart
            ValidationError: If quantity is invalid
        """
        from domain.aggregates.cart.events import CartItemQuantityUpdated

        validate_positive_quantity(quantity)
        item = self.get_item_by_product_id(product_id)

        if item is None:
            raise CartItemNotFoundError(str(product_id))

        old_quantity = item.quantity
        diff = quantity - old_quantity
        new_item = item.with_quantity(quantity)
        self.items = [new_item if i.id == item.id else i for i in self.items]

        self._raise_event(
            CartItemQuantityUpdated(
                cart_id=self.id,
                product_id=product_id,
                product_name=item.product_name,
                old_quantity=old_quantity,
                new_quantity=quantity,
                actor_id=actor_id,
            )
        )

        return diff

    def remove_item(
        self,
        product_id: UUID,
        actor_id: str = "anonymous",
    ) -> CartItem:
        """
        Remove an item from the cart.

        Returns:
            The removed item (for stock release).

        Raises:
            CartItemNotFoundError: If item not in cart
        """
        from domain.aggregates.cart.events import CartItemRemoved

        item = self.get_item_by_product_id(product_id)

        if item is None:
            raise CartItemNotFoundError(str(product_id))

        self.items = [i for i in self.items if i.id != item.id]

        self._raise_event(
            CartItemRemoved(
                cart_id=self.id,
                product_id=product_id,
                product_name=item.product_name,
                quantity_removed=item.quantity,
                actor_id=actor_id,
            )
        )

        return item

    def submit(
        self,
        actor_id: str = "anonymous",
    ) -> List[CartItem]:
        """
        Submit the cart by clearing items and returning them for order creation.

        The application layer is responsible for creating the Order from the
        returned items. This maintains aggregate isolation - Cart doesn't know
        about Order internals.

        Args:
            actor_id: ID of the actor performing the action

        Returns:
            List of CartItems that were in the cart (for order creation).

        Raises:
            EmptyCartError: If cart has no items
        """
        from domain.aggregates.cart.events import CartSubmitted

        if not self.items:
            raise EmptyCartError()

        total = self.get_total()
        item_count = self.get_item_count()

        # Capture items before clearing
        submitted_items = list(self.items)
        self.items = []

        self._raise_event(
            CartSubmitted(
                cart_id=self.id,
                total=total,
                item_count=item_count,
                actor_id=actor_id,
            )
        )

        return submitted_items

    def _raise_event(self, event: "DomainEvent") -> None:
        """Record a domain event."""
        self._domain_events.append(event)

    def get_domain_events(self) -> List["DomainEvent"]:
        """Return all collected events."""
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        """Clear collected events after dispatch."""
        self._domain_events = []
