"""
Application service for product reports.

This service wraps the ProductReportReader with authorization checks,
ensuring that only admins can access product reports.
"""

from application.ports.product_report_reader import ProductReportReader
from application.queries.product_report import ProductReportQuery, ProductReportResult
from domain.exceptions import PermissionDeniedError
from domain.user_context import UserContext


class ProductReportService:
    """
    Application service for product report queries.

    Provides authorization checks around the ProductReportReader.
    """

    def __init__(self, reader: ProductReportReader):
        self.reader = reader

    def get_report(
        self, query: ProductReportQuery, user_context: UserContext
    ) -> ProductReportResult:
        """
        Get the product report with authorization check.

        Args:
            query: Query parameters specifying pagination, filters, and what to include
            user_context: The authenticated user context

        Returns:
            ProductReportResult with paginated items and metadata

        Raises:
            PermissionDeniedError: If user is not an admin
        """
        if not user_context.is_admin():
            raise PermissionDeniedError(
                "get_product_report",
                "Only admins can view product reports",
            )

        return self.reader.get_report(query)
