"""
Port interface for product report queries.

This port defines the interface for reading product report data. Unlike repositories
which load and save aggregates, readers are optimized for cross-aggregate queries
that don't require domain logic.

This is part of the Simple Query Separation pattern - queries bypass the domain
layer and use direct database access for optimal performance.
"""

from abc import ABC, abstractmethod

from application.queries.product_report import ProductReportQuery, ProductReportResult


class ProductReportReader(ABC):
    """
    Abstract reader for product report queries.

    Implementations can use direct SQL, ORM queries with joins, or any other
    approach optimized for reading. Unlike repositories, readers:

    - Don't load domain aggregates (return simple data structures)
    - Can join across tables that represent different aggregates
    - Are optimized for read performance, not write consistency
    - Don't participate in Unit of Work transactions
    """

    @abstractmethod
    def get_report(self, query: ProductReportQuery) -> ProductReportResult:
        """
        Get the product report with pagination and filtering.

        Args:
            query: Query parameters specifying pagination, filters, and what to include

        Returns:
            ProductReportResult with paginated items and metadata
        """
        pass
