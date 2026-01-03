from typing import List
from uuid import UUID

from django.db import IntegrityError
from django.db.models import QuerySet

from domain.aggregates.product.entity import Product
from domain.aggregates.product.repository import ProductRepository
from domain.exceptions import DuplicateProductError
from domain.pagination import PaginatedResult, ProductFilter
from infrastructure.django_app.models import (
    CartItemModel,
    OrderItemModel,
    ProductModel,
)


class DjangoProductRepository(ProductRepository):
    def _base_queryset(self, include_deleted: bool = False) -> "QuerySet[ProductModel]":
        """Get base queryset with optional soft-delete filtering."""
        qs = ProductModel.objects.all()
        if not include_deleted:
            qs = qs.filter(deleted_at__isnull=True)
        return qs

    def get_all(self, include_deleted: bool = False) -> List[Product]:
        """Get all products ordered alphabetically by name."""
        return [
            self._to_domain(model) for model in self._base_queryset(include_deleted)
        ]

    def get_by_id(
        self, product_id: UUID, include_deleted: bool = False
    ) -> Product | None:
        """Get a product by its ID."""
        try:
            model = self._base_queryset(include_deleted).get(id=product_id)
            return self._to_domain(model)
        except ProductModel.DoesNotExist:
            return None

    def get_by_id_for_update(
        self, product_id: UUID, include_deleted: bool = False
    ) -> Product | None:
        """
        Get a product by its ID with a row-level lock for update.

        Uses SELECT ... FOR UPDATE to acquire an exclusive lock on the row,
        preventing concurrent transactions from modifying it until this
        transaction commits.
        """
        try:
            model = self._base_queryset(include_deleted).select_for_update().get(
                id=product_id
            )
            return self._to_domain(model)
        except ProductModel.DoesNotExist:
            return None

    def save(self, product: Product) -> Product:
        """
        Save a product (create or update).

        Raises:
            DuplicateProductError: If a product with the same name already exists
        """
        try:
            model, _ = ProductModel.objects.update_or_create(
                id=product.id,
                defaults={
                    "name": product.name,
                    "price": product.price,
                    "stock_quantity": product.stock_quantity,
                    "deleted_at": product.deleted_at,
                },
            )
        except IntegrityError:
            raise DuplicateProductError(product.name)
        # Refresh to get auto-generated created_at if new
        model.refresh_from_db()
        return self._to_domain(model)

    def delete(self, product_id: UUID) -> None:
        """Delete a product by its ID."""
        ProductModel.objects.filter(id=product_id).delete()

    def exists_by_name(self, name: str) -> bool:
        """Check if a product with the given name exists."""
        return ProductModel.objects.filter(name=name).exists()

    def is_in_any_cart(self, product_id: UUID) -> bool:
        """Check if the product is in any cart."""
        return CartItemModel.objects.filter(product_id=product_id).exists()

    def is_in_any_order(self, product_id: UUID) -> bool:
        """Check if the product is referenced in any order."""
        return OrderItemModel.objects.filter(product_id=product_id).exists()

    def find_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filter: ProductFilter | None = None,
        include_deleted: bool = False,
    ) -> PaginatedResult[Product]:
        """Find products with pagination and optional filtering."""
        queryset = self._base_queryset(include_deleted)

        # Apply filters
        if filter:
            queryset = self._apply_filter(queryset, filter)

        # Get total count before pagination
        total_count = queryset.count()

        # Apply pagination (ordering is defined on the model's Meta)
        offset = (page - 1) * page_size
        models = list(queryset[offset : offset + page_size])

        return PaginatedResult(
            items=[self._to_domain(m) for m in models],
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    def _apply_filter(queryset: "QuerySet[ProductModel]", filter: ProductFilter) -> "QuerySet[ProductModel]":
        """Apply filter criteria to the queryset."""
        if filter.search:
            queryset = queryset.filter(name__icontains=filter.search)
        if filter.min_price is not None:
            queryset = queryset.filter(price__gte=filter.min_price)
        if filter.max_price is not None:
            queryset = queryset.filter(price__lte=filter.max_price)
        if filter.in_stock is True:
            queryset = queryset.filter(stock_quantity__gt=0)
        return queryset

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        """Convert ORM model to domain entity."""
        return Product(
            id=model.id,
            name=model.name,
            price=model.price,
            stock_quantity=model.stock_quantity,
            created_at=model.created_at,
            deleted_at=model.deleted_at,
        )
