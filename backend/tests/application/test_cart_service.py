from decimal import Decimal
from uuid import uuid4

import pytest

from application.services.cart_service import CartService
from application.services.product_service import ProductService
from domain.exceptions import (
    CartItemNotFoundError,
    EmptyCartError,
    InsufficientStockError,
    ProductNotFoundError,
    ValidationError,
)
from domain.user_context import Role, UserContext
from infrastructure.django_app.unit_of_work import DjangoUnitOfWork


def make_user_context(role: Role = Role.ADMIN) -> UserContext:
    """Create a test UserContext."""
    return UserContext(user_id=uuid4(), username="testuser", role=role)


@pytest.mark.django_db
class TestCartService:
    def test_get_empty_cart(self) -> None:
        uow = DjangoUnitOfWork()
        service = CartService(uow)
        user_context = make_user_context()

        cart = service.get_cart(user_context)

        assert cart is not None
        assert cart.items == []
        assert cart.get_total() == Decimal("0")

    def test_add_item_to_cart(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Cart Test Product", price="15.00", stock_quantity=10,
            user_context=user_context
        )

        cart = cart_service.add_item(str(product.id), quantity=2, user_context=user_context)

        assert len(cart.items) == 1
        assert cart.items[0].product_name == "Cart Test Product"
        assert cart.items[0].quantity == 2
        assert cart.items[0].unit_price == Decimal("15.00")
        assert cart.get_total() == Decimal("30.00")

    def test_add_item_reserves_stock(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Stock Reserve Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=25, user_context=user_context)

        products = product_service.get_all_products()
        updated_product = next(p for p in products if p.id == product.id)
        assert updated_product.stock_quantity == 75

    def test_add_same_product_increases_quantity(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Add Twice Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=3, user_context=user_context)
        cart = cart_service.add_item(str(product.id), quantity=2, user_context=user_context)

        assert len(cart.items) == 1
        assert cart.items[0].quantity == 5

        # Stock should reflect total reserved
        products = product_service.get_all_products()
        updated_product = next(p for p in products if p.id == product.id)
        assert updated_product.stock_quantity == 95

    def test_add_item_insufficient_stock_raises(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Low Stock Product", price="10.00", stock_quantity=5,
            user_context=user_context
        )

        with pytest.raises(InsufficientStockError) as exc_info:
            cart_service.add_item(str(product.id), quantity=10, user_context=user_context)

        assert exc_info.value.available == 5
        assert exc_info.value.requested == 10

    def test_add_item_invalid_quantity_raises(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Quantity Test", price="10.00", stock_quantity=10,
            user_context=user_context
        )

        with pytest.raises(ValidationError):
            cart_service.add_item(str(product.id), quantity=0, user_context=user_context)

    def test_add_nonexistent_product_raises(self) -> None:
        uow = DjangoUnitOfWork()
        cart_service = CartService(uow)
        user_context = make_user_context()

        with pytest.raises(ProductNotFoundError):
            cart_service.add_item(
                "00000000-0000-0000-0000-000000000000", quantity=1,
                user_context=user_context
            )


@pytest.mark.django_db
class TestUpdateItemQuantity:
    def test_update_item_quantity(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Update Qty Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=5, user_context=user_context)
        cart = cart_service.update_item_quantity(str(product.id), quantity=8, user_context=user_context)

        assert cart.items[0].quantity == 8

    def test_update_adjusts_stock_increase(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Stock Adjust Inc", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=10, user_context=user_context)  # Stock: 90
        cart_service.update_item_quantity(str(product.id), quantity=15, user_context=user_context)  # Stock: 85

        products = product_service.get_all_products()
        updated_product = next(p for p in products if p.id == product.id)
        assert updated_product.stock_quantity == 85

    def test_update_adjusts_stock_decrease(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Stock Adjust Dec", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=10, user_context=user_context)  # Stock: 90
        cart_service.update_item_quantity(str(product.id), quantity=3, user_context=user_context)  # Stock: 97

        products = product_service.get_all_products()
        updated_product = next(p for p in products if p.id == product.id)
        assert updated_product.stock_quantity == 97

    def test_update_insufficient_stock_raises(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Stock Limit Test", price="10.00", stock_quantity=10,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=5, user_context=user_context)  # Stock: 5

        with pytest.raises(InsufficientStockError):
            cart_service.update_item_quantity(str(product.id), quantity=20, user_context=user_context)

    def test_update_nonexistent_item_raises(self) -> None:
        uow = DjangoUnitOfWork()
        cart_service = CartService(uow)
        user_context = make_user_context()

        with pytest.raises(CartItemNotFoundError):
            cart_service.update_item_quantity(
                "00000000-0000-0000-0000-000000000000", quantity=5,
                user_context=user_context
            )


@pytest.mark.django_db
class TestRemoveItem:
    def test_remove_item(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Remove Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=5, user_context=user_context)
        cart = cart_service.remove_item(str(product.id), user_context=user_context)

        assert len(cart.items) == 0

    def test_remove_releases_stock(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Release Stock Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=25, user_context=user_context)  # Stock: 75
        cart_service.remove_item(str(product.id), user_context=user_context)  # Stock: 100

        products = product_service.get_all_products()
        updated_product = next(p for p in products if p.id == product.id)
        assert updated_product.stock_quantity == 100

    def test_remove_nonexistent_item_raises(self) -> None:
        uow = DjangoUnitOfWork()
        cart_service = CartService(uow)
        user_context = make_user_context()

        with pytest.raises(CartItemNotFoundError):
            cart_service.remove_item("00000000-0000-0000-0000-000000000000", user_context=user_context)


@pytest.mark.django_db
class TestSubmitCart:
    def test_submit_cart_creates_order(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Submit Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=3, user_context=user_context)
        order = cart_service.submit_cart(user_context)

        assert order is not None
        assert len(order.items) == 1
        assert order.items[0].product_name == "Submit Test"
        assert order.items[0].quantity == 3
        assert order.get_total() == Decimal("30.00")

    def test_submit_clears_cart(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Clear Cart Test", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=2, user_context=user_context)
        cart_service.submit_cart(user_context)

        cart = cart_service.get_cart(user_context)
        assert len(cart.items) == 0

    def test_submit_stock_remains_decremented(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Stock After Submit", price="10.00", stock_quantity=100,
            user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=20, user_context=user_context)  # Stock: 80
        cart_service.submit_cart(user_context)

        products = product_service.get_all_products()
        updated_product = next(p for p in products if p.id == product.id)
        assert updated_product.stock_quantity == 80

    def test_submit_empty_cart_raises(self) -> None:
        uow = DjangoUnitOfWork()
        cart_service = CartService(uow)
        user_context = make_user_context()

        # Ensure cart is empty
        cart = cart_service.get_cart(user_context)
        assert len(cart.items) == 0

        with pytest.raises(EmptyCartError):
            cart_service.submit_cart(user_context)

    def test_submit_with_multiple_items(self) -> None:
        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product1 = product_service.create_product(
            name="Multi Item 1", price="10.00", stock_quantity=50,
            user_context=user_context
        )
        product2 = product_service.create_product(
            name="Multi Item 2", price="20.00", stock_quantity=50,
            user_context=user_context
        )

        cart_service.add_item(str(product1.id), quantity=2, user_context=user_context)
        cart_service.add_item(str(product2.id), quantity=3, user_context=user_context)
        order = cart_service.submit_cart(user_context)

        assert len(order.items) == 2
        # 10*2 + 20*3 = 20 + 60 = 80
        assert order.get_total() == Decimal("80.00")
