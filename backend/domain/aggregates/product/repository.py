from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from domain.aggregates.product.entity import Product
from domain.pagination import PaginatedResult, ProductFilter


class ProductRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Product]:
        """Get all products ordered alphabetically by name."""
        pass

    @abstractmethod
    def get_by_id(self, product_id: UUID) -> Product | None:
        """Get a product by its ID."""
        pass

    @abstractmethod
    def get_by_id_for_update(self, product_id: UUID) -> Product | None:
        """
        Get a product by its ID with a row-level lock for update.

        Use this method when you need to read a product and then modify it
        (e.g., stock updates) to prevent race conditions from concurrent requests.
        The lock is held until the current transaction commits.
        """
        pass

    @abstractmethod
    def save(self, product: Product) -> Product:
        """
        Save a product (create or update).

        Raises:
            DuplicateProductError: If a product with the same name already exists
        """
        pass

    @abstractmethod
    def delete(self, product_id: UUID) -> None:
        """Delete a product by its ID."""
        pass

    @abstractmethod
    def exists_by_name(self, name: str) -> bool:
        """Check if a product with the given name exists."""
        pass

    @abstractmethod
    def is_in_any_cart(self, product_id: UUID) -> bool:
        """Check if the product is in any cart."""
        pass

    @abstractmethod
    def is_in_any_order(self, product_id: UUID) -> bool:
        """Check if the product is referenced in any order."""
        pass

    @abstractmethod
    def find_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        filter: ProductFilter | None = None,
    ) -> PaginatedResult[Product]:
        """
        Find products with pagination and optional filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filter: Optional filter criteria

        Returns:
            PaginatedResult containing the products and pagination metadata
        """
        pass
