from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.aggregates.product.entity import Product
from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.order.entities import Order, OrderItem
from infrastructure.django_app.repositories.product_repository import (
    DjangoProductRepository,
)
from infrastructure.django_app.repositories.cart_repository import (
    DjangoCartRepository,
)
from infrastructure.django_app.repositories.order_repository import (
    DjangoOrderRepository,
)


@pytest.mark.django_db
class TestProductRepository:
    def test_save_and_get_product(self):
        repo = DjangoProductRepository()
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Test Product",
            price=Decimal("19.99"),
            stock_quantity=100,
            created_at=datetime.now(),
        )

        saved = repo.save(product)

        assert saved.id == product_id
        assert saved.name == "Test Product"
        assert saved.price == Decimal("19.99")
        assert saved.stock_quantity == 100

    def test_get_by_id(self):
        repo = DjangoProductRepository()
        product_id = uuid4()
        product = Product(
            id=product_id,
            name="Findable Product",
            price=Decimal("10.00"),
            stock_quantity=50,
            created_at=datetime.now(),
        )
        repo.save(product)

        found = repo.get_by_id(product_id)

        assert found is not None
        assert found.name == "Findable Product"

    def test_get_by_id_not_found(self):
        repo = DjangoProductRepository()
        assert repo.get_by_id(uuid4()) is None

    def test_get_all_ordered_by_name(self):
        repo = DjangoProductRepository()
        repo.save(Product(
            id=uuid4(), name="Zebra", price=Decimal("10.00"),
            stock_quantity=10, created_at=datetime.now()
        ))
        repo.save(Product(
            id=uuid4(), name="Apple", price=Decimal("5.00"),
            stock_quantity=20, created_at=datetime.now()
        ))
        repo.save(Product(
            id=uuid4(), name="Mango", price=Decimal("7.50"),
            stock_quantity=15, created_at=datetime.now()
        ))

        products = repo.get_all()

        assert [p.name for p in products] == ["Apple", "Mango", "Zebra"]

    def test_delete_product(self):
        repo = DjangoProductRepository()
        product_id = uuid4()
        repo.save(Product(
            id=product_id, name="To Delete", price=Decimal("10.00"),
            stock_quantity=5, created_at=datetime.now()
        ))

        repo.delete(product_id)

        assert repo.get_by_id(product_id) is None

    def test_exists_by_name(self):
        repo = DjangoProductRepository()
        repo.save(Product(
            id=uuid4(), name="Exists Product", price=Decimal("10.00"),
            stock_quantity=5, created_at=datetime.now()
        ))

        assert repo.exists_by_name("Exists Product") is True
        assert repo.exists_by_name("Nonexistent") is False

    def test_update_stock_quantity(self):
        repo = DjangoProductRepository()
        product_id = uuid4()
        original = Product(
            id=product_id, name="Stock Product", price=Decimal("10.00"),
            stock_quantity=100, created_at=datetime.now()
        )
        repo.save(original)

        updated = original.with_stock_quantity(50)
        repo.save(updated)

        found = repo.get_by_id(product_id)
        assert found.stock_quantity == 50


@pytest.mark.django_db
class TestCartRepository:
    def test_get_cart_creates_if_not_exists(self):
        repo = DjangoCartRepository()

        cart = repo.get_cart()

        assert cart is not None
        assert cart.items == []

    def test_get_cart_returns_same_cart(self):
        repo = DjangoCartRepository()
        cart1 = repo.get_cart()
        cart2 = repo.get_cart()

        assert cart1.id == cart2.id

    def test_add_item(self):
        repo = DjangoCartRepository()
        cart = repo.get_cart()
        item = CartItem(
            id=uuid4(),
            product_id=uuid4(),
            product_name="Test Product",
            unit_price=Decimal("15.00"),
            quantity=2,
        )

        saved_item = repo.add_item(cart.id, item)

        assert saved_item.product_name == "Test Product"
        assert saved_item.quantity == 2

        # Verify item is in cart
        updated_cart = repo.get_cart()
        assert len(updated_cart.items) == 1

    def test_update_item_quantity(self):
        repo = DjangoCartRepository()
        cart = repo.get_cart()
        item = CartItem(
            id=uuid4(),
            product_id=uuid4(),
            product_name="Update Test",
            unit_price=Decimal("10.00"),
            quantity=1,
        )
        saved_item = repo.add_item(cart.id, item)

        updated_item = saved_item.with_quantity(5)
        repo.update_item(updated_item)

        updated_cart = repo.get_cart()
        assert updated_cart.items[0].quantity == 5

    def test_delete_item(self):
        repo = DjangoCartRepository()
        cart = repo.get_cart()
        item = CartItem(
            id=uuid4(),
            product_id=uuid4(),
            product_name="Delete Test",
            unit_price=Decimal("10.00"),
            quantity=1,
        )
        saved_item = repo.add_item(cart.id, item)

        repo.delete_item(saved_item.id)

        updated_cart = repo.get_cart()
        assert len(updated_cart.items) == 0

    def test_clear_items(self):
        repo = DjangoCartRepository()
        cart = repo.get_cart()

        # Add multiple items
        for i in range(3):
            repo.add_item(cart.id, CartItem(
                id=uuid4(),
                product_id=uuid4(),
                product_name=f"Product {i}",
                unit_price=Decimal("10.00"),
                quantity=1,
            ))

        assert len(repo.get_cart().items) == 3

        repo.clear_items(cart.id)

        assert len(repo.get_cart().items) == 0


@pytest.mark.django_db
class TestOrderRepository:
    def test_save_and_get_orders(self):
        repo = DjangoOrderRepository()
        order_id = uuid4()
        order = Order(
            id=order_id,
            items=[
                OrderItem(
                    id=uuid4(),
                    order_id=order_id,
                    product_id=uuid4(),
                    product_name="Test Product",
                    unit_price=Decimal("20.00"),
                    quantity=2,
                )
            ],
            submitted_at=datetime.now(),
        )

        saved = repo.save(order)

        assert saved.id == order_id
        assert len(saved.items) == 1
        assert saved.items[0].product_name == "Test Product"

    def test_get_all_orders_newest_first(self):
        repo = DjangoOrderRepository()

        # Create orders
        for i in range(3):
            order_id = uuid4()
            repo.save(Order(
                id=order_id,
                items=[
                    OrderItem(
                        id=uuid4(),
                        order_id=order_id,
                        product_id=uuid4(),
                        product_name=f"Product {i}",
                        unit_price=Decimal("10.00"),
                        quantity=1,
                    )
                ],
                submitted_at=datetime.now(),
            ))

        orders = repo.get_all()

        assert len(orders) == 3
        # Newest first means descending order by submitted_at
        for i in range(len(orders) - 1):
            assert orders[i].submitted_at >= orders[i + 1].submitted_at


@pytest.mark.django_db
class TestProductInCartAndOrder:
    def test_is_in_any_cart(self):
        product_repo = DjangoProductRepository()
        cart_repo = DjangoCartRepository()

        product_id = uuid4()
        cart = cart_repo.get_cart()

        # Not in cart initially
        assert product_repo.is_in_any_cart(product_id) is False

        # Add to cart
        cart_repo.add_item(cart.id, CartItem(
            id=uuid4(),
            product_id=product_id,
            product_name="In Cart",
            unit_price=Decimal("10.00"),
            quantity=1,
        ))

        assert product_repo.is_in_any_cart(product_id) is True

    def test_is_in_any_order(self):
        product_repo = DjangoProductRepository()
        order_repo = DjangoOrderRepository()

        product_id = uuid4()

        # Not in order initially
        assert product_repo.is_in_any_order(product_id) is False

        # Create order with product
        order_id = uuid4()
        order_repo.save(Order(
            id=order_id,
            items=[
                OrderItem(
                    id=uuid4(),
                    order_id=order_id,
                    product_id=product_id,
                    product_name="In Order",
                    unit_price=Decimal("10.00"),
                    quantity=1,
                )
            ],
            submitted_at=datetime.now(),
        ))

        assert product_repo.is_in_any_order(product_id) is True
