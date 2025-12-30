class DomainError(Exception):
    """Base exception for domain errors."""

    pass


class ValidationError(DomainError):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.message = message
        self.field = field
        super().__init__(message)


class DuplicateProductError(DomainError):
    """Raised when attempting to create a product with a name that already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"A product with name '{name}' already exists")


class InsufficientStockError(DomainError):
    """Raised when there isn't enough stock for an operation."""

    def __init__(self, product_name: str, available: int, requested: int):
        self.product_name = product_name
        self.available = available
        self.requested = requested
        super().__init__(
            f"Insufficient stock for '{product_name}': "
            f"requested {requested}, available {available}"
        )


class ProductNotFoundError(DomainError):
    """Raised when a product is not found."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Product with ID '{product_id}' not found")


class ProductInUseError(DomainError):
    """Raised when attempting to delete a product that is in use."""

    def __init__(self, product_id: str, reason: str):
        self.product_id = product_id
        self.reason = reason
        super().__init__(f"Cannot delete product: {reason}")


class CartItemNotFoundError(DomainError):
    """Raised when a cart item is not found."""

    def __init__(self, product_id: str):
        self.product_id = product_id
        super().__init__(f"Cart item for product '{product_id}' not found")


class EmptyCartError(DomainError):
    """Raised when attempting to submit an empty cart."""

    def __init__(self):
        super().__init__("Cannot submit an empty cart")
