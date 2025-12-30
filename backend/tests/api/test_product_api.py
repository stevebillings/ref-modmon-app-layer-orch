import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.mark.django_db
class TestProductListCreate:
    def test_list_products_empty(self, api_client):
        response = api_client.get("/api/products/")
        assert response.status_code == 200
        assert response.json() == {"results": []}

    def test_create_product(self, api_client):
        response = api_client.post(
            "/api/products/",
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

    def test_create_product_validation_error(self, api_client):
        response = api_client.post(
            "/api/products/",
            {"name": "", "price": "10.00", "stock_quantity": 10},
            format="json",
        )

        assert response.status_code == 400
        assert "error" in response.json()

    def test_create_product_duplicate_name(self, api_client):
        api_client.post(
            "/api/products/",
            {"name": "Unique", "price": "10.00", "stock_quantity": 10},
            format="json",
        )

        response = api_client.post(
            "/api/products/",
            {"name": "Unique", "price": "20.00", "stock_quantity": 20},
            format="json",
        )

        assert response.status_code == 400

    def test_list_products(self, api_client):
        api_client.post(
            "/api/products/",
            {"name": "Zebra", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        api_client.post(
            "/api/products/",
            {"name": "Apple", "price": "5.00", "stock_quantity": 20},
            format="json",
        )

        response = api_client.get("/api/products/")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2
        # Should be alphabetically ordered
        assert results[0]["name"] == "Apple"
        assert results[1]["name"] == "Zebra"


@pytest.mark.django_db
class TestProductDelete:
    def test_delete_product(self, api_client):
        response = api_client.post(
            "/api/products/",
            {"name": "To Delete", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        response = api_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 204

        # Verify deleted
        response = api_client.get("/api/products/")
        assert len(response.json()["results"]) == 0

    def test_delete_nonexistent_product(self, api_client):
        response = api_client.delete(
            "/api/products/00000000-0000-0000-0000-000000000000/"
        )
        assert response.status_code == 404

    def test_delete_product_in_cart(self, api_client):
        # Create product
        response = api_client.post(
            "/api/products/",
            {"name": "In Cart", "price": "10.00", "stock_quantity": 10},
            format="json",
        )
        product_id = response.json()["id"]

        # Add to cart
        api_client.post(
            "/api/cart/items/",
            {"product_id": product_id, "quantity": 1},
            format="json",
        )

        # Try to delete
        response = api_client.delete(f"/api/products/{product_id}/")
        assert response.status_code == 400
        assert "cart" in response.json()["error"].lower()
