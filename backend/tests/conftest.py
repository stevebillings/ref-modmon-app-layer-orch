"""Shared test fixtures."""

from typing import Any

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from infrastructure.django_app.models import UserProfile


@pytest.fixture
def admin_user(db: Any) -> User:
    """Create an admin user with profile."""
    user = User.objects.create_user(
        username="testadmin",
        password="testpass123",
        email="admin@test.com",
    )
    # Signal auto-creates profile with role="customer", update to admin
    UserProfile.objects.filter(user=user).update(role="admin")
    # Refresh user from DB to ensure profile relation is fresh
    user.refresh_from_db()
    return user


@pytest.fixture
def customer_user(db: Any) -> User:
    """Create a customer user with profile."""
    user = User.objects.create_user(
        username="testcustomer",
        password="testpass123",
        email="customer@test.com",
    )
    # Signal auto-creates profile with role="customer", no action needed
    return user


@pytest.fixture
def authenticated_admin_client(admin_user: User) -> APIClient:
    """API client authenticated as admin."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture
def authenticated_customer_client(customer_user: User) -> APIClient:
    """API client authenticated as customer."""
    client = APIClient()
    client.force_authenticate(user=customer_user)
    return client
