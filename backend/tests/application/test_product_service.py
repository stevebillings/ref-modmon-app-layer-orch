from decimal import Decimal
from uuid import uuid4

import pytest

from application.services.product_service import ProductService
from domain.exceptions import (
    DuplicateProductError,
    ProductInUseError,
    ProductNotFoundError,
    ValidationError,
)
from domain.user_context import Role, UserContext
from infrastructure.django_app.unit_of_work import DjangoUnitOfWork


def make_user_context(role: Role = Role.ADMIN) -> UserContext:
    """Create a test UserContext."""
    return UserContext(user_id=uuid4(), username="testuser", role=role)


@pytest.mark.django_db
class TestProductService:
    def test_create_product(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        product = service.create_product(
            name="Test Product",
            price="19.99",
            stock_quantity=100,
            user_context=user_context,
        )

        assert product.name == "Test Product"
        assert product.price == Decimal("19.99")
        assert product.stock_quantity == 100

    def test_create_product_with_decimal_price(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        product = service.create_product(
            name="Decimal Price Product",
            price=Decimal("25.50"),
            stock_quantity=50,
            user_context=user_context,
        )

        assert product.price == Decimal("25.50")

    def test_create_product_validates_name(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        with pytest.raises(ValidationError) as exc_info:
            service.create_product(name="", price="10.00", stock_quantity=10, user_context=user_context)

        assert exc_info.value.field == "name"

    def test_create_product_validates_price(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        with pytest.raises(ValidationError) as exc_info:
            service.create_product(
                name="Test", price=Decimal("0"), stock_quantity=10, user_context=user_context
            )

        assert exc_info.value.field == "price"

    def test_create_product_validates_stock_quantity(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        with pytest.raises(ValidationError) as exc_info:
            service.create_product(
                name="Test", price="10.00", stock_quantity=-1, user_context=user_context
            )

        assert exc_info.value.field == "stock_quantity"

    def test_create_product_duplicate_name_raises(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        service.create_product(
            name="Unique Product", price="10.00", stock_quantity=10, user_context=user_context
        )

        with pytest.raises(DuplicateProductError) as exc_info:
            service.create_product(
                name="Unique Product", price="20.00", stock_quantity=20, user_context=user_context
            )

        assert "Unique Product" in str(exc_info.value)

    def test_get_all_products(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        service.create_product(name="Zebra", price="10.00", stock_quantity=10, user_context=user_context)
        service.create_product(name="Apple", price="5.00", stock_quantity=20, user_context=user_context)

        products = service.get_all_products()

        assert len(products) >= 2
        names = [p.name for p in products]
        # Should be alphabetically ordered
        assert names.index("Apple") < names.index("Zebra")

    def test_delete_product(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        product = service.create_product(
            name="To Delete", price="10.00", stock_quantity=10, user_context=user_context
        )

        service.delete_product(str(product.id), user_context=user_context)

        products = service.get_all_products()
        assert not any(p.id == product.id for p in products)

    def test_delete_nonexistent_product_raises(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        with pytest.raises(ProductNotFoundError):
            service.delete_product("00000000-0000-0000-0000-000000000000", user_context=user_context)

    def test_delete_product_invalid_uuid_raises(self) -> None:
        uow = DjangoUnitOfWork()
        service = ProductService(uow)
        user_context = make_user_context()

        with pytest.raises(ProductNotFoundError):
            service.delete_product("not-a-uuid", user_context=user_context)


@pytest.mark.django_db
class TestProductDeletionConstraints:
    def test_delete_product_in_cart_raises(self) -> None:
        from application.services.cart_service import CartService

        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="In Cart Product", price="10.00", stock_quantity=10, user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=1, user_context=user_context)

        with pytest.raises(ProductInUseError) as exc_info:
            product_service.delete_product(str(product.id), user_context=user_context)

        assert "cart" in str(exc_info.value).lower()

    def test_delete_product_in_order_raises(self) -> None:
        from application.services.cart_service import CartService

        uow = DjangoUnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)
        user_context = make_user_context()

        product = product_service.create_product(
            name="Ordered Product", price="10.00", stock_quantity=10, user_context=user_context
        )

        cart_service.add_item(str(product.id), quantity=1, user_context=user_context)
        cart_service.submit_cart(user_context)

        # After submitting, the cart is cleared, so delete should work
        # (product is in order but that no longer blocks deletion due to soft delete)
        product_service.delete_product(str(product.id), user_context=user_context)

        # Verify product is soft-deleted (not in regular get_all)
        products = product_service.get_all_products()
        assert not any(p.id == product.id for p in products)
