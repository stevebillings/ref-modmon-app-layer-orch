from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.aggregates.product.entity import Product
from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.order.entities import Order, OrderItem
from domain.aggregates.order.value_objects import VerifiedAddress
from domain.exceptions import (
    CartItemNotFoundError,
    EmptyCartError,
    InsufficientStockError,
)


TEST_SHIPPING_ADDRESS = VerifiedAddress(
    street_line_1="123 MAIN ST",
    street_line_2=None,
    city="ANYTOWN",
    state="CA",
    postal_code="90210",
    country="US",
    verification_id="TEST-123",
)


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

    def test_has_sufficient_stock(self) -> None:
        product = Product(
            id=uuid4(),
            name="Test",
            price=Decimal("10.00"),
            stock_quantity=100,
            created_at=datetime.now(),
        )

        assert product.has_sufficient_stock(50) is True
        assert product.has_sufficient_stock(100) is True
        assert product.has_sufficient_stock(101) is False

    def test_reserve_stock(self) -> None:
        product = Product(
            id=uuid4(),
            name="Test",
            price=Decimal("10.00"),
            stock_quantity=100,
            created_at=datetime.now(),
        )

        product.reserve_stock(30)
        assert product.stock_quantity == 70

        product.reserve_stock(20)
        assert product.stock_quantity == 50

    def test_reserve_stock_insufficient_raises(self) -> None:
        product = Product(
            id=uuid4(),
            name="Test",
            price=Decimal("10.00"),
            stock_quantity=10,
            created_at=datetime.now(),
        )

        with pytest.raises(InsufficientStockError):
            product.reserve_stock(20)

    def test_release_stock(self) -> None:
        product = Product(
            id=uuid4(),
            name="Test",
            price=Decimal("10.00"),
            stock_quantity=50,
            created_at=datetime.now(),
        )

        product.release_stock(25)
        assert product.stock_quantity == 75


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

        assert item.get_subtotal() == Decimal("29.97")

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
        user_id = uuid4()
        now = datetime.now()
        cart = Cart(id=cart_id, user_id=user_id, items=[], created_at=now)

        assert cart.id == cart_id
        assert cart.user_id == user_id
        assert cart.items == []
        assert cart.created_at == now

    def test_get_total_empty_cart(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())
        assert cart.get_total() == Decimal("0")

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
        cart = Cart(id=uuid4(), user_id=uuid4(), items=items, created_at=datetime.now())

        # 10*2 + 5.50*3 = 20 + 16.50 = 36.50
        assert cart.get_total() == Decimal("36.50")

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
        cart = Cart(id=uuid4(), user_id=uuid4(), items=items, created_at=datetime.now())

        assert cart.get_item_count() == 5

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
        cart = Cart(id=uuid4(), user_id=uuid4(), items=items, created_at=datetime.now())

        item = cart.get_item_by_product_id(product_id)
        assert item is not None
        assert item.product_name == "Target Product"

    def test_get_item_by_product_id_not_found(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())
        assert cart.get_item_by_product_id(uuid4()) is None

    def test_add_item_new(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())
        product_id = uuid4()

        cart.add_item(product_id, "Test Product", Decimal("15.00"), 2)

        assert len(cart.items) == 1
        assert cart.items[0].product_id == product_id
        assert cart.items[0].quantity == 2

    def test_add_item_merges_existing(self) -> None:
        product_id = uuid4()
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())

        cart.add_item(product_id, "Test Product", Decimal("10.00"), 2)
        cart.add_item(product_id, "Test Product", Decimal("10.00"), 3)

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5

    def test_update_item_quantity(self) -> None:
        product_id = uuid4()
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())
        cart.add_item(product_id, "Test", Decimal("10.00"), 5)

        diff = cart.update_item_quantity(product_id, 8)

        assert diff == 3
        assert cart.items[0].quantity == 8

    def test_update_item_quantity_not_found_raises(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())

        with pytest.raises(CartItemNotFoundError):
            cart.update_item_quantity(uuid4(), 5)

    def test_remove_item(self) -> None:
        product_id = uuid4()
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())
        cart.add_item(product_id, "Test", Decimal("10.00"), 5)

        removed = cart.remove_item(product_id)

        assert removed.quantity == 5
        assert len(cart.items) == 0

    def test_remove_item_not_found_raises(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())

        with pytest.raises(CartItemNotFoundError):
            cart.remove_item(uuid4())

    def test_submit_creates_order(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())
        cart.add_item(uuid4(), "Product A", Decimal("10.00"), 2)
        cart.add_item(uuid4(), "Product B", Decimal("5.00"), 3)

        order = cart.submit(shipping_address=TEST_SHIPPING_ADDRESS)

        assert len(order.items) == 2
        assert order.get_total() == Decimal("35.00")
        assert len(cart.items) == 0  # Cart is cleared
        assert order.shipping_address == TEST_SHIPPING_ADDRESS

    def test_submit_empty_cart_raises(self) -> None:
        cart = Cart(id=uuid4(), user_id=uuid4(), items=[], created_at=datetime.now())

        with pytest.raises(EmptyCartError):
            cart.submit(shipping_address=TEST_SHIPPING_ADDRESS)


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

        assert item.get_subtotal() == Decimal("25.98")


class TestOrder:
    def test_create_order(self) -> None:
        order_id = uuid4()
        user_id = uuid4()
        now = datetime.now()
        order = Order(
            id=order_id,
            user_id=user_id,
            items=[],
            shipping_address=TEST_SHIPPING_ADDRESS,
            submitted_at=now,
        )

        assert order.id == order_id
        assert order.user_id == user_id
        assert order.items == []
        assert order.shipping_address == TEST_SHIPPING_ADDRESS
        assert order.submitted_at == now

    def test_total(self) -> None:
        order_id = uuid4()
        user_id = uuid4()
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
        order = Order(
            id=order_id,
            user_id=user_id,
            items=items,
            shipping_address=TEST_SHIPPING_ADDRESS,
            submitted_at=datetime.now(),
        )

        # 10*2 + 7.50*4 = 20 + 30 = 50
        assert order.get_total() == Decimal("50.00")
