"""
Reader implementations for cross-aggregate queries.

Readers bypass the domain layer and use direct database access for optimal
read performance. They are part of the Simple Query Separation pattern.
"""

from infrastructure.django_app.readers.product_report_reader import (
    DjangoProductReportReader,
)

__all__ = ["DjangoProductReportReader"]
