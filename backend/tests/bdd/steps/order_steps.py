"""Order-related step definitions."""

from decimal import Decimal
from typing import Any
from uuid import uuid4

from pytest_bdd import given, when, then, parsers

from application.services.cart_service import CartService
from application.services.order_service import OrderService
from application.services.product_service import ProductService
from domain.user_context import Role, UserContext
from tests.bdd.conftest import VALID_SHIPPING_ADDRESS


# ============================================================================
# GIVEN steps
# ============================================================================


@given(
    parsers.parse(
        'a customer "{username}" has submitted an order for "{product_name}" '
        'at "${price}" quantity {qty:d}'
    )
)
def customer_has_order(
    context: dict[str, Any],
    product_service: ProductService,
    cart_service: CartService,
    admin_user_context: UserContext,
    username: str,
    product_name: str,
    price: str,
    qty: int,
) -> None:
    """Create a customer and have them submit an order."""
    # Create the user context if not exists
    if username not in context["named_users"]:
        context["named_users"][username] = UserContext(
            user_id=uuid4(),
            username=username,
            role=Role.CUSTOMER,
        )
    user_context = context["named_users"][username]

    # Create product if not exists
    if product_name not in context["products"]:
        product = product_service.create_product(
            name=product_name,
            price=Decimal(price),
            stock_quantity=100,  # Enough stock for test
            user_context=admin_user_context,
        )
        context["products"][product_name] = product

    product = context["products"][product_name]

    # Add to cart and submit
    cart_service.add_item(str(product.id), quantity=qty, user_context=user_context)
    order = cart_service.submit_cart(user_context, shipping_address=VALID_SHIPPING_ADDRESS)
    context["orders"].append(order)


@given("I have no previous orders")
def no_previous_orders(context: dict[str, Any]) -> None:
    """Placeholder - new user contexts don't have orders by default."""
    pass


# ============================================================================
# WHEN steps
# ============================================================================


@when(parsers.parse('I am logged in as customer "{username}"'))
def when_logged_in_as_customer(context: dict[str, Any], username: str) -> None:
    """Log in as a specific customer."""
    if username not in context["named_users"]:
        context["named_users"][username] = UserContext(
            user_id=uuid4(),
            username=username,
            role=Role.CUSTOMER,
        )
    context["current_user_context"] = context["named_users"][username]


@when("I am logged in as an Admin")
def when_logged_in_as_admin(
    context: dict[str, Any], admin_user_context: UserContext
) -> None:
    """Log in as admin."""
    context["current_user_context"] = admin_user_context


@when("I view my orders")
def view_my_orders(context: dict[str, Any], order_service: OrderService) -> None:
    """View orders for current user."""
    orders = order_service.get_orders(context["current_user_context"])
    context["viewed_orders"] = orders


@when("I view all orders")
def view_all_orders(context: dict[str, Any], order_service: OrderService) -> None:
    """View all orders (admin)."""
    orders = order_service.get_orders(context["current_user_context"])
    context["viewed_orders"] = orders


# ============================================================================
# THEN steps
# ============================================================================


@then(parsers.parse("I should see {count:d} order"))
def should_see_order_count_singular(context: dict[str, Any], count: int) -> None:
    """Verify number of orders visible (singular)."""
    viewed = context.get("viewed_orders", [])
    assert len(viewed) == count, f"Expected {count} order, got {len(viewed)}"


@then(parsers.parse("I should see {count:d} orders"))
def should_see_order_count_plural(context: dict[str, Any], count: int) -> None:
    """Verify number of orders visible (plural)."""
    viewed = context.get("viewed_orders", [])
    assert len(viewed) == count, f"Expected {count} orders, got {len(viewed)}"


@then(parsers.parse('the order should contain "{product_name}" quantity {qty:d}'))
def order_should_contain_quantity(
    context: dict[str, Any], product_name: str, qty: int
) -> None:
    """Verify order contains item with expected quantity."""
    viewed = context.get("viewed_orders", [])
    assert len(viewed) > 0, "No orders found"

    # Find the order with this product
    for order in viewed:
        item = next((i for i in order.items if i.product_name == product_name), None)
        if item:
            assert (
                item.quantity == qty
            ), f"Expected quantity {qty}, got {item.quantity}"
            return

    assert False, f"No order found containing '{product_name}'"


@then(parsers.parse('the order should contain "{product_name}" at "${price}" each'))
def viewed_order_should_contain_item_price(
    context: dict[str, Any], product_name: str, price: str
) -> None:
    """Verify order in viewed orders contains item with expected price."""
    viewed = context.get("viewed_orders", [])
    assert len(viewed) > 0, "No orders found"

    # Find the order with this product
    for order in viewed:
        item = next((i for i in order.items if i.product_name == product_name), None)
        if item:
            assert (
                item.unit_price == Decimal(price)
            ), f"Expected price ${price}, got ${item.unit_price}"
            return

    assert False, f"No order found containing '{product_name}'"
