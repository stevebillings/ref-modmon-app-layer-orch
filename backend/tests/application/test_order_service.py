from uuid import uuid4

import pytest

from application.services.cart_service import CartService
from application.services.order_service import OrderService
from application.services.product_service import ProductService
from domain.user_context import Role, UserContext
from infrastructure.django_app.unit_of_work import DjangoUnitOfWork


def make_user_context(role: Role = Role.ADMIN) -> UserContext:
    """Create a test UserContext."""
    return UserContext(user_id=uuid4(), username="testuser", role=role)


@pytest.mark.django_db
class TestOrderService:
    def test_get_all_orders_empty(self) -> None:
        uow = DjangoUnitOfWork()
        service = OrderService(uow)
        user_context = make_user_context()

        orders = service.get_orders(user_context)

        assert orders == []

    def test_get_all_orders(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        order_service = OrderService(uow)
        user_context = make_user_context()

        # Create products and orders
        product = product_service.create_product(
            name="Order List Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        for i in range(3):
            cart_service.add_item(str(product.id), quantity=1, user_context=user_context)
            cart_service.submit_cart(user_context)

        orders = order_service.get_orders(user_context)

        assert len(orders) == 3

    def test_orders_newest_first(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        order_service = OrderService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Order Sorting Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        # Create orders
        for _ in range(3):
            cart_service.add_item(str(product.id), quantity=1, user_context=user_context)
            cart_service.submit_cart(user_context)

        orders = order_service.get_orders(user_context)

        # Verify descending order by submitted_at
        for i in range(len(orders) - 1):
            current_time = orders[i].submitted_at
            next_time = orders[i + 1].submitted_at
            assert current_time is not None
            assert next_time is not None
            assert current_time >= next_time
