from decimal import Decimal, InvalidOperation

from domain.exceptions import ValidationError


def validate_product_name(name: str) -> str:
    """Validate product name: 1-200 characters, non-empty."""
    if not name or not name.strip():
        raise ValidationError("Product name cannot be empty", field="name")
    name = name.strip()
    if len(name) > 200:
        raise ValidationError(
            "Product name cannot exceed 200 characters", field="name"
        )
    return name


def validate_product_price(price: Decimal | str | float) -> Decimal:
    """Validate product price: greater than 0, max 2 decimal places."""
    try:
        if isinstance(price, str):
            price = Decimal(price)
        elif isinstance(price, float):
            price = Decimal(str(price))
    except InvalidOperation:
        raise ValidationError("Invalid price format", field="price")

    if price <= 0:
        raise ValidationError("Price must be greater than 0", field="price")

    # Check decimal places
    exponent = price.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -2:
        raise ValidationError("Price cannot have more than 2 decimal places", field="price")

    return price


def validate_stock_quantity(quantity: int) -> int:
    """Validate stock quantity: 0 or greater."""
    if quantity < 0:
        raise ValidationError("Stock quantity cannot be negative", field="stock_quantity")
    return quantity


def validate_cart_item_quantity(quantity: int) -> int:
    """Validate cart item quantity: must be positive (> 0)."""
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0", field="quantity")
    return quantity
