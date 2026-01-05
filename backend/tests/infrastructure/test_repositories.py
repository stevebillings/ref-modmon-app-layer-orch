from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from domain.aggregates.product.entity import Product
from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.order.entities import Order, OrderItem
from domain.aggregates.order.value_objects import VerifiedAddress
from infrastructure.django_app.repositories.product_repository import (
    DjangoProductRepository,
)
from infrastructure.django_app.repositories.cart_repository import (
    DjangoCartRepository,
)
from infrastructure.django_app.repositories.order_repository import (
    DjangoOrderRepository,
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


@pytest.mark.django_db
class TestProductRepository:
    def test_save_and_get_product(self) -> None:
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

    def test_get_by_id(self) -> None:
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

    def test_get_by_id_not_found(self) -> None:
        repo = DjangoProductRepository()
        assert repo.get_by_id(uuid4()) is None

    def test_get_all_ordered_by_name(self) -> None:
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

    def test_delete_product(self) -> None:
        repo = DjangoProductRepository()
        product_id = uuid4()
        repo.save(Product(
            id=product_id, name="To Delete", price=Decimal("10.00"),
            stock_quantity=5, created_at=datetime.now()
        ))

        repo.delete(product_id)

        assert repo.get_by_id(product_id) is None

    def test_exists_by_name(self) -> None:
        repo = DjangoProductRepository()
        repo.save(Product(
            id=uuid4(), name="Exists Product", price=Decimal("10.00"),
            stock_quantity=5, created_at=datetime.now()
        ))

        assert repo.exists_by_name("Exists Product") is True
        assert repo.exists_by_name("Nonexistent") is False

    def test_update_stock_quantity(self) -> None:
        repo = DjangoProductRepository()
        product_id = uuid4()
        product = Product(
            id=product_id, name="Stock Product", price=Decimal("10.00"),
            stock_quantity=100, created_at=datetime.now()
        )
        repo.save(product)

        # Use mutable approach - modify and save
        product.reserve_stock(50)
        repo.save(product)

        found = repo.get_by_id(product_id)
        assert found is not None
        assert found.stock_quantity == 50


@pytest.mark.django_db
class TestCartRepository:
    def test_get_cart_creates_if_not_exists(self) -> None:
        repo = DjangoCartRepository()
        user_id = uuid4()

        cart = repo.get_cart_for_user(user_id)

        assert cart is not None
        assert cart.items == []
        assert cart.user_id == user_id

    def test_get_cart_returns_same_cart(self) -> None:
        repo = DjangoCartRepository()
        user_id = uuid4()
        cart1 = repo.get_cart_for_user(user_id)
        cart2 = repo.get_cart_for_user(user_id)

        assert cart1.id == cart2.id

    def test_save_with_new_item(self) -> None:
        repo = DjangoCartRepository()
        user_id = uuid4()
        cart = repo.get_cart_for_user(user_id)

        # Add item using aggregate method
        cart.add_item(
            product_id=uuid4(),
            product_name="Test Product",
            unit_price=Decimal("15.00"),
            quantity=2,
        )
        repo.save(cart)

        # Verify item is persisted
        updated_cart = repo.get_cart_for_user(user_id)
        assert len(updated_cart.items) == 1
        assert updated_cart.items[0].product_name == "Test Product"
        assert updated_cart.items[0].quantity == 2

    def test_save_updates_item_quantity(self) -> None:
        repo = DjangoCartRepository()
        user_id = uuid4()
        cart = repo.get_cart_for_user(user_id)
        product_id = uuid4()

        # Add initial item
        cart.add_item(
            product_id=product_id,
            product_name="Update Test",
            unit_price=Decimal("10.00"),
            quantity=1,
        )
        repo.save(cart)

        # Update quantity using aggregate method
        cart.update_item_quantity(product_id, 5)
        repo.save(cart)

        updated_cart = repo.get_cart_for_user(user_id)
        assert updated_cart.items[0].quantity == 5

    def test_save_removes_deleted_item(self) -> None:
        repo = DjangoCartRepository()
        user_id = uuid4()
        cart = repo.get_cart_for_user(user_id)
        product_id = uuid4()

        # Add item
        cart.add_item(
            product_id=product_id,
            product_name="Delete Test",
            unit_price=Decimal("10.00"),
            quantity=1,
        )
        repo.save(cart)
        assert len(repo.get_cart_for_user(user_id).items) == 1

        # Remove using aggregate method
        cart.remove_item(product_id)
        repo.save(cart)

        updated_cart = repo.get_cart_for_user(user_id)
        assert len(updated_cart.items) == 0

    def test_save_clears_all_items(self) -> None:
        repo = DjangoCartRepository()
        user_id = uuid4()
        cart = repo.get_cart_for_user(user_id)

        # Add multiple items
        for i in range(3):
            cart.add_item(
                product_id=uuid4(),
                product_name=f"Product {i}",
                unit_price=Decimal("10.00"),
                quantity=1,
            )
        repo.save(cart)
        assert len(repo.get_cart_for_user(user_id).items) == 3

        # Clear items (simulate what submit does)
        cart.items = []
        repo.save(cart)

        assert len(repo.get_cart_for_user(user_id).items) == 0


@pytest.mark.django_db
class TestOrderRepository:
    def test_save_and_get_orders(self) -> None:
        repo = DjangoOrderRepository()
        order_id = uuid4()
        user_id = uuid4()
        order = Order(
            id=order_id,
            user_id=user_id,
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
            shipping_address=TEST_SHIPPING_ADDRESS,
            submitted_at=datetime.now(),
        )

        saved = repo.save(order)

        assert saved.id == order_id
        assert saved.user_id == user_id
        assert len(saved.items) == 1
        assert saved.items[0].product_name == "Test Product"
        assert saved.shipping_address.city == "ANYTOWN"

    def test_get_all_orders_newest_first(self) -> None:
        repo = DjangoOrderRepository()
        user_id = uuid4()

        # Create orders
        for i in range(3):
            order_id = uuid4()
            repo.save(Order(
                id=order_id,
                user_id=user_id,
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
                shipping_address=TEST_SHIPPING_ADDRESS,
                submitted_at=datetime.now(),
            ))

        orders = repo.get_all()

        assert len(orders) == 3
        # Newest first means descending order by submitted_at
        for i in range(len(orders) - 1):
            current_time = orders[i].submitted_at
            next_time = orders[i + 1].submitted_at
            assert current_time is not None
            assert next_time is not None
            assert current_time >= next_time


@pytest.mark.django_db
class TestProductInCartAndOrder:
    def test_is_in_any_cart(self) -> None:
        product_repo = DjangoProductRepository()
        cart_repo = DjangoCartRepository()

        product_id = uuid4()
        user_id = uuid4()
        cart = cart_repo.get_cart_for_user(user_id)

        # Not in cart initially
        assert product_repo.is_in_any_cart(product_id) is False

        # Add to cart using aggregate method
        cart.add_item(
            product_id=product_id,
            product_name="In Cart",
            unit_price=Decimal("10.00"),
            quantity=1,
        )
        cart_repo.save(cart)

        assert product_repo.is_in_any_cart(product_id) is True

    def test_is_in_any_order(self) -> None:
        product_repo = DjangoProductRepository()
        order_repo = DjangoOrderRepository()

        product_id = uuid4()

        # Not in order initially
        assert product_repo.is_in_any_order(product_id) is False

        # Create order with product
        order_id = uuid4()
        user_id = uuid4()
        order_repo.save(Order(
            id=order_id,
            user_id=user_id,
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
            shipping_address=TEST_SHIPPING_ADDRESS,
            submitted_at=datetime.now(),
        ))

        assert product_repo.is_in_any_order(product_id) is True
