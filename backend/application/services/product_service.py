from decimal import Decimal
from typing import List
from uuid import UUID

from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.product.entity import Product
from domain.aggregates.product.validation import validate_product_name
from domain.exceptions import (
    DuplicateProductError,
    PermissionDeniedError,
    ProductInUseError,
    ProductNotFoundError,
)
from domain.pagination import PaginatedResult, ProductFilter
from domain.user_context import UserContext


class ProductService:
    """
    Application service for product operations.

    Handles product CRUD operations with validation, authorization,
    and event collection.
    """

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all_products(self) -> List[Product]:
        """
        Get all products ordered alphabetically by name.

        No authorization required - product catalog is public.
        """
        return self.uow.get_product_repository().get_all()

    def get_products_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
    ) -> PaginatedResult[Product]:
        """
        Get products with pagination and optional filtering.

        No authorization required - product catalog is public.

        Args:
            page: Page number (1-indexed, default 1)
            page_size: Items per page (default 20, max 100)
            search: Search term for product name (case-insensitive)
            min_price: Minimum price filter
            max_price: Maximum price filter
            in_stock: If True, only return products with stock > 0
        """
        # Enforce reasonable limits
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        # Build filter if any criteria provided
        filter = None
        if any([search, min_price is not None, max_price is not None, in_stock is not None]):
            filter = ProductFilter(
                search=search,
                min_price=min_price,
                max_price=max_price,
                in_stock=in_stock,
            )

        return self.uow.get_product_repository().find_paginated(
            page=page,
            page_size=page_size,
            filter=filter,
        )

    def create_product(
        self,
        name: str,
        price: Decimal | str,
        stock_quantity: int,
        user_context: UserContext,
    ) -> Product:
        """
        Create a new product.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            ValidationError: If validation fails
            DuplicateProductError: If a product with the same name exists
        """
        if not user_context.is_admin():
            raise PermissionDeniedError(
                "create_product", "Only administrators can create products"
            )

        # Validate name early to check for duplicates with normalized value
        validated_name = validate_product_name(name)

        # Check for duplicate name (fast path for common case)
        if self.uow.get_product_repository().exists_by_name(validated_name):
            raise DuplicateProductError(validated_name)

        # Create product using factory method (validates all fields)
        product = Product.create(
            name=name,
            price=price,
            stock_quantity=stock_quantity,
        )

        # Repository handles race condition by raising DuplicateProductError
        # if another request created the product after our exists_by_name check
        saved_product = self.uow.get_product_repository().save(product)
        self.uow.collect_events_from(product)
        return saved_product

    def delete_product(self, product_id: str, user_context: UserContext) -> None:
        """
        Delete a product.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            ProductNotFoundError: If product doesn't exist
            ProductInUseError: If product is in a cart or order
        """
        if not user_context.is_admin():
            raise PermissionDeniedError(
                "delete_product", "Only administrators can delete products"
            )

        try:
            pid = UUID(product_id)
        except ValueError:
            raise ProductNotFoundError(product_id)

        # Use get_by_id_for_update to acquire a row-level lock, preventing
        # race conditions where another request adds this product to cart
        # while we're checking and deleting (add_item also uses this lock)
        product = self.uow.get_product_repository().get_by_id_for_update(pid)
        if product is None:
            raise ProductNotFoundError(product_id)

        # Check if in cart
        if self.uow.get_product_repository().is_in_any_cart(pid):
            raise ProductInUseError(
                product_id, "Product is currently in a cart"
            )

        # Check if in any order
        if self.uow.get_product_repository().is_in_any_order(pid):
            raise ProductInUseError(
                product_id, "Product has been ordered and cannot be deleted"
            )

        self.uow.get_product_repository().delete(pid)
