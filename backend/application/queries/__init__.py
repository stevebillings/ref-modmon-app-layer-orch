"""Query definitions for read operations that span aggregates."""

from application.queries.product_report import (
    ProductReportItem,
    ProductReportQuery,
    ProductReportResult,
)

__all__ = ["ProductReportQuery", "ProductReportItem", "ProductReportResult"]
