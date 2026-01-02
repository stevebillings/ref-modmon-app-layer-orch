import pytest

from application.services.cart_service import CartService
from application.services.order_service import OrderService
from application.services.product_service import ProductService
from infrastructure.django_app.unit_of_work import UnitOfWork


@pytest.mark.django_db
class TestOrderService:
    def test_get_all_orders_empty(self) -> None:
        uow = UnitOfWork()
        service = OrderService(uow)

        orders = service.get_all_orders()

        assert orders == []

    def test_get_all_orders(self) -> None:
        uow = UnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        order_service = OrderService(uow)

        # Create products and orders
        product = product_service.create_product(
            name="Order List Test", price="10.00", stock_quantity=100
        )

        for i in range(3):
            cart_service.add_item(str(product.id), quantity=1)
            cart_service.submit_cart()

        orders = order_service.get_all_orders()

        assert len(orders) == 3

    def test_orders_newest_first(self) -> None:
        uow = UnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        order_service = OrderService(uow)

        product = product_service.create_product(
            name="Order Sorting Test", price="10.00", stock_quantity=100
        )

        # Create orders
        for _ in range(3):
            cart_service.add_item(str(product.id), quantity=1)
            cart_service.submit_cart()

        orders = order_service.get_all_orders()

        # Verify descending order by submitted_at
        for i in range(len(orders) - 1):
            current_time = orders[i].submitted_at
            next_time = orders[i + 1].submitted_at
            assert current_time is not None
            assert next_time is not None
            assert current_time >= next_time
