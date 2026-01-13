"""Cart-related step definitions."""

from decimal import Decimal
from typing import Any, Dict, List
from uuid import uuid4

from pytest_bdd import given, when, then, parsers

from application.services.cart_service import CartService
from domain.aggregates.order.value_objects import UnverifiedAddress
from tests.bdd.conftest import VALID_SHIPPING_ADDRESS, INVALID_SHIPPING_ADDRESS


# ============================================================================
# GIVEN steps
# ============================================================================


@given(parsers.parse('my cart contains {qty:d} "{product_name}"'))
def cart_contains_items(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    qty: int,
) -> None:
    """Add items to the current user's cart."""
    product = context["products"][product_name]
    cart_service.add_item(
        str(product.id),
        quantity=qty,
        user_context=context["current_user_context"],
    )


@given("my cart is empty")
def cart_is_empty(context: Dict[str, Any], cart_service: CartService) -> None:
    """Ensure the cart is empty by removing all items."""
    cart = cart_service.get_cart(context["current_user_context"])
    for item in list(cart.items):
        cart_service.remove_item(
            str(item.product_id),
            user_context=context["current_user_context"],
        )


@given(parsers.parse('I add {qty:d} "{product_name}" to my cart'))
def add_to_cart_given(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    qty: int,
) -> None:
    """Add items to cart (Given clause version)."""
    product = context["products"][product_name]
    cart_service.add_item(
        str(product.id),
        quantity=qty,
        user_context=context["current_user_context"],
    )


@given("I have a valid shipping address:")
def have_valid_shipping_address(
    context: Dict[str, Any], datatable: List[List[str]]
) -> None:
    """Set up a valid shipping address from the datatable."""
    # pytest-bdd returns datatable as list of lists, first row is headers
    headers = datatable[0]
    values = datatable[1]
    row = dict(zip(headers, values))
    context["shipping_address"] = UnverifiedAddress(
        street_line_1=row["street_line_1"],
        street_line_2=row.get("street_line_2"),
        city=row["city"],
        state=row["state"],
        postal_code=row["postal_code"],
        country=row["country"],
    )


@given("I have an invalid shipping address:")
def have_invalid_shipping_address(
    context: Dict[str, Any], datatable: List[List[str]]
) -> None:
    """Set up an invalid shipping address from the datatable."""
    # pytest-bdd returns datatable as list of lists, first row is headers
    headers = datatable[0]
    values = datatable[1]
    row = dict(zip(headers, values))
    context["shipping_address"] = UnverifiedAddress(
        street_line_1=row["street_line_1"],
        street_line_2=row.get("street_line_2"),
        city=row["city"],
        state=row["state"],
        postal_code=row["postal_code"],
        country=row["country"],
    )


# ============================================================================
# WHEN steps
# ============================================================================


@when(parsers.parse('I add {qty:d} "{product_name}" to my cart'))
def add_to_cart(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    qty: int,
) -> None:
    """Add items to cart (expected to succeed)."""
    product = context["products"][product_name]
    cart_service.add_item(
        str(product.id),
        quantity=qty,
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I try to add {qty:d} "{product_name}" to my cart'))
def try_add_to_cart(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    qty: int,
) -> None:
    """Try to add items to cart (may fail)."""
    try:
        product = context["products"].get(product_name)
        if product is None:
            # Product doesn't exist - use a fake ID
            cart_service.add_item(
                str(uuid4()),
                quantity=qty,
                user_context=context["current_user_context"],
            )
        else:
            cart_service.add_item(
                str(product.id),
                quantity=qty,
                user_context=context["current_user_context"],
            )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I update "{product_name}" quantity to {qty:d}'))
def update_cart_quantity(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    qty: int,
) -> None:
    """Update item quantity in cart (expected to succeed)."""
    product = context["products"][product_name]
    cart_service.update_item_quantity(
        str(product.id),
        quantity=qty,
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I try to update "{product_name}" quantity to {qty:d}'))
def try_update_cart_quantity(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    qty: int,
) -> None:
    """Try to update item quantity (may fail)."""
    try:
        product = context["products"].get(product_name)
        if product is None:
            cart_service.update_item_quantity(
                str(uuid4()),
                quantity=qty,
                user_context=context["current_user_context"],
            )
        else:
            cart_service.update_item_quantity(
                str(product.id),
                quantity=qty,
                user_context=context["current_user_context"],
            )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I remove "{product_name}" from my cart'))
def remove_from_cart(
    context: Dict[str, Any], cart_service: CartService, product_name: str
) -> None:
    """Remove item from cart (expected to succeed)."""
    product = context["products"][product_name]
    cart_service.remove_item(
        str(product.id),
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I try to remove "{product_name}" from my cart'))
def try_remove_from_cart(
    context: Dict[str, Any], cart_service: CartService, product_name: str
) -> None:
    """Try to remove item from cart (may fail)."""
    try:
        product = context["products"].get(product_name)
        if product is None:
            cart_service.remove_item(
                str(uuid4()),
                user_context=context["current_user_context"],
            )
        else:
            cart_service.remove_item(
                str(product.id),
                user_context=context["current_user_context"],
            )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when("I submit my cart")
def submit_cart(context: Dict[str, Any], cart_service: CartService) -> None:
    """Submit cart (expected to succeed)."""
    address = context.get("shipping_address", VALID_SHIPPING_ADDRESS)
    order = cart_service.submit_cart(
        context["current_user_context"],
        shipping_address=address,
    )
    context["orders"].append(order)


@when("I try to submit my cart")
def try_submit_cart(context: Dict[str, Any], cart_service: CartService) -> None:
    """Try to submit cart (may fail)."""
    try:
        address = context.get("shipping_address", VALID_SHIPPING_ADDRESS)
        order = cart_service.submit_cart(
            context["current_user_context"],
            shipping_address=address,
        )
        context["orders"].append(order)
        context["error"] = None
    except Exception as e:
        context["error"] = e


# ============================================================================
# THEN steps
# ============================================================================


@then(
    parsers.parse('my cart should contain {qty:d} "{product_name}" at "${price}" each')
)
def cart_should_contain_with_price(
    context: Dict[str, Any],
    cart_service: CartService,
    qty: int,
    product_name: str,
    price: str,
) -> None:
    """Verify cart contains item with expected quantity and price."""
    cart = cart_service.get_cart(context["current_user_context"])
    item = next((i for i in cart.items if i.product_name == product_name), None)
    assert item is not None, f"Item '{product_name}' not found in cart"
    assert item.quantity == qty, f"Expected quantity {qty}, got {item.quantity}"
    assert (
        item.unit_price == Decimal(price)
    ), f"Expected price ${price}, got ${item.unit_price}"


@then(parsers.parse('my cart should contain {qty:d} "{product_name}"'))
def cart_should_contain(
    context: Dict[str, Any],
    cart_service: CartService,
    qty: int,
    product_name: str,
) -> None:
    """Verify cart contains item with expected quantity."""
    cart = cart_service.get_cart(context["current_user_context"])
    item = next((i for i in cart.items if i.product_name == product_name), None)
    assert item is not None, f"Item '{product_name}' not found in cart"
    assert item.quantity == qty, f"Expected quantity {qty}, got {item.quantity}"


@then("my cart should be empty")
def cart_should_be_empty(context: Dict[str, Any], cart_service: CartService) -> None:
    """Verify cart has no items."""
    cart = cart_service.get_cart(context["current_user_context"])
    assert len(cart.items) == 0, f"Cart should be empty but has {len(cart.items)} items"


@then(
    parsers.parse('my cart item "{product_name}" should still show "${price}" per unit')
)
def cart_item_should_show_price(
    context: Dict[str, Any],
    cart_service: CartService,
    product_name: str,
    price: str,
) -> None:
    """Verify cart item retains original snapshot price."""
    cart = cart_service.get_cart(context["current_user_context"])
    item = next((i for i in cart.items if i.product_name == product_name), None)
    assert item is not None, f"Item '{product_name}' not found in cart"
    assert (
        item.unit_price == Decimal(price)
    ), f"Expected price ${price}, got ${item.unit_price}"


@then(
    parsers.parse(
        'an order should be created with {item_count:d} items totaling "${total}"'
    )
)
def order_should_be_created_plural(
    context: Dict[str, Any], item_count: int, total: str
) -> None:
    """Verify order was created with expected item count and total (plural)."""
    assert len(context["orders"]) > 0, "No order was created"
    order = context["orders"][-1]
    assert (
        len(order.items) == item_count
    ), f"Expected {item_count} items, got {len(order.items)}"
    assert (
        order.get_total() == Decimal(total)
    ), f"Expected total ${total}, got ${order.get_total()}"


@then(
    parsers.parse(
        'an order should be created with {item_count:d} item totaling "${total}"'
    )
)
def order_should_be_created_singular(
    context: Dict[str, Any], item_count: int, total: str
) -> None:
    """Verify order was created with expected item count and total (singular)."""
    order_should_be_created_plural(context, item_count, total)


@then("the order should have a verified shipping address")
def order_should_have_verified_address(context: Dict[str, Any]) -> None:
    """Verify order has a verified shipping address."""
    assert len(context["orders"]) > 0, "No order was created"
    order = context["orders"][-1]
    assert order.shipping_address is not None, "Order has no shipping address"
    assert order.shipping_address.verification_id, "Address is not verified"


@then(parsers.parse('the order should contain "{product_name}" at "${price}" each'))
def order_should_contain_item(
    context: Dict[str, Any], product_name: str, price: str
) -> None:
    """Verify order contains item with expected price."""
    assert len(context["orders"]) > 0, "No order was created"
    order = context["orders"][-1]
    item = next((i for i in order.items if i.product_name == product_name), None)
    assert item is not None, f"Item '{product_name}' not found in order"
    assert (
        item.unit_price == Decimal(price)
    ), f"Expected price ${price}, got ${item.unit_price}"
