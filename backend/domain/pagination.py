"""
Domain types for pagination and filtering.

These are generic types that can be used by any aggregate's repository.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ProductFilter:
    """
    Filter criteria for product queries.

    All fields are optional. Unset fields (None) mean no filtering on that field.
    """

    search: str | None = None  # Search by name (case-insensitive contains)
    min_price: Decimal | None = None
    max_price: Decimal | None = None
    in_stock: bool | None = None  # If True, only products with stock > 0


@dataclass(frozen=True)
class PaginatedResult(Generic[T]):
    """
    A page of results with pagination metadata.

    Attributes:
        items: The items on this page
        total_count: Total number of items matching the query (across all pages)
        page: Current page number (1-indexed)
        page_size: Number of items per page
    """

    items: list[T]
    total_count: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        """Calculate total number of pages."""
        if self.page_size <= 0:
            return 0
        return (self.total_count + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.page > 1
