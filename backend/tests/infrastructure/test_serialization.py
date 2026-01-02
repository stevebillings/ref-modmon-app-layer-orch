from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from domain.aggregates.product.entity import Product
from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.order.entities import Order, OrderItem
from infrastructure.django_app.serialization import to_dict


class TestToDict:
    def test_none_returns_none(self) -> None:
        assert to_dict(None) is None

    def test_primitive_types_unchanged(self) -> None:
        assert to_dict("hello") == "hello"
        assert to_dict(42) == 42
        assert to_dict(3.14) == 3.14
        assert to_dict(True) is True

    def test_uuid_to_string(self) -> None:
        uid = UUID("12345678-1234-5678-1234-567812345678")
        assert to_dict(uid) == "12345678-1234-5678-1234-567812345678"

    def test_datetime_to_isoformat(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0)
        assert to_dict(dt) == "2024-01-15T10:30:00"

    def test_decimal_to_string(self) -> None:
        d = Decimal("19.99")
        assert to_dict(d) == "19.99"

    def test_list_of_primitives(self) -> None:
        assert to_dict([1, 2, 3]) == [1, 2, 3]

    def test_list_of_uuids(self) -> None:
        uuids = [uuid4(), uuid4()]
        result = to_dict(uuids)
        assert all(isinstance(r, str) for r in result)

    def test_product_entity(self) -> None:
        product_id = uuid4()
        now = datetime(2024, 1, 15, 10, 0, 0)
        product = Product(
            id=product_id,
            name="Test Product",
            price=Decimal("19.99"),
            stock_quantity=100,
            created_at=now,
        )

        result = to_dict(product)

        assert result == {
            "id": str(product_id),
            "name": "Test Product",
            "price": "19.99",
            "stock_quantity": 100,
            "created_at": "2024-01-15T10:00:00",
        }

    def test_cart_with_items(self) -> None:
        cart_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()
        now = datetime(2024, 1, 15, 10, 0, 0)

        cart = Cart(
            id=cart_id,
            items=[
                CartItem(
                    id=item_id,
                    product_id=product_id,
                    product_name="Test Product",
                    unit_price=Decimal("10.00"),
                    quantity=2,
                )
            ],
            created_at=now,
        )

        result = to_dict(cart)

        assert result["id"] == str(cart_id)
        assert result["created_at"] == "2024-01-15T10:00:00"
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name"] == "Test Product"
        assert result["items"][0]["unit_price"] == "10.00"
        assert result["items"][0]["quantity"] == 2

    def test_order_with_items(self) -> None:
        order_id = uuid4()
        item_id = uuid4()
        product_id = uuid4()
        now = datetime(2024, 1, 15, 10, 0, 0)

        order = Order(
            id=order_id,
            items=[
                OrderItem(
                    id=item_id,
                    order_id=order_id,
                    product_id=product_id,
                    product_name="Test Product",
                    unit_price=Decimal("15.00"),
                    quantity=3,
                )
            ],
            submitted_at=now,
        )

        result = to_dict(order)

        assert result["id"] == str(order_id)
        assert result["submitted_at"] == "2024-01-15T10:00:00"
        assert len(result["items"]) == 1
        assert result["items"][0]["product_name"] == "Test Product"

    def test_empty_cart(self) -> None:
        cart = Cart(
            id=uuid4(),
            items=[],
            created_at=datetime.now(),
        )

        result = to_dict(cart)
        assert result["items"] == []
