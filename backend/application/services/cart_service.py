from decimal import Decimal
from uuid import UUID, uuid4

from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.order.entities import Order, OrderItem
from domain.exceptions import (
    CartItemNotFoundError,
    EmptyCartError,
    InsufficientStockError,
    ProductNotFoundError,
)
from domain.validation import validate_cart_item_quantity
from infrastructure.django_app.unit_of_work import UnitOfWork


class CartService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_cart(self) -> Cart:
        """Get the current cart."""
        return self.uow.cart.get_cart()

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
        validate_cart_item_quantity(quantity)

        try:
            pid = UUID(product_id)
        except ValueError:
            raise ProductNotFoundError(product_id)

        # Use get_by_id_for_update to acquire a row-level lock, preventing
        # race conditions when multiple requests try to reserve stock concurrently
        product = self.uow.products.get_by_id_for_update(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        cart = self.uow.cart.get_cart()
        existing_item = cart.get_item_by_product_id(pid)

        if existing_item:
            # Adding to existing item
            new_quantity = existing_item.quantity + quantity
            additional_stock_needed = quantity

            if additional_stock_needed > product.stock_quantity:
                raise InsufficientStockError(
                    product.name, product.stock_quantity, additional_stock_needed
                )

            # Update cart item
            updated_item = existing_item.with_quantity(new_quantity)
            self.uow.cart.update_item(updated_item)

            # Reserve stock
            updated_product = product.with_stock_quantity(
                product.stock_quantity - additional_stock_needed
            )
            self.uow.products.save(updated_product)
        else:
            # New item
            if quantity > product.stock_quantity:
                raise InsufficientStockError(
                    product.name, product.stock_quantity, quantity
                )

            # Create cart item with snapshotted product data
            item = CartItem(
                id=uuid4(),
                product_id=pid,
                product_name=product.name,
                unit_price=product.price,
                quantity=quantity,
            )
            self.uow.cart.add_item(cart.id, item)

            # Reserve stock
            updated_product = product.with_stock_quantity(
                product.stock_quantity - quantity
            )
            self.uow.products.save(updated_product)

        return self.uow.cart.get_cart()

    def update_item_quantity(self, product_id: str, quantity: int) -> Cart:
        """
        Update the quantity of an item in the cart.

        Adjusts stock reservation accordingly.

        Raises:
            CartItemNotFoundError: If item not in cart
            ValidationError: If quantity is invalid
            InsufficientStockError: If increasing beyond available stock
        """
        validate_cart_item_quantity(quantity)

        try:
            pid = UUID(product_id)
        except ValueError:
            raise CartItemNotFoundError(product_id)

        cart = self.uow.cart.get_cart()
        item = cart.get_item_by_product_id(pid)

        if item is None:
            raise CartItemNotFoundError(product_id)

        # Use get_by_id_for_update to acquire a row-level lock, preventing
        # race conditions when multiple requests try to modify stock concurrently
        product = self.uow.products.get_by_id_for_update(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        quantity_diff = quantity - item.quantity

        if quantity_diff > 0:
            # Increasing quantity - need more stock
            if quantity_diff > product.stock_quantity:
                raise InsufficientStockError(
                    product.name, product.stock_quantity, quantity_diff
                )

        # Update cart item
        updated_item = item.with_quantity(quantity)
        self.uow.cart.update_item(updated_item)

        # Adjust stock
        new_stock = product.stock_quantity - quantity_diff
        updated_product = product.with_stock_quantity(new_stock)
        self.uow.products.save(updated_product)

        return self.uow.cart.get_cart()

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

        cart = self.uow.cart.get_cart()
        item = cart.get_item_by_product_id(pid)

        if item is None:
            raise CartItemNotFoundError(product_id)

        # Release stock - use get_by_id_for_update to acquire a row-level lock,
        # preventing race conditions when multiple requests try to release stock
        product = self.uow.products.get_by_id_for_update(pid)
        if product:
            updated_product = product.with_stock_quantity(
                product.stock_quantity + item.quantity
            )
            self.uow.products.save(updated_product)

        # Remove item
        self.uow.cart.delete_item(item.id)

        return self.uow.cart.get_cart()

    def submit_cart(self) -> Order:
        """
        Submit the cart as an order.

        Creates an immutable Order from cart contents and clears the cart.
        Stock remains decremented (was reserved when added to cart).

        Raises:
            EmptyCartError: If cart has no items
        """
        cart = self.uow.cart.get_cart()

        if not cart.items:
            raise EmptyCartError()

        # Create order
        order_id = uuid4()
        order_items = [
            OrderItem(
                id=uuid4(),
                order_id=order_id,
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
            )
            for item in cart.items
        ]

        order = Order(
            id=order_id,
            items=order_items,
            submitted_at=None,  # Will be set by repository
        )

        saved_order = self.uow.orders.save(order)

        # Clear cart
        self.uow.cart.clear_items(cart.id)

        return saved_order
