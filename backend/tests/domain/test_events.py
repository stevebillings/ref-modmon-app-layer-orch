"""Tests for domain events."""

from decimal import Decimal
from uuid import uuid4

import pytest

from domain.events import DomainEvent
from domain.aggregates.product.events import StockReserved, StockReleased
from domain.aggregates.cart.events import CartItemAdded, CartSubmitted
from domain.aggregates.product.entity import Product
from domain.aggregates.cart.entities import Cart


class TestDomainEvent:
    """Tests for base DomainEvent class."""

    def test_event_has_unique_id(self) -> None:
        event1 = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=9,
            actor_id="test",
        )
        event2 = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=9,
            actor_id="test",
        )
        assert event1.event_id != event2.event_id

    def test_event_has_timestamp(self) -> None:
        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=9,
            actor_id="test",
        )
        assert event.occurred_at is not None

    def test_event_is_immutable(self) -> None:
        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=9,
            actor_id="test",
        )
        with pytest.raises(AttributeError):
            event.quantity_reserved = 5  # type: ignore

    def test_event_to_dict(self) -> None:
        product_id = uuid4()
        event = StockReserved(
            product_id=product_id,
            product_name="Test Product",
            quantity_reserved=5,
            remaining_stock=95,
            actor_id="user-123",
        )
        result = event.to_dict()

        assert result["event_type"] == "StockReserved"
        assert result["product_id"] == str(product_id)
        assert result["product_name"] == "Test Product"
        assert result["quantity_reserved"] == 5
        assert result["remaining_stock"] == 95
        assert result["actor_id"] == "user-123"
        assert "event_id" in result
        assert "occurred_at" in result

    def test_get_event_type(self) -> None:
        event = StockReleased(
            product_id=uuid4(),
            product_name="Test",
            quantity_released=1,
            new_stock=10,
            actor_id="test",
        )
        assert event.get_event_type() == "StockReleased"


class TestProductEvents:
    """Tests for Product aggregate event raising."""

    def test_reserve_stock_raises_event(self) -> None:
        product = Product.create(
            name="Test Product",
            price=Decimal("10.00"),
            stock_quantity=100,
        )

        product.reserve_stock(10, actor_id="user-123")

        events = product.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], StockReserved)
        assert events[0].product_id == product.id
        assert events[0].quantity_reserved == 10
        assert events[0].remaining_stock == 90
        assert events[0].actor_id == "user-123"

    def test_release_stock_raises_event(self) -> None:
        product = Product.create(
            name="Test Product",
            price=Decimal("10.00"),
            stock_quantity=90,
        )

        product.release_stock(10, actor_id="system")

        events = product.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], StockReleased)
        assert events[0].quantity_released == 10
        assert events[0].new_stock == 100
        assert events[0].actor_id == "system"

    def test_clear_domain_events(self) -> None:
        product = Product.create(
            name="Test Product",
            price=Decimal("10.00"),
            stock_quantity=100,
        )
        product.reserve_stock(10)
        assert len(product.get_domain_events()) == 1

        product.clear_domain_events()
        assert len(product.get_domain_events()) == 0


class TestCartEvents:
    """Tests for Cart aggregate event raising."""

    def test_add_item_raises_event(self) -> None:
        cart = Cart.create(user_id=uuid4())
        product_id = uuid4()

        cart.add_item(
            product_id=product_id,
            product_name="Test Product",
            unit_price=Decimal("19.99"),
            quantity=2,
            actor_id="user-456",
        )

        events = cart.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], CartItemAdded)
        assert events[0].cart_id == cart.id
        assert events[0].product_id == product_id
        assert events[0].quantity == 2
        assert events[0].actor_id == "user-456"

    def test_submit_raises_event(self) -> None:
        cart = Cart.create(user_id=uuid4())
        cart.add_item(
            product_id=uuid4(),
            product_name="Test Product",
            unit_price=Decimal("10.00"),
            quantity=1,
        )
        cart.clear_domain_events()  # Clear the add_item event

        order = cart.submit(actor_id="user-789")

        events = cart.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], CartSubmitted)
        assert events[0].cart_id == cart.id
        assert events[0].order_id == order.id
        assert events[0].total == Decimal("10.00")
        assert events[0].item_count == 1
        assert events[0].actor_id == "user-789"

    def test_multiple_operations_collect_events(self) -> None:
        cart = Cart.create(user_id=uuid4())
        product1_id = uuid4()
        product2_id = uuid4()

        cart.add_item(product1_id, "Product 1", Decimal("10.00"), 1)
        cart.add_item(product2_id, "Product 2", Decimal("20.00"), 2)

        events = cart.get_domain_events()
        assert len(events) == 2
