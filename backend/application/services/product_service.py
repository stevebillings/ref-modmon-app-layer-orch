from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import uuid4

from domain.aggregates.product.entity import Product
from domain.exceptions import (
    DuplicateProductError,
    ProductInUseError,
    ProductNotFoundError,
)
from domain.validation import (
    validate_product_name,
    validate_product_price,
    validate_stock_quantity,
)
from infrastructure.django_app.unit_of_work import UnitOfWork


class ProductService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all_products(self) -> List[Product]:
        """Get all products ordered alphabetically by name."""
        return self.uow.products.get_all()

    def create_product(
        self, name: str, price: Decimal | str, stock_quantity: int
    ) -> Product:
        """
        Create a new product.

        Raises:
            ValidationError: If validation fails
            DuplicateProductError: If a product with the same name exists
        """
        # Validate inputs
        validated_name = validate_product_name(name)
        validated_price = validate_product_price(price)
        validated_quantity = validate_stock_quantity(stock_quantity)

        # Check for duplicate name
        if self.uow.products.exists_by_name(validated_name):
            raise DuplicateProductError(validated_name)

        # Create and save
        product = Product(
            id=uuid4(),
            name=validated_name,
            price=validated_price,
            stock_quantity=validated_quantity,
            created_at=datetime.now(),
        )

        return self.uow.products.save(product)

    def delete_product(self, product_id: str) -> None:
        """
        Delete a product.

        Raises:
            ProductNotFoundError: If product doesn't exist
            ProductInUseError: If product is in a cart or order
        """
        from uuid import UUID

        try:
            pid = UUID(product_id)
        except ValueError:
            raise ProductNotFoundError(product_id)

        product = self.uow.products.get_by_id(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        # Check if in cart
        if self.uow.products.is_in_any_cart(pid):
            raise ProductInUseError(
                product_id, "Product is currently in a cart"
            )

        # Check if in any order
        if self.uow.products.is_in_any_order(pid):
            raise ProductInUseError(
                product_id, "Product has been ordered and cannot be deleted"
            )

        self.uow.products.delete(pid)
