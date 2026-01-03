from typing import List
from uuid import UUID

from django.db import IntegrityError

from domain.aggregates.product.entity import Product
from domain.aggregates.product.repository import ProductRepository
from domain.exceptions import DuplicateProductError
from infrastructure.django_app.models import (
    CartItemModel,
    OrderItemModel,
    ProductModel,
)


class DjangoProductRepository(ProductRepository):
    def get_all(self) -> List[Product]:
        """Get all products ordered alphabetically by name."""
        return [
            self._to_domain(model) for model in ProductModel.objects.all()
        ]

    def get_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by its ID."""
        try:
            model = ProductModel.objects.get(id=product_id)
            return self._to_domain(model)
        except ProductModel.DoesNotExist:
            return None

    def get_by_id_for_update(self, product_id: UUID) -> Product | None:
        """
        Get a product by its ID with a row-level lock for update.

        Uses SELECT ... FOR UPDATE to acquire an exclusive lock on the row,
        preventing concurrent transactions from modifying it until this
        transaction commits.
        """
        try:
            model = ProductModel.objects.select_for_update().get(id=product_id)
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

    @staticmethod
    def _to_domain(model: ProductModel) -> Product:
        """Convert ORM model to domain entity."""
        return Product(
            id=model.id,
            name=model.name,
            price=model.price,
            stock_quantity=model.stock_quantity,
            created_at=model.created_at,
        )
