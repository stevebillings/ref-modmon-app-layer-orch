"""Common step definitions shared across features."""

from decimal import Decimal
from typing import Any
from uuid import uuid4

from django.contrib.auth.models import User
from pytest_bdd import given, parsers

from application.services.product_service import ProductService
from domain.user_context import Role, UserContext
from infrastructure.django_app.models import UserProfile


def _create_database_user(username: str, role: str = "customer") -> UserContext:
    """Create a real Django user with profile and return UserContext."""
    # Check if user already exists
    try:
        django_user = User.objects.get(username=username)
        profile = django_user.profile
    except User.DoesNotExist:
        # Create Django User - the post_save signal auto-creates UserProfile
        django_user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpassword",
        )
        # Get the profile that was created by the signal
        profile = django_user.profile
        # Update role if needed
        if role != "customer":
            profile.role = role
            profile.save()
    # Return UserContext with the real profile ID
    return UserContext(
        user_id=profile.id,
        username=username,
        role=Role.ADMIN if role == "admin" else Role.CUSTOMER,
    )


@given("I am logged in as an Admin")
def logged_in_as_admin(context: dict[str, Any], admin_user_context: UserContext) -> None:
    """Set the current user context to admin."""
    context["current_user_context"] = admin_user_context


@given("I am logged in as a Customer")
def logged_in_as_customer(
    context: dict[str, Any], customer_user_context: UserContext
) -> None:
    """Set the current user context to customer."""
    context["current_user_context"] = customer_user_context


@given(parsers.parse('I am logged in as customer "{username}"'))
def logged_in_as_named_customer(context: dict[str, Any], username: str) -> None:
    """Set the current user context to a specific named customer."""
    if username not in context["named_users"]:
        context["named_users"][username] = _create_database_user(username, "customer")
    context["current_user_context"] = context["named_users"][username]


@given(
    parsers.parse(
        'a product "{name}" exists with price "${price}" and stock quantity {qty:d}'
    )
)
def product_exists(
    context: dict[str, Any],
    product_service: ProductService,
    admin_user_context: UserContext,
    name: str,
    price: str,
    qty: int,
) -> None:
    """Create a product with the given attributes."""
    product = product_service.create_product(
        name=name,
        price=Decimal(price),
        stock_quantity=qty,
        user_context=admin_user_context,
    )
    context["products"][name] = product


@given(parsers.parse('a customer "{username}" exists'))
def customer_exists(context: dict[str, Any], username: str) -> None:
    """Ensure a named customer exists with a real database user profile."""
    if username not in context["named_users"]:
        context["named_users"][username] = _create_database_user(username, "customer")
