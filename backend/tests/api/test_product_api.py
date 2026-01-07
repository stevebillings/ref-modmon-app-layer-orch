from typing import Any

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from infrastructure.django_app.models import UserProfile


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def admin_client() -> APIClient:
    """Create an authenticated admin API client."""
    user = User.objects.create_user(username="testadmin", password="testpass123")
    UserProfile.objects.create(user=user, role="admin")
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def customer_client() -> APIClient:
    """Create an authenticated customer API client."""
    user = User.objects.create_user(username="testcustomer", password="testpass123")
    UserProfile.objects.create(user=user, role="customer")
    client = APIClient()
    client.force_login(user)
    return client


@pytest.mark.django_db
class TestProductListCreate:
    def test_list_products_empty(self, api_client: APIClient) -> None:
        response = api_client.get("/api/products/")
        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_create_product(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Test Product", "price": "19.99", "stock_quantity": 100},
            format="json",
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["price"] == "19.99"
        assert data["stock_quantity"] == 100
        assert "id" in data
        assert "created_at" in data

    def test_create_product_validation_error(self, admin_client: APIClient) -> None:
        response = admin_client.post(
            "/api/products/create/",
            {"name": "", "price": "10.00", "stock_quantity": 10},
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_create_product_duplicate_name(self, admin_client: APIClient) -> None:
        admin_client.post(
            "/api/products/create/",
            {"name": "Unique", "price": "10.00", "stock_quantity": 10},
            format="json",
        )

        response = admin_client.post(
            "/api/products/create/",
            {"name": "Unique", "price": "20.00", "stock_quantity": 20},
            format="json",
        )

        assert response.status_code == 400

    def test_list_products(self, api_client: APIClient, admin_client: APIClient) -> None:
        admin_client.post(
            "/api/products/create/",
            {"name": "Zebra", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        admin_client.post(
            "/api/products/create/",
            {"name": "Apple", "price": "5.00", "stock_quantity": 20},
            format="json",
        )

        response = api_client.get("/api/products/")
        assert response.status_code == 200
        data = response.json()
        results = data["results"]
        assert len(results) == 2
        assert data["total_count"] == 2
        # Should be alphabetically ordered
        assert results[0]["name"] == "Apple"
        assert results[1]["name"] == "Zebra"


@pytest.mark.django_db
class TestProductDelete:
    def test_delete_product(self, admin_client: APIClient, api_client: APIClient) -> None:
        response = admin_client.post(
            "/api/products/create/",
            {"name": "To Delete", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        response = admin_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 204

        # Verify deleted
        response = api_client.get("/api/products/")
        assert len(response.json()["results"]) == 0

    def test_delete_nonexistent_product(self, admin_client: APIClient) -> None:
        response = admin_client.delete(
            "/api/products/00000000-0000-0000-0000-000000000000/"
        )
        assert response.status_code == 404

    def test_delete_product_in_cart(self, admin_client: APIClient, customer_client: APIClient) -> None:
        # Create product
        response = admin_client.post(
            "/api/products/create/",
            {"name": "In Cart", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        # Add to cart (using customer client)
        customer_client.post(
            "/api/cart/items/",
            {"product_id": product_id, "quantity": 1},
            format="json",
        )

        # Try to delete (as admin)
        response = admin_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 400
        assert "cart" in response.json()["error"].lower()


@pytest.mark.django_db
class TestProductSoftDelete:
    def test_delete_product_is_soft_delete(
        self, admin_client: APIClient, api_client: APIClient
    ) -> None:
        """Verify delete is soft delete - product hidden but not destroyed."""
        # Create product
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Soft Delete Test", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        # Delete
        response = admin_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 204

        # Not visible in normal list
        response = api_client.get("/api/products/")
        assert product_id not in [p["id"] for p in response.json()["results"]]

        # Visible with include_deleted (as admin)
        response = admin_client.get("/api/products/?include_deleted=true")
        product_ids = [p["id"] for p in response.json()["results"]]
        assert product_id in product_ids

    def test_include_deleted_requires_admin(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Non-admins cannot see deleted products even with include_deleted=true."""
        # Create and delete product
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Admin Only", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]
        admin_client.delete(f"/api/products/{product_id}/")

        # Customer with include_deleted=true should NOT see deleted
        response = customer_client.get("/api/products/?include_deleted=true")
        assert product_id not in [p["id"] for p in response.json()["results"]]

    def test_restore_product(self, admin_client: APIClient, api_client: APIClient) -> None:
        """Test restoring a soft-deleted product."""
        # Create and delete
        response = admin_client.post(
            "/api/products/create/",
            {"name": "To Restore", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]
        admin_client.delete(f"/api/products/{product_id}/")

        # Restore
        response = admin_client.post(f"/api/products/{product_id}/restore/")
        assert response.status_code == 200
        assert response.json()["id"] == product_id
        assert response.json()["deleted_at"] is None

        # Now visible again
        response = api_client.get("/api/products/")
        assert product_id in [p["id"] for p in response.json()["results"]]

    def test_restore_non_deleted_returns_error(self, admin_client: APIClient) -> None:
        """Restoring a non-deleted product should fail."""
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Not Deleted", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        response = admin_client.post(f"/api/products/{product_id}/restore/")
        assert response.status_code == 400

    def test_delete_already_deleted_returns_error(self, admin_client: APIClient) -> None:
        """Deleting an already deleted product should fail."""
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Already Deleted", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        # First delete succeeds
        response = admin_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 204

        # Second delete fails
        response = admin_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 400

    def test_deleted_product_has_deleted_at_in_response(
        self, admin_client: APIClient
    ) -> None:
        """Verify deleted_at is included in response for admins."""
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Check deleted_at", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]
        admin_client.delete(f"/api/products/{product_id}/")

        # Get with include_deleted
        response = admin_client.get("/api/products/?include_deleted=true")
        product = next(
            p for p in response.json()["results"] if p["id"] == product_id
        )
        assert product["deleted_at"] is not None

    def test_restore_requires_admin(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Only admins can restore products."""
        response = admin_client.post(
            "/api/products/create/",
            {"name": "Restore Auth Test", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]
        admin_client.delete(f"/api/products/{product_id}/")

        # Customer cannot restore
        response = customer_client.post(f"/api/products/{product_id}/restore/")
        assert response.status_code == 403


@pytest.mark.django_db
class TestProductPagination:
    """Tests for product list pagination and filtering."""

    def _create_products(self, admin_client: APIClient, products: list[dict[str, object]]) -> None:
        """Helper to create multiple products."""
        for p in products:
            admin_client.post("/api/products/create/", p, format="json")

    def test_pagination_defaults(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test default pagination values."""
        self._create_products(admin_client, [
            {"name": f"Product {i}", "price": "10.00", "stock_quantity": 10}
            for i in range(5)
        ])

        response = api_client.get("/api/products/")
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_count"] == 5
        assert data["total_pages"] == 1
        assert data["has_next"] is False
        assert data["has_previous"] is False
        assert len(data["results"]) == 5

    def test_pagination_custom_page_size(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test custom page size."""
        self._create_products(admin_client, [
            {"name": f"Product {i:02d}", "price": "10.00", "stock_quantity": 10}
            for i in range(25)
        ])

        response = api_client.get("/api/products/?page_size=10")
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_count"] == 25
        assert data["total_pages"] == 3
        assert data["has_next"] is True
        assert data["has_previous"] is False
        assert len(data["results"]) == 10

    def test_pagination_second_page(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test fetching second page."""
        self._create_products(admin_client, [
            {"name": f"Product {i:02d}", "price": "10.00", "stock_quantity": 10}
            for i in range(25)
        ])

        response = api_client.get("/api/products/?page=2&page_size=10")
        data = response.json()

        assert data["page"] == 2
        assert data["page_size"] == 10
        assert data["total_count"] == 25
        assert data["has_next"] is True
        assert data["has_previous"] is True
        assert len(data["results"]) == 10

    def test_pagination_last_page(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test last page with partial results."""
        self._create_products(admin_client, [
            {"name": f"Product {i:02d}", "price": "10.00", "stock_quantity": 10}
            for i in range(25)
        ])

        response = api_client.get("/api/products/?page=3&page_size=10")
        data = response.json()

        assert data["page"] == 3
        assert data["has_next"] is False
        assert data["has_previous"] is True
        assert len(data["results"]) == 5

    def test_filter_by_search(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test filtering by search term."""
        self._create_products(admin_client, [
            {"name": "Laptop Pro", "price": "999.00", "stock_quantity": 10},
            {"name": "Laptop Mini", "price": "599.00", "stock_quantity": 5},
            {"name": "Desktop Tower", "price": "799.00", "stock_quantity": 8},
        ])

        response = api_client.get("/api/products/?search=laptop")
        data = response.json()

        assert data["total_count"] == 2
        assert all("Laptop" in p["name"] for p in data["results"])

    def test_filter_by_min_price(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test filtering by minimum price."""
        self._create_products(admin_client, [
            {"name": "Cheap Item", "price": "10.00", "stock_quantity": 100},
            {"name": "Mid Item", "price": "50.00", "stock_quantity": 50},
            {"name": "Expensive Item", "price": "100.00", "stock_quantity": 10},
        ])

        response = api_client.get("/api/products/?min_price=50")
        data = response.json()

        assert data["total_count"] == 2
        assert all(float(p["price"]) >= 50 for p in data["results"])

    def test_filter_by_max_price(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test filtering by maximum price."""
        self._create_products(admin_client, [
            {"name": "Cheap Item", "price": "10.00", "stock_quantity": 100},
            {"name": "Mid Item", "price": "50.00", "stock_quantity": 50},
            {"name": "Expensive Item", "price": "100.00", "stock_quantity": 10},
        ])

        response = api_client.get("/api/products/?max_price=50")
        data = response.json()

        assert data["total_count"] == 2
        assert all(float(p["price"]) <= 50 for p in data["results"])

    def test_filter_by_price_range(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test filtering by price range."""
        self._create_products(admin_client, [
            {"name": "Item A", "price": "10.00", "stock_quantity": 100},
            {"name": "Item B", "price": "50.00", "stock_quantity": 50},
            {"name": "Item C", "price": "75.00", "stock_quantity": 25},
            {"name": "Item D", "price": "100.00", "stock_quantity": 10},
        ])

        response = api_client.get("/api/products/?min_price=40&max_price=80")
        data = response.json()

        assert data["total_count"] == 2
        names = [p["name"] for p in data["results"]]
        assert "Item B" in names
        assert "Item C" in names

    def test_filter_in_stock(self, api_client: APIClient, admin_client: APIClient) -> None:
        """Test filtering for in-stock items only."""
        self._create_products(admin_client, [
            {"name": "In Stock Item", "price": "10.00", "stock_quantity": 50},
            {"name": "Out of Stock", "price": "20.00", "stock_quantity": 0},
            {"name": "Also In Stock", "price": "30.00", "stock_quantity": 1},
        ])

        response = api_client.get("/api/products/?in_stock=true")
        data = response.json()

        assert data["total_count"] == 2
        assert all(p["stock_quantity"] > 0 for p in data["results"])

    def test_combined_filters_and_pagination(
        self, api_client: APIClient, admin_client: APIClient
    ) -> None:
        """Test combining filters with pagination."""
        self._create_products(admin_client, [
            {"name": f"Widget {i}", "price": str(10 + i * 10), "stock_quantity": i * 5}
            for i in range(10)
        ])

        # Search for "Widget", price between 30 and 70, in stock, page 1 of size 2
        response = api_client.get(
            "/api/products/?search=widget&min_price=30&max_price=70&in_stock=true&page_size=2"
        )
        data = response.json()

        # Widgets 3-6 match price range (30, 40, 50, 60, 70), but Widget 0 has 0 stock
        # So we expect widgets 3, 4, 5, 6 to match (Widget 2=30, 3=40, 4=50, 5=60, 6=70)
        # Widget 2 has stock=10, Widget 3 has stock=15, etc.
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["results"]) == 2
        assert data["has_next"] is True
