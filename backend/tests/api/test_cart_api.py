from typing import Any, Dict, cast

import pytest
from rest_framework.test import APIClient


@pytest.fixture
def product(authenticated_admin_client: APIClient) -> Dict[str, Any]:
    response = authenticated_admin_client.post(
        "/api/products/create/",
        {"name": "Test Product", "price": "10.00", "stock_quantity": 100},
        format="json",
    )
    return cast(Dict[str, Any], response.json())


@pytest.mark.django_db
class TestCartGet:
    def test_get_empty_cart(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.get("/api/cart/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == "0"
        assert data["item_count"] == 0


@pytest.mark.django_db
class TestCartAddItem:
    def test_add_item_to_cart(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 2},
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["product_name"] == "Test Product"
        assert data["items"][0]["quantity"] == 2
        assert data["total"] == "20.00"
        assert data["item_count"] == 2

    def test_add_item_reserves_stock(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 25},
            format="json",
        )

        response = authenticated_admin_client.get("/api/products/")
        products = response.json()["results"]
        updated_product = next(p for p in products if p["id"] == product["id"])
        assert updated_product["stock_quantity"] == 75

    def test_add_same_product_increases_quantity(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 3},
            format="json",
        )
        response = authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 2},
            format="json",
        )

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 5

    def test_add_insufficient_stock(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 200},
            format="json",
        )

        assert response.status_code == 400
        assert "stock" in response.json()["error"].lower()

    def test_add_nonexistent_product(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/items/",
            {
                "product_id": "00000000-0000-0000-0000-000000000000",
                "quantity": 1,
            },
            format="json",
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCartUpdateItem:
    def test_update_item_quantity(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )

        response = authenticated_admin_client.patch(
            f"/api/cart/items/{product['id']}/",
            {"quantity": 8},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["items"][0]["quantity"] == 8

    def test_update_adjusts_stock(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 10},
            format="json",
        )

        authenticated_admin_client.patch(
            f"/api/cart/items/{product['id']}/",
            {"quantity": 15},
            format="json",
        )

        response = authenticated_admin_client.get("/api/products/")
        products = response.json()["results"]
        updated_product = next(p for p in products if p["id"] == product["id"])
        assert updated_product["stock_quantity"] == 85

    def test_update_insufficient_stock(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )

        response = authenticated_admin_client.patch(
            f"/api/cart/items/{product['id']}/",
            {"quantity": 200},
            format="json",
        )

        assert response.status_code == 400

    def test_update_nonexistent_item(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.patch(
            "/api/cart/items/00000000-0000-0000-0000-000000000000/",
            {"quantity": 5},
            format="json",
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCartRemoveItem:
    def test_remove_item(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )

        response = authenticated_admin_client.delete(
            f"/api/cart/items/{product['id']}/remove/"
        )

        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_remove_releases_stock(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 25},
            format="json",
        )

        authenticated_admin_client.delete(f"/api/cart/items/{product['id']}/remove/")

        response = authenticated_admin_client.get("/api/products/")
        products = response.json()["results"]
        updated_product = next(p for p in products if p["id"] == product["id"])
        assert updated_product["stock_quantity"] == 100

    def test_remove_nonexistent_item(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.delete(
            "/api/cart/items/00000000-0000-0000-0000-000000000000/remove/"
        )

        assert response.status_code == 404


VALID_SHIPPING_ADDRESS = {
    "street_line_1": "123 Main St",
    "street_line_2": "Apt 4",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "90210",
    "country": "US",
}


@pytest.mark.django_db
class TestCartVerifyAddress:
    def test_verify_valid_address(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/verify-address/",
            VALID_SHIPPING_ADDRESS,
            format="json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True
        assert data["status"] == "verified"
        assert "standardized_address" in data
        # Stub adapter uppercases addresses
        assert data["standardized_address"]["city"] == "ANYTOWN"

    def test_verify_invalid_address(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/verify-address/",
            {
                "street_line_1": "Invalid Street Address",
                "city": "Nowhere",
                "state": "XX",
                "postal_code": "00000",
                "country": "US",
            },
            format="json",
        )

        assert response.status_code == 400
        data = response.json()
        assert data["verified"] is False
        assert "error_message" in data

    def test_verify_undeliverable_address(
        self, authenticated_admin_client: APIClient
    ) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/verify-address/",
            {
                "street_line_1": "Undeliverable Address",
                "city": "Somewhere",
                "state": "CA",
                "postal_code": "90210",
                "country": "US",
            },
            format="json",
        )

        assert response.status_code == 400
        data = response.json()
        assert data["verified"] is False


@pytest.mark.django_db
class TestCartSubmit:
    def test_submit_cart(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 3},
            format="json",
        )

        response = authenticated_admin_client.post(
            "/api/cart/submit/",
            {"shipping_address": VALID_SHIPPING_ADDRESS},
            format="json",
        )

        assert response.status_code == 201
        order = response.json()
        assert len(order["items"]) == 1
        assert order["items"][0]["product_name"] == "Test Product"
        assert order["total"] == "30.00"
        assert "shipping_address" in order
        assert order["shipping_address"]["city"] == "ANYTOWN"

    def test_submit_clears_cart(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 2},
            format="json",
        )

        authenticated_admin_client.post(
            "/api/cart/submit/",
            {"shipping_address": VALID_SHIPPING_ADDRESS},
            format="json",
        )

        response = authenticated_admin_client.get("/api/cart/")
        assert response.json()["items"] == []

    def test_submit_empty_cart(self, authenticated_admin_client: APIClient) -> None:
        response = authenticated_admin_client.post(
            "/api/cart/submit/",
            {"shipping_address": VALID_SHIPPING_ADDRESS},
            format="json",
        )

        assert response.status_code == 400
        assert "empty" in response.json()["error"].lower()

    def test_submit_without_address(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 1},
            format="json",
        )

        response = authenticated_admin_client.post("/api/cart/submit/")

        assert response.status_code == 400
        assert "shipping_address" in response.json()["error"].lower()

    def test_submit_with_invalid_address(
        self, authenticated_admin_client: APIClient, product: Dict[str, Any]
    ) -> None:
        authenticated_admin_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 1},
            format="json",
        )

        response = authenticated_admin_client.post(
            "/api/cart/submit/",
            {
                "shipping_address": {
                    "street_line_1": "Invalid Street",
                    "city": "Nowhere",
                    "state": "XX",
                    "postal_code": "00000",
                    "country": "US",
                }
            },
            format="json",
        )

        assert response.status_code == 400
        assert "verification" in response.json()["error"].lower()
