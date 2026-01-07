"""
Django implementation of the ProductReportReader.

This reader uses Django ORM with annotations to efficiently query data
from multiple aggregates in a single database query.
"""

from typing import Any, Optional

from django.db.models import OuterRef, Q, Subquery, Sum
from django.db.models.functions import Coalesce

from application.ports.product_report_reader import ProductReportReader
from application.queries.product_report import (
    ProductReportItem,
    ProductReportQuery,
    ProductReportResult,
)
from infrastructure.django_app.models import (
    CartItemModel,
    OrderItemModel,
    ProductModel,
)


class DjangoProductReportReader(ProductReportReader):
    """
    Django ORM implementation of the product report reader.

    Uses annotations to aggregate data from related tables (cart items, order items)
    in a single query. This bypasses the domain layer entirely - we're just reading
    data, not enforcing business rules.
    """

    def get_report(self, query: ProductReportQuery) -> ProductReportResult:
        """
        Get product report with aggregated data from Cart and Order items.

        Uses Django ORM annotations to:
        - Sum quantities from CartItemModel for currently_reserved
        - Sum quantities from OrderItemModel for total_sold

        Supports pagination and filtering on both product fields and
        aggregated fields (total_sold, currently_reserved).
        """
        # Enforce reasonable pagination limits
        page = max(1, query.page)
        page_size = max(1, min(100, query.page_size))

        # Subquery for total sold (sum of order item quantities for each product)
        total_sold_subquery = (
            OrderItemModel.objects.filter(product_id=OuterRef("id"))
            .values("product_id")
            .annotate(total=Sum("quantity"))
            .values("total")
        )

        # Subquery for currently reserved (sum of cart item quantities for each product)
        currently_reserved_subquery = (
            CartItemModel.objects.filter(product_id=OuterRef("id"))
            .values("product_id")
            .annotate(total=Sum("quantity"))
            .values("total")
        )

        # Build queryset with annotations
        queryset = ProductModel.objects.annotate(
            total_sold=Coalesce(Subquery(total_sold_subquery), 0),
            currently_reserved=Coalesce(Subquery(currently_reserved_subquery), 0),
        )

        # Apply filters
        queryset = self._apply_filters(queryset, query)

        # Order by name for consistent results
        queryset = queryset.order_by("name")

        # Get total count before pagination
        total_count = queryset.count()

        # Apply pagination
        offset = (page - 1) * page_size
        queryset = queryset[offset : offset + page_size]

        items = [self._to_report_item(product) for product in queryset]

        return ProductReportResult(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    def _apply_filters(
        self, queryset: Any, query: ProductReportQuery
    ) -> Any:
        """Apply filters from query to queryset."""
        # Filter out deleted products unless requested
        if not query.include_deleted:
            queryset = queryset.filter(deleted_at__isnull=True)

        # Search by name (case-insensitive contains)
        if query.search:
            queryset = queryset.filter(name__icontains=query.search)

        # Low stock threshold filter
        if query.low_stock_threshold is not None:
            queryset = queryset.filter(stock_quantity__lte=query.low_stock_threshold)

        # Has sales filter (requires filtering on annotated field)
        if query.has_sales is True:
            queryset = queryset.filter(total_sold__gt=0)
        elif query.has_sales is False:
            queryset = queryset.filter(total_sold=0)

        # Has reservations filter (requires filtering on annotated field)
        if query.has_reservations is True:
            queryset = queryset.filter(currently_reserved__gt=0)
        elif query.has_reservations is False:
            queryset = queryset.filter(currently_reserved=0)

        return queryset

    def _to_report_item(self, product: ProductModel) -> ProductReportItem:
        """Convert an annotated ProductModel to a ProductReportItem."""
        return ProductReportItem(
            product_id=product.id,
            name=product.name,
            price=product.price,
            stock_quantity=product.stock_quantity,
            is_deleted=product.deleted_at is not None,
            total_sold=product.total_sold,  # type: ignore[attr-defined]
            currently_reserved=product.currently_reserved,  # type: ignore[attr-defined]
        )


# Singleton instance for dependency injection
_reader: Optional[ProductReportReader] = None


def get_product_report_reader() -> ProductReportReader:
    """
    Get the product report reader instance.

    Returns a singleton instance of the Django implementation.
    This follows the same pattern as other adapters (get_email_adapter,
    get_feature_flags, etc.) for consistent dependency injection.
    """
    global _reader
    if _reader is None:
        _reader = DjangoProductReportReader()
    return _reader
