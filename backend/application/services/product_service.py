from decimal import Decimal
from typing import List
from uuid import UUID

from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.product.entity import Product
from domain.aggregates.product.validation import validate_product_name
from domain.exceptions import (
    DuplicateProductError,
    PermissionDeniedError,
    ProductAlreadyDeletedError,
    ProductInUseError,
    ProductNotDeletedError,
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
        include_deleted: bool = False,
        user_context: UserContext | None = None,
    ) -> PaginatedResult[Product]:
        """
        Get products with pagination and optional filtering.

        No authorization required - product catalog is public.
        Only admins can see soft-deleted products.

        Args:
            page: Page number (1-indexed, default 1)
            page_size: Items per page (default 20, max 100)
            search: Search term for product name (case-insensitive)
            min_price: Minimum price filter
            max_price: Maximum price filter
            in_stock: If True, only return products with stock > 0
            include_deleted: If True and user is admin, include soft-deleted products
            user_context: User context for authorization check
        """
        # Enforce reasonable limits
        page = max(1, page)
        page_size = max(1, min(100, page_size))

        # Only admins can see deleted products
        if include_deleted and (user_context is None or not user_context.is_admin()):
            include_deleted = False

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
            include_deleted=include_deleted,
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
        Soft-delete a product.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            ProductNotFoundError: If product doesn't exist
            ProductAlreadyDeletedError: If product is already deleted
            ProductInUseError: If product is in a cart
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
            # Check if it's already deleted or truly doesn't exist
            existing = self.uow.get_product_repository().get_by_id_for_update(
                pid, include_deleted=True
            )
            if existing and existing.is_deleted:
                raise ProductAlreadyDeletedError(product_id)
            raise ProductNotFoundError(product_id)

        # Check if in cart (still blocked - can't soft-delete products in carts)
        if self.uow.get_product_repository().is_in_any_cart(pid):
            raise ProductInUseError(
                product_id, "Product is currently in a cart"
            )

        # Note: We no longer block deletion for products in orders.
        # Order history is preserved via the snapshot pattern (OrderItem
        # stores product_name and unit_price at order time).

        # Perform soft delete
        product.soft_delete(actor_id=user_context.actor_id)

        # Persist and collect events
        self.uow.get_product_repository().save(product)
        self.uow.collect_events_from(product)

    def restore_product(self, product_id: str, user_context: UserContext) -> Product:
        """
        Restore a soft-deleted product.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            ProductNotFoundError: If product doesn't exist
            ProductNotDeletedError: If product is not deleted
        """
        if not user_context.is_admin():
            raise PermissionDeniedError(
                "restore_product", "Only administrators can restore products"
            )

        try:
            pid = UUID(product_id)
        except ValueError:
            raise ProductNotFoundError(product_id)

        # Get product including deleted ones
        product = self.uow.get_product_repository().get_by_id_for_update(
            pid, include_deleted=True
        )
        if product is None:
            raise ProductNotFoundError(product_id)

        if not product.is_deleted:
            raise ProductNotDeletedError(product_id)

        # Restore the product
        product.restore(actor_id=user_context.actor_id)

        # Persist and collect events
        saved = self.uow.get_product_repository().save(product)
        self.uow.collect_events_from(product)

        return saved
