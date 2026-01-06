"""Tests for the product report API endpoint."""

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
    user = User.objects.create_user(username="reportadmin", password="testpass123")
    UserProfile.objects.create(user=user, role="admin")
    client = APIClient()
    client.force_login(user)
    return client


@pytest.fixture
def customer_client() -> APIClient:
    """Create an authenticated customer API client."""
    user = User.objects.create_user(username="reportcustomer", password="testpass123")
    UserProfile.objects.create(user=user, role="customer")
    client = APIClient()
    client.force_login(user)
    return client


def _create_product(admin_client: APIClient, name: str, price: str, stock: int) -> str:
    """Helper to create a product and return its ID."""
    response = admin_client.post(
        "/api/products/create/",
        {"name": name, "price": price, "stock_quantity": stock},
        format="json",
    )
    return response.json()["id"]


def _add_to_cart(customer_client: APIClient, product_id: str, quantity: int) -> None:
    """Helper to add a product to cart."""
    customer_client.post(
        "/api/cart/items/",
        {"product_id": product_id, "quantity": quantity},
        format="json",
    )


def _submit_cart(customer_client: APIClient) -> None:
    """Helper to submit cart as an order."""
    customer_client.post(
        "/api/cart/submit/",
        {
            "shipping_address": {
                "street_line_1": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "postal_code": "90210",
                "country": "US",
            }
        },
        format="json",
    )


@pytest.mark.django_db
class TestProductReportAuthorization:
    """Tests for product report authorization."""

    def test_report_requires_authentication(self, api_client: APIClient) -> None:
        """Unauthenticated users cannot access the report."""
        response = api_client.get("/api/products/report/")
        assert response.status_code == 401

    def test_report_requires_admin(self, customer_client: APIClient) -> None:
        """Non-admin users cannot access the report."""
        response = customer_client.get("/api/products/report/")
        assert response.status_code == 403
        assert "admin" in response.json()["error"].lower()

    def test_admin_can_access_report(self, admin_client: APIClient) -> None:
        """Admin users can access the report."""
        response = admin_client.get("/api/products/report/")
        assert response.status_code == 200


@pytest.mark.django_db
class TestProductReportBasicFunctionality:
    """Tests for basic product report functionality."""

    def test_empty_report(self, admin_client: APIClient) -> None:
        """Report with no products returns empty results with pagination metadata."""
        response = admin_client.get("/api/products/report/")
        data = response.json()

        assert data["results"] == []
        assert data["total_count"] == 0
        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_pages"] == 0
        assert data["has_next"] is False
        assert data["has_previous"] is False

    def test_report_includes_product_data(self, admin_client: APIClient) -> None:
        """Report includes basic product data."""
        _create_product(admin_client, "Test Product", "29.99", 50)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        assert data["total_count"] == 1
        item = data["results"][0]
        assert item["name"] == "Test Product"
        assert item["price"] == "29.99"
        assert item["stock_quantity"] == 50
        assert item["is_deleted"] is False

    def test_report_includes_aggregated_data(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Report includes total_sold and currently_reserved from other aggregates."""
        product_id = _create_product(admin_client, "Popular Item", "19.99", 100)

        # Add to cart (reserves stock)
        _add_to_cart(customer_client, product_id, 5)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        item = data["results"][0]
        assert item["currently_reserved"] == 5
        assert item["total_sold"] == 0  # Not sold yet, just in cart

    def test_report_tracks_total_sold(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Report correctly tracks total_sold from orders."""
        product_id = _create_product(admin_client, "Bestseller", "9.99", 100)

        # Add to cart and submit order
        _add_to_cart(customer_client, product_id, 3)
        _submit_cart(customer_client)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        item = data["results"][0]
        assert item["total_sold"] == 3
        assert item["currently_reserved"] == 0  # Cart cleared after order

    def test_report_aggregates_multiple_orders(
        self, admin_client: APIClient
    ) -> None:
        """Report aggregates sales across multiple orders from different customers."""
        product_id = _create_product(admin_client, "Multi-Order Item", "15.00", 100)

        # Create multiple customers and orders
        for i in range(3):
            user = User.objects.create_user(
                username=f"customer{i}", password="testpass"
            )
            UserProfile.objects.create(user=user, role="customer")
            customer = APIClient()
            customer.force_login(user)

            _add_to_cart(customer, product_id, 2)
            _submit_cart(customer)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        item = data["results"][0]
        assert item["total_sold"] == 6  # 2 * 3 orders

    def test_report_aggregates_multiple_carts(self, admin_client: APIClient) -> None:
        """Report aggregates reservations across multiple active carts."""
        product_id = _create_product(admin_client, "Cart Item", "20.00", 100)

        # Create multiple customers with items in cart
        for i in range(3):
            user = User.objects.create_user(
                username=f"cartcustomer{i}", password="testpass"
            )
            UserProfile.objects.create(user=user, role="customer")
            customer = APIClient()
            customer.force_login(user)

            _add_to_cart(customer, product_id, 4)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        item = data["results"][0]
        assert item["currently_reserved"] == 12  # 4 * 3 carts


@pytest.mark.django_db
class TestProductReportPagination:
    """Tests for product report pagination."""

    def _create_products(self, admin_client: APIClient, count: int) -> None:
        """Helper to create multiple products."""
        for i in range(count):
            _create_product(admin_client, f"Product {i:03d}", "10.00", 10)

    def test_pagination_defaults(self, admin_client: APIClient) -> None:
        """Test default pagination values."""
        self._create_products(admin_client, 5)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 20
        assert data["total_count"] == 5
        assert data["total_pages"] == 1
        assert len(data["results"]) == 5

    def test_custom_page_size(self, admin_client: APIClient) -> None:
        """Test custom page size."""
        self._create_products(admin_client, 25)

        response = admin_client.get("/api/products/report/?page_size=10")
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 10
        assert data["total_count"] == 25
        assert data["total_pages"] == 3
        assert data["has_next"] is True
        assert data["has_previous"] is False
        assert len(data["results"]) == 10

    def test_second_page(self, admin_client: APIClient) -> None:
        """Test fetching second page."""
        self._create_products(admin_client, 25)

        response = admin_client.get("/api/products/report/?page=2&page_size=10")
        data = response.json()

        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_previous"] is True
        assert len(data["results"]) == 10

    def test_last_page(self, admin_client: APIClient) -> None:
        """Test last page with partial results."""
        self._create_products(admin_client, 25)

        response = admin_client.get("/api/products/report/?page=3&page_size=10")
        data = response.json()

        assert data["page"] == 3
        assert data["has_next"] is False
        assert data["has_previous"] is True
        assert len(data["results"]) == 5

    def test_page_size_capped_at_100(self, admin_client: APIClient) -> None:
        """Page size should be capped at 100."""
        self._create_products(admin_client, 5)

        response = admin_client.get("/api/products/report/?page_size=200")
        data = response.json()

        assert data["page_size"] == 100


@pytest.mark.django_db
class TestProductReportFiltering:
    """Tests for product report filtering."""

    def test_filter_by_search(self, admin_client: APIClient) -> None:
        """Test filtering by product name search."""
        _create_product(admin_client, "Laptop Pro", "999.00", 10)
        _create_product(admin_client, "Laptop Mini", "599.00", 5)
        _create_product(admin_client, "Desktop Tower", "799.00", 8)

        response = admin_client.get("/api/products/report/?search=laptop")
        data = response.json()

        assert data["total_count"] == 2
        assert all("Laptop" in item["name"] for item in data["results"])

    def test_filter_by_low_stock_threshold(self, admin_client: APIClient) -> None:
        """Test filtering by low stock threshold."""
        _create_product(admin_client, "Low Stock Item", "10.00", 5)
        _create_product(admin_client, "Good Stock Item", "10.00", 50)
        _create_product(admin_client, "Critical Stock", "10.00", 2)

        response = admin_client.get("/api/products/report/?low_stock_threshold=10")
        data = response.json()

        assert data["total_count"] == 2
        assert all(item["stock_quantity"] <= 10 for item in data["results"])
        names = [item["name"] for item in data["results"]]
        assert "Low Stock Item" in names
        assert "Critical Stock" in names

    def test_filter_has_sales_true(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Test filtering for products with sales."""
        sold_id = _create_product(admin_client, "Sold Item", "10.00", 100)
        _create_product(admin_client, "Unsold Item", "10.00", 100)

        # Make a sale
        _add_to_cart(customer_client, sold_id, 1)
        _submit_cart(customer_client)

        response = admin_client.get("/api/products/report/?has_sales=true")
        data = response.json()

        assert data["total_count"] == 1
        assert data["results"][0]["name"] == "Sold Item"
        assert data["results"][0]["total_sold"] > 0

    def test_filter_has_sales_false(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Test filtering for products without sales."""
        sold_id = _create_product(admin_client, "Sold Item", "10.00", 100)
        _create_product(admin_client, "Unsold Item", "10.00", 100)

        # Make a sale
        _add_to_cart(customer_client, sold_id, 1)
        _submit_cart(customer_client)

        response = admin_client.get("/api/products/report/?has_sales=false")
        data = response.json()

        assert data["total_count"] == 1
        assert data["results"][0]["name"] == "Unsold Item"
        assert data["results"][0]["total_sold"] == 0

    def test_filter_has_reservations_true(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Test filtering for products in carts."""
        reserved_id = _create_product(admin_client, "Reserved Item", "10.00", 100)
        _create_product(admin_client, "Not Reserved", "10.00", 100)

        # Add to cart
        _add_to_cart(customer_client, reserved_id, 2)

        response = admin_client.get("/api/products/report/?has_reservations=true")
        data = response.json()

        assert data["total_count"] == 1
        assert data["results"][0]["name"] == "Reserved Item"
        assert data["results"][0]["currently_reserved"] > 0

    def test_filter_has_reservations_false(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Test filtering for products not in carts."""
        reserved_id = _create_product(admin_client, "Reserved Item", "10.00", 100)
        _create_product(admin_client, "Not Reserved", "10.00", 100)

        # Add to cart
        _add_to_cart(customer_client, reserved_id, 2)

        response = admin_client.get("/api/products/report/?has_reservations=false")
        data = response.json()

        assert data["total_count"] == 1
        assert data["results"][0]["name"] == "Not Reserved"
        assert data["results"][0]["currently_reserved"] == 0

    def test_filter_include_deleted(self, admin_client: APIClient) -> None:
        """Test including soft-deleted products."""
        active_id = _create_product(admin_client, "Active Product", "10.00", 10)
        deleted_id = _create_product(admin_client, "Deleted Product", "20.00", 5)

        # Soft delete one product
        admin_client.delete(f"/api/products/{deleted_id}/")

        # Without include_deleted
        response = admin_client.get("/api/products/report/")
        data = response.json()
        assert data["total_count"] == 1
        assert data["results"][0]["name"] == "Active Product"

        # With include_deleted
        response = admin_client.get("/api/products/report/?include_deleted=true")
        data = response.json()
        assert data["total_count"] == 2
        deleted_item = next(
            item for item in data["results"] if item["product_id"] == deleted_id
        )
        assert deleted_item["is_deleted"] is True

    def test_combined_filters(
        self, admin_client: APIClient, customer_client: APIClient
    ) -> None:
        """Test combining multiple filters."""
        # Create various products
        laptop_sold = _create_product(admin_client, "Laptop Sold", "500.00", 5)
        laptop_unsold = _create_product(admin_client, "Laptop Unsold", "600.00", 50)
        desktop_sold = _create_product(admin_client, "Desktop Sold", "700.00", 3)

        # Make sales for some products
        _add_to_cart(customer_client, laptop_sold, 1)
        _submit_cart(customer_client)

        # Create another customer and make another sale
        user = User.objects.create_user(username="buyer2", password="testpass")
        UserProfile.objects.create(user=user, role="customer")
        buyer2 = APIClient()
        buyer2.force_login(user)
        _add_to_cart(buyer2, desktop_sold, 1)
        _submit_cart(buyer2)

        # Filter: search=laptop, has_sales=true, low_stock_threshold=10
        response = admin_client.get(
            "/api/products/report/?search=laptop&has_sales=true&low_stock_threshold=10"
        )
        data = response.json()

        # Should only match "Laptop Sold" (name contains laptop, has sales, stock <= 10)
        assert data["total_count"] == 1
        assert data["results"][0]["name"] == "Laptop Sold"


@pytest.mark.django_db
class TestProductReportOrdering:
    """Tests for product report ordering."""

    def test_results_ordered_by_name(self, admin_client: APIClient) -> None:
        """Results should be ordered alphabetically by name."""
        _create_product(admin_client, "Zebra", "10.00", 10)
        _create_product(admin_client, "Apple", "10.00", 10)
        _create_product(admin_client, "Mango", "10.00", 10)

        response = admin_client.get("/api/products/report/")
        data = response.json()

        names = [item["name"] for item in data["results"]]
        assert names == ["Apple", "Mango", "Zebra"]
