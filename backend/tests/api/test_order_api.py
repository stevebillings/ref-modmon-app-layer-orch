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
class TestOrderList:
    def test_list_orders_empty(self, api_client):
        response = api_client.get("/api/orders/")
        assert response.status_code == 200
        assert response.json() == {"results": []}

    def test_list_orders(self, api_client, product):
        # Create orders
        for _ in range(3):
            api_client.post(
                "/api/cart/items/",
                {"product_id": product["id"], "quantity": 1},
                format="json",
            )
            api_client.post("/api/cart/submit/")

        response = api_client.get("/api/orders/")
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 3

    def test_orders_include_total(self, api_client, product):
        api_client.post(
            "/api/cart/items/",
            {"product_id": product["id"], "quantity": 5},
            format="json",
        )
        api_client.post("/api/cart/submit/")

        response = api_client.get("/api/orders/")
        order = response.json()["results"][0]
        assert order["total"] == "50.00"

    def test_orders_newest_first(self, api_client, product):
        for _ in range(3):
            api_client.post(
                "/api/cart/items/",
                {"product_id": product["id"], "quantity": 1},
                format="json",
            )
            api_client.post("/api/cart/submit/")

        response = api_client.get("/api/orders/")
        results = response.json()["results"]

        # Verify descending order
        for i in range(len(results) - 1):
            assert results[i]["submitted_at"] >= results[i + 1]["submitted_at"]


@pytest.mark.django_db
class TestFullWorkflow:
    def test_complete_order_workflow(self, api_client):
        # 1. Create products
        product1 = api_client.post(
            "/api/products/",
            {"name": "Widget", "price": "15.00", "stock_quantity": 50},
            format="json",
        ).json()

        product2 = api_client.post(
            "/api/products/",
            {"name": "Gadget", "price": "25.00", "stock_quantity": 30},
            format="json",
        ).json()

        # 2. Add items to cart
        api_client.post(
            "/api/cart/items/",
            {"product_id": product1["id"], "quantity": 2},
            format="json",
        )
        cart_response = api_client.post(
            "/api/cart/items/",
            {"product_id": product2["id"], "quantity": 3},
            format="json",
        )

        cart = cart_response.json()
        assert len(cart["items"]) == 2
        # 15*2 + 25*3 = 30 + 75 = 105
        assert cart["total"] == "105.00"

        # 3. Verify stock reserved
        products = api_client.get("/api/products/").json()["results"]
        widget = next(p for p in products if p["name"] == "Widget")
        gadget = next(p for p in products if p["name"] == "Gadget")
        assert widget["stock_quantity"] == 48
        assert gadget["stock_quantity"] == 27

        # 4. Submit order
        order = api_client.post("/api/cart/submit/").json()
        assert order["total"] == "105.00"
        assert len(order["items"]) == 2

        # 5. Verify cart is empty
        cart = api_client.get("/api/cart/").json()
        assert cart["items"] == []

        # 6. Verify order appears in history
        orders = api_client.get("/api/orders/").json()["results"]
        assert len(orders) == 1
        assert orders[0]["total"] == "105.00"

        # 7. Stock remains decremented
        products = api_client.get("/api/products/").json()["results"]
        widget = next(p for p in products if p["name"] == "Widget")
        gadget = next(p for p in products if p["name"] == "Gadget")
        assert widget["stock_quantity"] == 48
        assert gadget["stock_quantity"] == 27
