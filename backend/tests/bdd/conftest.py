"""BDD test fixtures and configuration."""

from typing import Any, Dict, Generator

import pytest
from pytest_bdd import parser
from uuid import uuid4


def pytest_bdd_apply_tag(tag: str, function: Any) -> Any:
    """Filter scenarios by tag for backend tests.

    This hook allows us to skip frontend-only scenarios when running
    backend BDD tests. The shared feature files use tags to indicate
    which layer(s) should execute each scenario.
    """
    if tag == "frontend-only":
        return pytest.mark.skip(reason="Frontend-only scenario")
    # All other tags (backend, frontend, backend-only) run normally
    return None

from application.ports.address_verification import AddressVerificationPort
from application.services.cart_service import CartService
from application.services.feature_flag_service import FeatureFlagService
from application.services.order_service import OrderService
from application.services.product_service import ProductService
from application.services.user_group_service import UserGroupService
from application.services.user_service import UserService
from domain.aggregates.order.value_objects import UnverifiedAddress
from domain.user_context import Role, UserContext
from infrastructure.django_app.address_verification import get_address_verification_adapter
from infrastructure.django_app.feature_flags import get_feature_flag_repository
from infrastructure.django_app.repositories.user_group_repository import get_user_group_repository
from infrastructure.django_app.repositories.user_repository import get_user_repository
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
def feature_flag_service(db: Any) -> FeatureFlagService:
    """Create a FeatureFlagService instance."""
    return FeatureFlagService(get_feature_flag_repository())


@pytest.fixture
def user_group_service(db: Any) -> UserGroupService:
    """Create a UserGroupService instance."""
    return UserGroupService(get_user_group_repository())


@pytest.fixture
def user_service(db: Any) -> UserService:
    """Create a UserService instance."""
    return UserService(get_user_repository(), get_user_group_repository())


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
def context() -> Dict[str, Any]:
    """
    Mutable context for passing data between BDD steps.

    Used to store:
    - current_user_context: The currently logged in user
    - error: Any exception raised during a "When I try..." step
    - products: Dict mapping product names to Product entities
    - orders: List of created orders
    - named_users: Dict mapping usernames to UserContext instances
    - feature_flags: Dict mapping flag names to FeatureFlag entities
    - user_groups: Dict mapping group names to UserGroup entities
    """
    return {
        "current_user_context": None,
        "error": None,
        "products": {},
        "orders": [],
        "named_users": {},
        "feature_flags": {},
        "user_groups": {},
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
