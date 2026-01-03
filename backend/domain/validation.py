from domain.exceptions import ValidationError


def validate_positive_quantity(quantity: int) -> int:
    """Validate that quantity is positive (> 0)."""
    if quantity <= 0:
        raise ValidationError(
            "Quantity must be greater than 0", field="quantity"
        )
    return quantity
