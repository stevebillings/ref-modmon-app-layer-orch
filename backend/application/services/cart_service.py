from uuid import UUID

from domain.aggregates.cart.entities import Cart
from domain.aggregates.order.entities import Order
from domain.exceptions import (
    CartItemNotFoundError,
    InsufficientStockError,
    ProductNotFoundError,
)
from infrastructure.django_app.unit_of_work import UnitOfWork


class CartService:
    """
    Application service for cart operations.

    Thin orchestration layer that coordinates between Cart and Product aggregates.
    Business logic is encapsulated in the aggregates; this service handles:
    - Cross-aggregate coordination (stock availability checking)
    - Persistence via repositories
    - Concurrency control (pessimistic locking)
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_cart(self) -> Cart:
        """Get the current cart."""
        return self.uow.get_cart_repository().get_cart()

    def add_item(self, product_id: str, quantity: int) -> Cart:
        """
        Add an item to the cart.

        If the product is already in the cart, increases the quantity.
        Reserves stock immediately (decrements product's stock_quantity).

        Raises:
            ProductNotFoundError: If product doesn't exist
            ValidationError: If quantity is invalid
            InsufficientStockError: If not enough stock available
        """
        try:
            pid = UUID(product_id)
        except ValueError:
            raise ProductNotFoundError(product_id)

        # Acquire row-level lock to prevent concurrent stock modifications
        product = self.uow.get_product_repository().get_by_id_for_update(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        # Check stock availability (cross-aggregate concern handled by service)
        if not product.has_sufficient_stock(quantity):
            raise InsufficientStockError(
                product.name, product.stock_quantity, quantity
            )

        # Delegate to aggregates
        cart = self.uow.get_cart_repository().get_cart()
        cart.add_item(pid, product.name, product.price, quantity)
        product.reserve_stock(quantity)

        # Persist both aggregates
        self.uow.get_cart_repository().save(cart)
        self.uow.get_product_repository().save(product)

        return cart

    def update_item_quantity(self, product_id: str, quantity: int) -> Cart:
        """
        Update the quantity of an item in the cart.

        Adjusts stock reservation accordingly.

        Raises:
            CartItemNotFoundError: If item not in cart
            ValidationError: If quantity is invalid
            InsufficientStockError: If increasing beyond available stock
        """
        try:
            pid = UUID(product_id)
        except ValueError:
            raise CartItemNotFoundError(product_id)

        cart = self.uow.get_cart_repository().get_cart()

        # Check item exists before acquiring product lock
        if cart.get_item_by_product_id(pid) is None:
            raise CartItemNotFoundError(product_id)

        # Acquire row-level lock for stock modification
        product = self.uow.get_product_repository().get_by_id_for_update(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        # Delegate to cart aggregate - returns quantity difference
        diff = cart.update_item_quantity(pid, quantity)

        # Adjust stock based on difference
        if diff > 0:
            # Increasing quantity - need more stock
            if not product.has_sufficient_stock(diff):
                raise InsufficientStockError(
                    product.name, product.stock_quantity, diff
                )
            product.reserve_stock(diff)
        elif diff < 0:
            # Decreasing quantity - release stock
            product.release_stock(-diff)

        # Persist both aggregates
        self.uow.get_cart_repository().save(cart)
        self.uow.get_product_repository().save(product)

        return cart

    def remove_item(self, product_id: str) -> Cart:
        """
        Remove an item from the cart.

        Releases reserved stock.

        Raises:
            CartItemNotFoundError: If item not in cart
        """
        try:
            pid = UUID(product_id)
        except ValueError:
            raise CartItemNotFoundError(product_id)

        cart = self.uow.get_cart_repository().get_cart()

        # Delegate to cart aggregate - returns removed item for stock release
        removed_item = cart.remove_item(pid)

        # Acquire row-level lock and release stock
        product = self.uow.get_product_repository().get_by_id_for_update(pid)
        if product:
            product.release_stock(removed_item.quantity)
            self.uow.get_product_repository().save(product)

        # Persist cart
        self.uow.get_cart_repository().save(cart)

        return cart

    def submit_cart(self) -> Order:
        """
        Submit the cart as an order.

        Creates an immutable Order from cart contents and clears the cart.
        Stock remains decremented (was reserved when added to cart).

        Raises:
            EmptyCartError: If cart has no items
        """
        cart = self.uow.get_cart_repository().get_cart()

        # Delegate to cart aggregate - creates order and clears cart
        order = cart.submit()

        # Persist order and cleared cart
        saved_order = self.uow.get_order_repository().save(order)
        self.uow.get_cart_repository().save(cart)

        return saved_order
