"""
Product report query definitions.

This module defines the query parameters and result types for the product report,
which aggregates data from multiple aggregates (Product, Cart, Order).

This is part of the Simple Query Separation pattern - queries that need to read
across aggregate boundaries bypass the domain layer and use optimized read paths.
"""

from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class ProductReportQuery:
    """
    Query parameters for the product report.

    This defines what data to include in the report. Queries are simple
    data structures that describe what to fetch, without any business logic.

    Pagination:
        page: Page number (1-indexed)
        page_size: Items per page

    Filters:
        include_deleted: Include soft-deleted products
        search: Search by product name (case-insensitive contains)
        low_stock_threshold: Only products with stock_quantity <= this value
        has_sales: If True, only products with total_sold > 0
        has_reservations: If True, only products with currently_reserved > 0
    """

    # Pagination
    page: int = 1
    page_size: int = 20

    # Filters
    include_deleted: bool = False
    search: Optional[str] = None
    low_stock_threshold: Optional[int] = None
    has_sales: Optional[bool] = None
    has_reservations: Optional[bool] = None


@dataclass(frozen=True)
class ProductReportItem:
    """
    A single item in the product report.

    This combines data from multiple aggregates:
    - Product: id, name, price, stock_quantity, is_deleted
    - Cart items: currently_reserved (sum of quantities across all carts)
    - Order items: total_sold (sum of quantities across all orders)

    This is a read-only projection optimized for reporting, not a domain entity.
    """

    product_id: UUID
    name: str
    price: Decimal
    stock_quantity: int
    is_deleted: bool
    total_sold: int
    currently_reserved: int


@dataclass(frozen=True)
class ProductReportResult:
    """
    Paginated result for product report queries.

    Contains the items for the current page plus pagination metadata.
    """

    items: List[ProductReportItem]
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
