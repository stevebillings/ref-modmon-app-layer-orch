from uuid import UUID, uuid4

from application.ports.address_verification import (
    AddressVerificationPort,
    AddressVerificationResult,
    VerificationStatus,
)
from application.ports.metrics import MetricsPort, NoOpMetrics
from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.cart.entities import Cart
from domain.aggregates.order.entities import Order, OrderItem
from domain.aggregates.order.value_objects import UnverifiedAddress, VerifiedAddress
from domain.exceptions import (
    AddressVerificationError,
    CartItemNotFoundError,
    InsufficientStockError,
    ProductNotFoundError,
)
from domain.user_context import UserContext


class CartService:
    """
    Application service for cart operations.

    Thin orchestration layer that coordinates between Cart and Product aggregates.
    Business logic is encapsulated in the aggregates; this service handles:
    - Cross-aggregate coordination (stock availability checking)
    - Persistence via repositories
    - Concurrency control (pessimistic locking)
    - Event collection for dispatch after commit
    - User context for cart ownership and audit logging
    - Address verification for order submission
    """

    def __init__(
        self,
        uow: UnitOfWork,
        address_verification: AddressVerificationPort | None = None,
        metrics: MetricsPort | None = None,
    ):
        self.uow = uow
        self.address_verification = address_verification
        self.metrics = metrics or NoOpMetrics()

    def get_cart(self, user_context: UserContext) -> Cart:
        """Get the cart for the authenticated user."""
        return self.uow.get_cart_repository().get_cart_for_user(user_context.user_id)

    def add_item(
        self, product_id: str, quantity: int, user_context: UserContext
    ) -> Cart:
        """
        Add an item to the user's cart.

        If the product is already in the cart, increases the quantity.
        Reserves stock immediately (decrements product's stock_quantity).

        Raises:
            ProductNotFoundError: If product doesn't exist
            ValidationError: If quantity is invalid
            InsufficientStockError: If not enough stock available
        """
        with self.metrics.time_operation("cart_add_item"):
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
            cart = self.uow.get_cart_repository().get_cart_for_user(user_context.user_id)
            cart.add_item(
                pid, product.name, product.price, quantity, actor_id=user_context.actor_id
            )
            product.reserve_stock(quantity, actor_id=user_context.actor_id)

            # Persist both aggregates
            self.uow.get_cart_repository().save(cart)
            self.uow.get_product_repository().save(product)

            # Collect events from modified aggregates
            self.uow.collect_events_from(cart)
            self.uow.collect_events_from(product)

            return cart

    def update_item_quantity(
        self, product_id: str, quantity: int, user_context: UserContext
    ) -> Cart:
        """
        Update the quantity of an item in the user's cart.

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

        cart = self.uow.get_cart_repository().get_cart_for_user(user_context.user_id)

        # Check item exists before acquiring product lock
        if cart.get_item_by_product_id(pid) is None:
            raise CartItemNotFoundError(product_id)

        # Acquire row-level lock for stock modification
        product = self.uow.get_product_repository().get_by_id_for_update(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        # Delegate to cart aggregate - returns quantity difference
        diff = cart.update_item_quantity(pid, quantity, actor_id=user_context.actor_id)

        # Adjust stock based on difference
        if diff > 0:
            # Increasing quantity - need more stock
            if not product.has_sufficient_stock(diff):
                raise InsufficientStockError(
                    product.name, product.stock_quantity, diff
                )
            product.reserve_stock(diff, actor_id=user_context.actor_id)
        elif diff < 0:
            # Decreasing quantity - release stock
            product.release_stock(-diff, actor_id=user_context.actor_id)

        # Persist both aggregates
        self.uow.get_cart_repository().save(cart)
        self.uow.get_product_repository().save(product)

        # Collect events from modified aggregates
        self.uow.collect_events_from(cart)
        self.uow.collect_events_from(product)

        return cart

    def remove_item(self, product_id: str, user_context: UserContext) -> Cart:
        """
        Remove an item from the user's cart.

        Releases reserved stock.

        Raises:
            CartItemNotFoundError: If item not in cart
        """
        with self.metrics.time_operation("cart_remove_item"):
            try:
                pid = UUID(product_id)
            except ValueError:
                raise CartItemNotFoundError(product_id)

            cart = self.uow.get_cart_repository().get_cart_for_user(user_context.user_id)

            # Delegate to cart aggregate - returns removed item for stock release
            removed_item = cart.remove_item(pid, actor_id=user_context.actor_id)

            # Acquire row-level lock and release stock
            product = self.uow.get_product_repository().get_by_id_for_update(pid)
            if product:
                product.release_stock(removed_item.quantity, actor_id=user_context.actor_id)
                self.uow.get_product_repository().save(product)
                self.uow.collect_events_from(product)

            # Persist cart
            self.uow.get_cart_repository().save(cart)
            self.uow.collect_events_from(cart)

            return cart

    def verify_address(
        self,
        address: UnverifiedAddress,
    ) -> tuple[VerifiedAddress, AddressVerificationResult]:
        """
        Verify a shipping address using the address verification service.

        Args:
            address: The unverified address to check

        Returns:
            Tuple of (VerifiedAddress, AddressVerificationResult)

        Raises:
            AddressVerificationError: If verification fails or service unavailable
            RuntimeError: If address verification port not configured
        """
        if self.address_verification is None:
            raise RuntimeError("Address verification service not configured")

        result = self.address_verification.verify(
            street_line_1=address.street_line_1,
            street_line_2=address.street_line_2,
            city=address.city,
            state=address.state,
            postal_code=address.postal_code,
            country=address.country,
        )

        if result.status == VerificationStatus.SERVICE_UNAVAILABLE:
            raise AddressVerificationError(
                result.error_message or "Service unavailable"
            )

        if result.status in (VerificationStatus.INVALID, VerificationStatus.UNDELIVERABLE):
            field = None
            if result.field_errors:
                field = next(iter(result.field_errors.keys()), None)
            raise AddressVerificationError(
                result.error_message or "Invalid address",
                field=field,
            )

        verified = VerifiedAddress.from_unverified(
            original=address,
            standardized=result.standardized_address or {},
            verification_id=result.verification_id or "",
        )

        return verified, result

    def submit_cart(
        self,
        user_context: UserContext,
        shipping_address: UnverifiedAddress,
    ) -> Order:
        """
        Submit the user's cart as an order.

        Orchestrates cross-aggregate operation:
        1. Verifies the shipping address
        2. Submits the cart (clears items, returns them for order creation)
        3. Creates an Order from the cart items
        4. Persists both aggregates

        Stock remains decremented (was reserved when added to cart).

        Args:
            user_context: The authenticated user context
            shipping_address: The shipping address (will be verified)

        Raises:
            EmptyCartError: If cart has no items
            AddressVerificationError: If address verification fails
        """
        with self.metrics.time_operation("cart_submit"):
            # Verify address first (fail fast before modifying cart)
            verified_address, _ = self.verify_address(shipping_address)

            cart = self.uow.get_cart_repository().get_cart_for_user(user_context.user_id)

            # Submit cart - returns items for order creation and clears cart
            cart_items = cart.submit(actor_id=user_context.actor_id)

            # Application layer orchestrates Order creation from cart items
            # Generate order_id first so OrderItems can reference it
            order_id = uuid4()
            order_items = [
                OrderItem.create(
                    order_id=order_id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                )
                for item in cart_items
            ]

            order = Order(
                id=order_id,
                user_id=user_context.user_id,
                items=order_items,
                shipping_address=verified_address,
                submitted_at=None,
            )

            # Persist order and cleared cart
            saved_order = self.uow.get_order_repository().save(order)
            self.uow.get_cart_repository().save(cart)

            # Collect events from cart (includes CartSubmitted event)
            self.uow.collect_events_from(cart)

            return saved_order
