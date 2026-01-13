"""Product-related step definitions."""

from decimal import Decimal
from typing import Any, Dict

from pytest_bdd import given, when, then, parsers

from application.services.product_service import ProductService
from domain.user_context import UserContext


# ============================================================================
# GIVEN steps
# ============================================================================


@given(parsers.parse('the product "{name}" has been deleted'))
def product_has_been_deleted(
    context: Dict[str, Any],
    product_service: ProductService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Mark a product as deleted."""
    product = context["products"].get(name)
    if product:
        product_service.delete_product(str(product.id), admin_user_context)


# ============================================================================
# WHEN steps
# ============================================================================


@when(
    parsers.parse(
        'I create a product with name "{name}" price "${price}" and stock quantity {qty:d}'
    )
)
def create_product(
    context: Dict[str, Any],
    product_service: ProductService,
    name: str,
    price: str,
    qty: int,
) -> None:
    """Create a product (expected to succeed)."""
    product = product_service.create_product(
        name=name,
        price=Decimal(price),
        stock_quantity=qty,
        user_context=context["current_user_context"],
    )
    context["products"][name] = product


@when(
    parsers.parse(
        'I try to create a product with name "{name}" price "${price}" and stock quantity {qty:d}'
    )
)
def try_create_product(
    context: Dict[str, Any],
    product_service: ProductService,
    name: str,
    price: str,
    qty: int,
) -> None:
    """Try to create a product (may fail)."""
    try:
        product = product_service.create_product(
            name=name,
            price=Decimal(price),
            stock_quantity=qty,
            user_context=context["current_user_context"],
        )
        context["products"][name] = product
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when('I try to create a product with name "" price "$29.99" and stock quantity 100')
def try_create_product_empty_name(
    context: Dict[str, Any], product_service: ProductService
) -> None:
    """Try to create a product with empty name."""
    try:
        product_service.create_product(
            name="",
            price=Decimal("29.99"),
            stock_quantity=100,
            user_context=context["current_user_context"],
        )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I delete the product "{name}"'))
def delete_product(
    context: Dict[str, Any], product_service: ProductService, name: str
) -> None:
    """Delete a product (expected to succeed)."""
    product = context["products"][name]
    product_service.delete_product(str(product.id), context["current_user_context"])


@when(parsers.parse('I try to delete the product "{name}"'))
def try_delete_product(
    context: Dict[str, Any], product_service: ProductService, name: str
) -> None:
    """Try to delete a product (may fail)."""
    try:
        product = context["products"][name]
        product_service.delete_product(str(product.id), context["current_user_context"])
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I restore the product "{name}"'))
def restore_product(
    context: Dict[str, Any], product_service: ProductService, name: str
) -> None:
    """Restore a deleted product."""
    product = context["products"][name]
    restored = product_service.restore_product(
        str(product.id), context["current_user_context"]
    )
    context["products"][name] = restored


@when(parsers.parse('the product "{name}" price changes to "${new_price}"'))
def change_product_price(
    context: Dict[str, Any], name: str, new_price: str
) -> None:
    """Change a product's price (simulating external update)."""
    product = context["products"][name]
    # Get fresh product and update price directly in DB for test
    from infrastructure.django_app.models import ProductModel

    ProductModel.objects.filter(id=product.id).update(price=Decimal(new_price))


@when(parsers.parse('the product "{name}" is soft-deleted'))
def soft_delete_product(
    context: Dict[str, Any],
    product_service: ProductService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Soft-delete a product after other operations."""
    product = context["products"][name]
    product_service.delete_product(str(product.id), admin_user_context)


# ============================================================================
# THEN steps
# ============================================================================


@then(parsers.parse('the product "{name}" should exist'))
def product_should_exist(product_service: ProductService, name: str) -> None:
    """Verify a product exists in the catalog."""
    products = product_service.get_all_products()
    assert any(p.name == name for p in products), f"Product '{name}' not found"


@then(parsers.parse('the product "{name}" should have price "${expected_price}"'))
def product_should_have_price(
    product_service: ProductService, name: str, expected_price: str
) -> None:
    """Verify a product has the expected price."""
    products = product_service.get_all_products()
    product = next((p for p in products if p.name == name), None)
    assert product is not None, f"Product '{name}' not found"
    assert (
        product.price == Decimal(expected_price)
    ), f"Expected price ${expected_price}, got ${product.price}"


@then(parsers.parse('the product "{name}" should have stock quantity {expected_qty:d}'))
def product_should_have_stock(
    context: Dict[str, Any],
    product_service: ProductService,
    name: str,
    expected_qty: int,
) -> None:
    """Verify a product has the expected stock quantity."""
    # Get fresh data including deleted products (for completeness)
    result = product_service.get_products_paginated(
        include_deleted=True,
        user_context=context.get("current_user_context"),
    )
    product = next((p for p in result.items if p.name == name), None)
    assert product is not None, f"Product '{name}' not found"
    assert (
        product.stock_quantity == expected_qty
    ), f"Expected stock {expected_qty}, got {product.stock_quantity}"


@then(parsers.parse('the product "{name}" should be marked as deleted'))
def product_should_be_deleted(
    context: Dict[str, Any],
    product_service: ProductService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a product is soft-deleted."""
    result = product_service.get_products_paginated(
        include_deleted=True,
        user_context=admin_user_context,
    )
    product = next((p for p in result.items if p.name == name), None)
    assert product is not None, f"Product '{name}' not found"
    assert product.is_deleted, f"Product '{name}' should be deleted"


@then(parsers.parse('the product "{name}" should not appear in the product catalog'))
def product_should_not_appear_in_catalog(
    product_service: ProductService, name: str
) -> None:
    """Verify a product is not visible in the regular catalog."""
    products = product_service.get_all_products()
    assert not any(
        p.name == name for p in products
    ), f"Product '{name}' should not appear in catalog"


@then(
    parsers.parse('the product "{name}" should appear when including deleted products')
)
def product_should_appear_when_including_deleted(
    product_service: ProductService, admin_user_context: UserContext, name: str
) -> None:
    """Verify a deleted product appears when including deleted."""
    result = product_service.get_products_paginated(
        include_deleted=True,
        user_context=admin_user_context,
    )
    assert any(
        p.name == name for p in result.items
    ), f"Product '{name}' should appear when including deleted"


@then(parsers.parse('the product "{name}" should appear in the product catalog'))
def product_should_appear_in_catalog(
    product_service: ProductService, name: str
) -> None:
    """Verify a product is visible in the catalog."""
    products = product_service.get_all_products()
    assert any(
        p.name == name for p in products
    ), f"Product '{name}' should appear in catalog"


@then(parsers.parse('I should receive a "{error_type}"'))
def should_receive_error(context: Dict[str, Any], error_type: str) -> None:
    """Verify that a specific error was raised."""
    assert context["error"] is not None, f"Expected {error_type} but no error occurred"
    actual_type = type(context["error"]).__name__
    assert (
        actual_type == error_type
    ), f"Expected {error_type}, got {actual_type}: {context['error']}"


@then(parsers.parse('I should receive an "{error_type}"'))
def should_receive_error_an(context: Dict[str, Any], error_type: str) -> None:
    """Verify that a specific error was raised (alternate grammar)."""
    should_receive_error(context, error_type)
