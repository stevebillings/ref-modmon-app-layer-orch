from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.aggregates.product.entity import Product
from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.order.entities import Order, OrderItem


class TestProduct:
    def test_create_product(self) -> None:
        product_id = uuid4()
        now = datetime.now()
        product = Product(
            id=product_id,
            name="Test Product",
            price=Decimal("19.99"),
            stock_quantity=100,
            created_at=now,
        )

        assert product.id == product_id
        assert product.name == "Test Product"
        assert product.price == Decimal("19.99")
        assert product.stock_quantity == 100
        assert product.created_at == now

    def test_product_is_frozen(self) -> None:
        product = Product(
            id=uuid4(),
            name="Test",
            price=Decimal("10.00"),
            stock_quantity=10,
            created_at=datetime.now(),
        )

        with pytest.raises(AttributeError):
            product.name = "New Name"  # type: ignore[misc]

    def test_with_stock_quantity(self) -> None:
        product = Product(
            id=uuid4(),
            name="Test",
            price=Decimal("10.00"),
            stock_quantity=100,
            created_at=datetime.now(),
        )

        updated = product.with_stock_quantity(50)

        assert updated.stock_quantity == 50
        assert updated.id == product.id
        assert updated.name == product.name
        assert updated.price == product.price
        assert product.stock_quantity == 100  # Original unchanged


class TestCartItem:
    def test_create_cart_item(self) -> None:
        item_id = uuid4()
        product_id = uuid4()
        item = CartItem(
            id=item_id,
            product_id=product_id,
            product_name="Test Product",
            unit_price=Decimal("9.99"),
            quantity=3,
        )

        assert item.id == item_id
        assert item.product_id == product_id
        assert item.product_name == "Test Product"
        assert item.unit_price == Decimal("9.99")
        assert item.quantity == 3

    def test_subtotal(self) -> None:
        item = CartItem(
            id=uuid4(),
            product_id=uuid4(),
            product_name="Test",
            unit_price=Decimal("9.99"),
            quantity=3,
        )

        assert item.subtotal == Decimal("29.97")

    def test_with_quantity(self) -> None:
        item = CartItem(
            id=uuid4(),
            product_id=uuid4(),
            product_name="Test",
            unit_price=Decimal("10.00"),
            quantity=2,
        )

        updated = item.with_quantity(5)

        assert updated.quantity == 5
        assert updated.id == item.id
        assert item.quantity == 2  # Original unchanged


class TestCart:
    def test_create_cart(self) -> None:
        cart_id = uuid4()
        now = datetime.now()
        cart = Cart(id=cart_id, items=[], created_at=now)

        assert cart.id == cart_id
        assert cart.items == []
        assert cart.created_at == now

    def test_total_empty_cart(self) -> None:
        cart = Cart(id=uuid4(), items=[], created_at=datetime.now())
        assert cart.total == Decimal("0")

    def test_total_with_items(self) -> None:
        items = [
            CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name="Product A",
                unit_price=Decimal("10.00"),
                quantity=2,
            ),
            CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name="Product B",
                unit_price=Decimal("5.50"),
                quantity=3,
            ),
        ]
        cart = Cart(id=uuid4(), items=items, created_at=datetime.now())

        # 10*2 + 5.50*3 = 20 + 16.50 = 36.50
        assert cart.total == Decimal("36.50")

    def test_item_count(self) -> None:
        items = [
            CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name="Product A",
                unit_price=Decimal("10.00"),
                quantity=2,
            ),
            CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name="Product B",
                unit_price=Decimal("5.50"),
                quantity=3,
            ),
        ]
        cart = Cart(id=uuid4(), items=items, created_at=datetime.now())

        assert cart.item_count == 5

    def test_get_item_by_product_id(self) -> None:
        product_id = uuid4()
        items = [
            CartItem(
                id=uuid4(),
                product_id=product_id,
                product_name="Target Product",
                unit_price=Decimal("10.00"),
                quantity=2,
            ),
            CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name="Other Product",
                unit_price=Decimal("5.00"),
                quantity=1,
            ),
        ]
        cart = Cart(id=uuid4(), items=items, created_at=datetime.now())

        item = cart.get_item_by_product_id(product_id)
        assert item is not None
        assert item.product_name == "Target Product"

    def test_get_item_by_product_id_not_found(self) -> None:
        cart = Cart(id=uuid4(), items=[], created_at=datetime.now())
        assert cart.get_item_by_product_id(uuid4()) is None

    def test_with_items(self) -> None:
        cart = Cart(id=uuid4(), items=[], created_at=datetime.now())
        new_items = [
            CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name="New Item",
                unit_price=Decimal("15.00"),
                quantity=1,
            )
        ]

        updated = cart.with_items(new_items)

        assert len(updated.items) == 1
        assert updated.id == cart.id
        assert len(cart.items) == 0  # Original unchanged


class TestOrderItem:
    def test_create_order_item(self) -> None:
        item_id = uuid4()
        order_id = uuid4()
        product_id = uuid4()
        item = OrderItem(
            id=item_id,
            order_id=order_id,
            product_id=product_id,
            product_name="Test Product",
            unit_price=Decimal("12.99"),
            quantity=2,
        )

        assert item.id == item_id
        assert item.order_id == order_id
        assert item.product_id == product_id
        assert item.product_name == "Test Product"
        assert item.unit_price == Decimal("12.99")
        assert item.quantity == 2

    def test_subtotal(self) -> None:
        item = OrderItem(
            id=uuid4(),
            order_id=uuid4(),
            product_id=uuid4(),
            product_name="Test",
            unit_price=Decimal("12.99"),
            quantity=2,
        )

        assert item.subtotal == Decimal("25.98")


class TestOrder:
    def test_create_order(self) -> None:
        order_id = uuid4()
        now = datetime.now()
        order = Order(id=order_id, items=[], submitted_at=now)

        assert order.id == order_id
        assert order.items == []
        assert order.submitted_at == now

    def test_total(self) -> None:
        order_id = uuid4()
        items = [
            OrderItem(
                id=uuid4(),
                order_id=order_id,
                product_id=uuid4(),
                product_name="Product A",
                unit_price=Decimal("10.00"),
                quantity=2,
            ),
            OrderItem(
                id=uuid4(),
                order_id=order_id,
                product_id=uuid4(),
                product_name="Product B",
                unit_price=Decimal("7.50"),
                quantity=4,
            ),
        ]
        order = Order(id=order_id, items=items, submitted_at=datetime.now())

        # 10*2 + 7.50*4 = 20 + 30 = 50
        assert order.total == Decimal("50.00")
