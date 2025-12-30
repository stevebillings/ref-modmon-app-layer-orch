from decimal import Decimal

import pytest

from application.services.product_service import ProductService
from domain.exceptions import (
    DuplicateProductError,
    ProductInUseError,
    ProductNotFoundError,
    ValidationError,
)
from infrastructure.django_app.unit_of_work import UnitOfWork


@pytest.mark.django_db
class TestProductService:
    def test_create_product(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        product = service.create_product(
            name="Test Product",
            price="19.99",
            stock_quantity=100,
        )

        assert product.name == "Test Product"
        assert product.price == Decimal("19.99")
        assert product.stock_quantity == 100

    def test_create_product_with_decimal_price(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        product = service.create_product(
            name="Decimal Price Product",
            price=Decimal("25.50"),
            stock_quantity=50,
        )

        assert product.price == Decimal("25.50")

    def test_create_product_validates_name(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        with pytest.raises(ValidationError) as exc_info:
            service.create_product(name="", price="10.00", stock_quantity=10)

        assert exc_info.value.field == "name"

    def test_create_product_validates_price(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        with pytest.raises(ValidationError) as exc_info:
            service.create_product(
                name="Test", price=Decimal("0"), stock_quantity=10
            )

        assert exc_info.value.field == "price"

    def test_create_product_validates_stock_quantity(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        with pytest.raises(ValidationError) as exc_info:
            service.create_product(
                name="Test", price="10.00", stock_quantity=-1
            )

        assert exc_info.value.field == "stock_quantity"

    def test_create_product_duplicate_name_raises(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        service.create_product(
            name="Unique Product", price="10.00", stock_quantity=10
        )

        with pytest.raises(DuplicateProductError) as exc_info:
            service.create_product(
                name="Unique Product", price="20.00", stock_quantity=20
            )

        assert "Unique Product" in str(exc_info.value)

    def test_get_all_products(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        service.create_product(name="Zebra", price="10.00", stock_quantity=10)
        service.create_product(name="Apple", price="5.00", stock_quantity=20)

        products = service.get_all_products()

        assert len(products) >= 2
        names = [p.name for p in products]
        # Should be alphabetically ordered
        assert names.index("Apple") < names.index("Zebra")

    def test_delete_product(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        product = service.create_product(
            name="To Delete", price="10.00", stock_quantity=10
        )

        service.delete_product(str(product.id))

        products = service.get_all_products()
        assert not any(p.id == product.id for p in products)

    def test_delete_nonexistent_product_raises(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        with pytest.raises(ProductNotFoundError):
            service.delete_product("00000000-0000-0000-0000-000000000000")

    def test_delete_product_invalid_uuid_raises(self):
        uow = UnitOfWork()
        service = ProductService(uow)

        with pytest.raises(ProductNotFoundError):
            service.delete_product("not-a-uuid")


@pytest.mark.django_db
class TestProductDeletionConstraints:
    def test_delete_product_in_cart_raises(self):
        from application.services.cart_service import CartService

        uow = UnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)

        product = product_service.create_product(
            name="In Cart Product", price="10.00", stock_quantity=10
        )

        cart_service.add_item(str(product.id), quantity=1)

        with pytest.raises(ProductInUseError) as exc_info:
            product_service.delete_product(str(product.id))

        assert "cart" in str(exc_info.value).lower()

    def test_delete_product_in_order_raises(self):
        from application.services.cart_service import CartService

        uow = UnitOfWork()
        product_service = ProductService(uow)
        cart_service = CartService(uow)

        product = product_service.create_product(
            name="Ordered Product", price="10.00", stock_quantity=10
        )

        cart_service.add_item(str(product.id), quantity=1)
        cart_service.submit_cart()

        with pytest.raises(ProductInUseError) as exc_info:
            product_service.delete_product(str(product.id))

        assert "order" in str(exc_info.value).lower()
