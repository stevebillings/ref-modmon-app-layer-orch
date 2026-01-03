from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID, uuid4

from domain.aggregates.order.entities import Order, OrderItem
from domain.exceptions import CartItemNotFoundError, EmptyCartError
from domain.validation import validate_positive_quantity


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
    items: List[CartItem] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

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

    def add_item(
        self,
        product_id: UUID,
        product_name: str,
        unit_price: Decimal,
        quantity: int,
    ) -> None:
        """
        Add an item to the cart, or merge if product already exists.

        Raises:
            ValidationError: If quantity is invalid
        """
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

    def update_item_quantity(self, product_id: UUID, quantity: int) -> int:
        """
        Update the quantity of an item in the cart.

        Returns:
            The quantity difference (new - old) for stock adjustment.

        Raises:
            CartItemNotFoundError: If item not in cart
            ValidationError: If quantity is invalid
        """
        validate_positive_quantity(quantity)
        item = self.get_item_by_product_id(product_id)

        if item is None:
            raise CartItemNotFoundError(str(product_id))

        diff = quantity - item.quantity
        new_item = item.with_quantity(quantity)
        self.items = [new_item if i.id == item.id else i for i in self.items]

        return diff

    def remove_item(self, product_id: UUID) -> CartItem:
        """
        Remove an item from the cart.

        Returns:
            The removed item (for stock release).

        Raises:
            CartItemNotFoundError: If item not in cart
        """
        item = self.get_item_by_product_id(product_id)

        if item is None:
            raise CartItemNotFoundError(str(product_id))

        self.items = [i for i in self.items if i.id != item.id]
        return item

    def submit(self) -> Order:
        """
        Create an Order from cart contents and clear the cart.

        Returns:
            The created Order.

        Raises:
            EmptyCartError: If cart has no items
        """
        if not self.items:
            raise EmptyCartError()

        order_id = uuid4()
        order_items = [
            OrderItem.create(
                order_id=order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
            )
            for item in self.items
        ]

        order = Order(id=order_id, items=order_items, submitted_at=None)
        self.items = []

        return order
