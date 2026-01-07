"""Tests for feature flag infrastructure."""

from typing import Any

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from infrastructure.django_app.feature_flags import (
    DjangoFeatureFlagAdapter,
    DjangoFeatureFlagRepository,
)
from infrastructure.django_app.models import FeatureFlagModel, UserProfile


@pytest.fixture
def admin_client(db: Any) -> APIClient:
    """Create an authenticated admin API client."""
    user = User.objects.create_user(username="flagadmin", password="testpass123")
    UserProfile.objects.create(user=user, role="admin")
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def customer_client(db: Any) -> APIClient:
    """Create an authenticated customer API client."""
    user = User.objects.create_user(username="flagcustomer", password="testpass123")
    UserProfile.objects.create(user=user, role="customer")
    client = APIClient()
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestDjangoFeatureFlagAdapter:
    """Tests for the feature flag adapter."""

    def test_is_enabled_returns_false_for_nonexistent_flag(self) -> None:
        adapter = DjangoFeatureFlagAdapter()
        assert adapter.is_enabled("nonexistent_flag") is False

    def test_is_enabled_returns_false_for_disabled_flag(self) -> None:
        FeatureFlagModel.objects.create(
            name="disabled_flag",
            enabled=False,
            description="A disabled flag",
        )
        adapter = DjangoFeatureFlagAdapter()
        assert adapter.is_enabled("disabled_flag") is False

    def test_is_enabled_returns_true_for_enabled_flag(self) -> None:
        FeatureFlagModel.objects.create(
            name="enabled_flag",
            enabled=True,
            description="An enabled flag",
        )
        adapter = DjangoFeatureFlagAdapter()
        assert adapter.is_enabled("enabled_flag") is True

    def test_flag_state_changes_are_reflected(self) -> None:
        flag = FeatureFlagModel.objects.create(
            name="toggle_flag",
            enabled=False,
        )
        adapter = DjangoFeatureFlagAdapter()

        assert adapter.is_enabled("toggle_flag") is False

        flag.enabled = True
        flag.save()

        assert adapter.is_enabled("toggle_flag") is True


@pytest.mark.django_db
class TestFeatureFlagAPI:
    """Tests for feature flag admin API endpoints."""

    def test_list_flags_empty(self, admin_client: APIClient) -> None:
        response = admin_client.get("/api/admin/feature-flags/")
        assert response.status_code == 200
        assert response.json()["results"] == []

    def test_list_flags(self, admin_client: APIClient) -> None:
        FeatureFlagModel.objects.create(name="flag_a", enabled=True)
        FeatureFlagModel.objects.create(name="flag_b", enabled=False)

        response = admin_client.get("/api/admin/feature-flags/")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        names = [f["name"] for f in results]
        assert "flag_a" in names
        assert "flag_b" in names

    def test_list_flags_requires_admin(self, customer_client: APIClient) -> None:
        response = customer_client.get("/api/admin/feature-flags/")
        assert response.status_code == 403

    def test_create_flag(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/admin/feature-flags/create/",
            {
                "name": "new_flag",
                "enabled": True,
                "description": "A new feature flag",
            },
            format="json",
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "new_flag"
        assert data["enabled"] is True
        assert data["description"] == "A new feature flag"

    def test_create_flag_defaults_to_disabled(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/admin/feature-flags/create/",
            {"name": "default_disabled"},
            format="json",
        )
        assert response.status_code == 201
        assert response.json()["enabled"] is False

    def test_create_flag_requires_name(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/admin/feature-flags/create/",
            {"enabled": True},
            format="json",
        )
        assert response.status_code == 400
        assert "name" in response.json()["error"].lower()

    def test_create_flag_duplicate_name(self, admin_client: APIClient) -> None:
        FeatureFlagModel.objects.create(name="existing_flag", enabled=False)

        response = admin_client.post(
            "/api/admin/feature-flags/create/",
            {"name": "existing_flag"},
            format="json",
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["error"]

    def test_create_flag_requires_admin(self, customer_client: APIClient) -> None:
        response = customer_client.post(
            "/api/admin/feature-flags/create/",
            {"name": "customer_flag"},
            format="json",
        )
        assert response.status_code == 403

    def test_get_flag(self, admin_client: APIClient) -> None:
        FeatureFlagModel.objects.create(
            name="get_me",
            enabled=True,
            description="Get this flag",
        )

        response = admin_client.get("/api/admin/feature-flags/get_me/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "get_me"
        assert data["enabled"] is True
        assert data["description"] == "Get this flag"

    def test_get_nonexistent_flag(self, admin_client: APIClient) -> None:
        response = admin_client.get("/api/admin/feature-flags/nonexistent/")
        assert response.status_code == 404

    def test_update_flag(self, admin_client: APIClient) -> None:
        FeatureFlagModel.objects.create(name="update_me", enabled=False)

        response = admin_client.put(
            "/api/admin/feature-flags/update_me/",
            {"enabled": True, "description": "Now enabled"},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["description"] == "Now enabled"

    def test_update_flag_partial(self, admin_client: APIClient) -> None:
        FeatureFlagModel.objects.create(
            name="partial_update",
            enabled=False,
            description="Original description",
        )

        response = admin_client.put(
            "/api/admin/feature-flags/partial_update/",
            {"enabled": True},
            format="json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert data["description"] == "Original description"

    def test_delete_flag(self, admin_client: APIClient) -> None:
        FeatureFlagModel.objects.create(name="delete_me", enabled=True)

        response = admin_client.delete("/api/admin/feature-flags/delete_me/")
        assert response.status_code == 204

        # Verify deleted
        assert not FeatureFlagModel.objects.filter(name="delete_me").exists()

    def test_delete_nonexistent_flag(self, admin_client: APIClient) -> None:
        response = admin_client.delete("/api/admin/feature-flags/nonexistent/")
        assert response.status_code == 404

    def test_flag_operations_require_admin(self, customer_client: APIClient) -> None:
        FeatureFlagModel.objects.create(name="admin_only", enabled=True)

        # GET
        response = customer_client.get("/api/admin/feature-flags/admin_only/")
        assert response.status_code == 403

        # PUT
        response = customer_client.put(
            "/api/admin/feature-flags/admin_only/",
            {"enabled": False},
            format="json",
        )
        assert response.status_code == 403

        # DELETE
        response = customer_client.delete("/api/admin/feature-flags/admin_only/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestDjangoFeatureFlagRepository:
    """Tests for the feature flag repository."""

    def test_get_all_empty(self) -> None:
        repo = DjangoFeatureFlagRepository()
        flags = repo.get_all()
        assert flags == []

    def test_get_all_returns_all_flags(self) -> None:
        FeatureFlagModel.objects.create(name="flag_a", enabled=True)
        FeatureFlagModel.objects.create(name="flag_b", enabled=False)

        repo = DjangoFeatureFlagRepository()
        flags = repo.get_all()

        assert len(flags) == 2
        names = [f.name for f in flags]
        assert "flag_a" in names
        assert "flag_b" in names

    def test_get_by_name_returns_flag(self) -> None:
        FeatureFlagModel.objects.create(
            name="get_me",
            enabled=True,
            description="Test flag",
        )

        repo = DjangoFeatureFlagRepository()
        flag = repo.get_by_name("get_me")

        assert flag is not None
        assert flag.name == "get_me"
        assert flag.enabled is True
        assert flag.description == "Test flag"

    def test_get_by_name_not_found(self) -> None:
        repo = DjangoFeatureFlagRepository()
        flag = repo.get_by_name("nonexistent")
        assert flag is None

    def test_exists_returns_true_for_existing(self) -> None:
        FeatureFlagModel.objects.create(name="exists", enabled=True)

        repo = DjangoFeatureFlagRepository()
        assert repo.exists("exists") is True

    def test_exists_returns_false_for_nonexistent(self) -> None:
        repo = DjangoFeatureFlagRepository()
        assert repo.exists("nonexistent") is False

    def test_save_creates_new_flag(self) -> None:
        repo = DjangoFeatureFlagRepository()

        flag = repo.save("new_flag", enabled=True, description="Created via repo")

        assert flag.name == "new_flag"
        assert flag.enabled is True
        assert flag.description == "Created via repo"
        assert FeatureFlagModel.objects.filter(name="new_flag").exists()

    def test_save_updates_existing_flag(self) -> None:
        FeatureFlagModel.objects.create(
            name="update_me",
            enabled=False,
            description="Original",
        )

        repo = DjangoFeatureFlagRepository()
        flag = repo.save("update_me", enabled=True, description="Updated")

        assert flag.enabled is True
        assert flag.description == "Updated"

        # Verify DB was updated
        model = FeatureFlagModel.objects.get(name="update_me")
        assert model.enabled is True
        assert model.description == "Updated"

    def test_delete_removes_flag(self) -> None:
        FeatureFlagModel.objects.create(name="delete_me", enabled=True)

        repo = DjangoFeatureFlagRepository()
        result = repo.delete("delete_me")

        assert result is True
        assert not FeatureFlagModel.objects.filter(name="delete_me").exists()

    def test_delete_nonexistent_returns_false(self) -> None:
        repo = DjangoFeatureFlagRepository()
        result = repo.delete("nonexistent")
        assert result is False
