import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def product(api_client):
    response = api_client.post(
        "/api/products/",
        {"name": "Test Product", "price": "10.00", "stock_quantity": 100},
        format="json",
    )
    return response.json()


@pytest.mark.django_db
class TestCartGet:
    def test_get_empty_cart(self, api_client):
        response = api_client.get("/api/cart/")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == "0"
        assert data["item_count"] == 0


@pytest.mark.django_db
class TestCartAddItem:
    def test_add_item_to_cart(self, api_client, product):
        response = api_client.post(
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

    def test_add_item_reserves_stock(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 25},
            format="json",
        )

        response = api_client.get("/api/products/")
        products = response.json()["results"]
        updated_product = next(p for p in products if p["id"] == product["id"])
        assert updated_product["stock_quantity"] == 75

    def test_add_same_product_increases_quantity(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 3},
            format="json",
        )
        response = api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 2},
            format="json",
        )

        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 5

    def test_add_insufficient_stock(self, api_client, product):
        response = api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 200},
            format="json",
        )

        assert response.status_code == 400
        assert "stock" in response.json()["error"].lower()

    def test_add_nonexistent_product(self, api_client):
        response = api_client.post(
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
    def test_update_item_quantity(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )

        response = api_client.patch(
            f"/api/cart/items/{product['id']}/",
            {"quantity": 8},
            format="json",
        )

        assert response.status_code == 200
        assert response.json()["items"][0]["quantity"] == 8

    def test_update_adjusts_stock(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 10},
            format="json",
        )

        api_client.patch(
            f"/api/cart/items/{product['id']}/",
            {"quantity": 15},
            format="json",
        )

        response = api_client.get("/api/products/")
        products = response.json()["results"]
        updated_product = next(p for p in products if p["id"] == product["id"])
        assert updated_product["stock_quantity"] == 85

    def test_update_insufficient_stock(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )

        response = api_client.patch(
            f"/api/cart/items/{product['id']}/",
            {"quantity": 200},
            format="json",
        )

        assert response.status_code == 400

    def test_update_nonexistent_item(self, api_client):
        response = api_client.patch(
            "/api/cart/items/00000000-0000-0000-0000-000000000000/",
            {"quantity": 5},
            format="json",
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCartRemoveItem:
    def test_remove_item(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )

        response = api_client.delete(
            f"/api/cart/items/{product['id']}/remove/"
        )

        assert response.status_code == 200
        assert response.json()["items"] == []

    def test_remove_releases_stock(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 25},
            format="json",
        )

        api_client.delete(f"/api/cart/items/{product['id']}/remove/")

        response = api_client.get("/api/products/")
        products = response.json()["results"]
        updated_product = next(p for p in products if p["id"] == product["id"])
        assert updated_product["stock_quantity"] == 100

    def test_remove_nonexistent_item(self, api_client):
        response = api_client.delete(
            "/api/cart/items/00000000-0000-0000-0000-000000000000/remove/"
        )

        assert response.status_code == 404


@pytest.mark.django_db
class TestCartSubmit:
    def test_submit_cart(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 3},
            format="json",
        )

        response = api_client.post("/api/cart/submit/")

        assert response.status_code == 201
        order = response.json()
        assert len(order["items"]) == 1
        assert order["items"][0]["product_name"] == "Test Product"
        assert order["total"] == "30.00"

    def test_submit_clears_cart(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 2},
            format="json",
        )

        api_client.post("/api/cart/submit/")

        response = api_client.get("/api/cart/")
        assert response.json()["items"] == []

    def test_submit_empty_cart(self, api_client):
        response = api_client.post("/api/cart/submit/")

        assert response.status_code == 400
        assert "empty" in response.json()["error"].lower()
