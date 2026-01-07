"""BDD test fixtures and configuration."""

from typing import Any, Generator

import pytest
from uuid import uuid4

from application.ports.address_verification import AddressVerificationPort
from application.services.cart_service import CartService
from application.services.order_service import OrderService
from application.services.product_service import ProductService
from domain.aggregates.order.value_objects import UnverifiedAddress
from domain.user_context import Role, UserContext
from infrastructure.django_app.address_verification import get_address_verification_adapter
from infrastructure.django_app.unit_of_work import DjangoUnitOfWork


@pytest.fixture
def uow(db: Any) -> DjangoUnitOfWork:
    """Create a Django Unit of Work for database access."""
    return DjangoUnitOfWork()


@pytest.fixture
def address_verification() -> AddressVerificationPort:
    """Get the address verification adapter (stub in test mode)."""
    return get_address_verification_adapter()


@pytest.fixture
def product_service(uow: DjangoUnitOfWork) -> ProductService:
    """Create a ProductService instance."""
    return ProductService(uow)


@pytest.fixture
def cart_service(
    uow: DjangoUnitOfWork, address_verification: AddressVerificationPort
) -> CartService:
    """Create a CartService instance."""
    return CartService(uow, address_verification=address_verification)


@pytest.fixture
def order_service(uow: DjangoUnitOfWork) -> OrderService:
    """Create an OrderService instance."""
    return OrderService(uow)


@pytest.fixture
def admin_user_context() -> UserContext:
    """Create an admin UserContext."""
    return UserContext(
        user_id=uuid4(),
        username="admin",
        role=Role.ADMIN,
    )


@pytest.fixture
def customer_user_context() -> UserContext:
    """Create a customer UserContext."""
    return UserContext(
        user_id=uuid4(),
        username="customer",
        role=Role.CUSTOMER,
    )


@pytest.fixture
def context() -> dict[str, Any]:
    """
    Mutable context for passing data between BDD steps.

    Used to store:
    - current_user_context: The currently logged in user
    - error: Any exception raised during a "When I try..." step
    - products: Dict mapping product names to Product entities
    - orders: List of created orders
    - named_users: Dict mapping usernames to UserContext instances
    """
    return {
        "current_user_context": None,
        "error": None,
        "products": {},
        "orders": [],
        "named_users": {},
    }


def make_user_context(username: str, role: Role) -> UserContext:
    """Factory function to create a UserContext with a unique ID."""
    return UserContext(
        user_id=uuid4(),
        username=username,
        role=role,
    )


# Valid address for testing
VALID_SHIPPING_ADDRESS = UnverifiedAddress(
    street_line_1="123 Main St",
    street_line_2="Apt 4",
    city="Anytown",
    state="CA",
    postal_code="90210",
    country="US",
)

# Invalid address for testing (the stub rejects addresses with state="XX")
INVALID_SHIPPING_ADDRESS = UnverifiedAddress(
    street_line_1="Invalid Street Address",
    street_line_2=None,
    city="Nowhere",
    state="XX",
    postal_code="00000",
    country="US",
)
