"""
Audit logging event handler.

Persists domain events to the audit log via repository injection.
"""

import logging
from typing import Dict, Tuple, Type

from application.ports.audit_log_repository import AuditLogRepository
from domain.events import DomainEvent
from domain.aggregates.product.events import (
    StockReserved,
    StockReleased,
    ProductDeleted,
    ProductRestored,
)
from domain.aggregates.cart.events import (
    CartItemAdded,
    CartItemQuantityUpdated,
    CartItemRemoved,
    CartSubmitted,
)
from domain.aggregates.order.events import OrderCreated


logger = logging.getLogger(__name__)


# Map event types to (aggregate_type, aggregate_id_field)
EVENT_AGGREGATE_MAP: Dict[Type[DomainEvent], Tuple[str, str]] = {
    StockReserved: ("Product", "product_id"),
    StockReleased: ("Product", "product_id"),
    ProductDeleted: ("Product", "product_id"),
    ProductRestored: ("Product", "product_id"),
    CartItemAdded: ("Cart", "cart_id"),
    CartItemQuantityUpdated: ("Cart", "cart_id"),
    CartItemRemoved: ("Cart", "cart_id"),
    CartSubmitted: ("Cart", "cart_id"),
    OrderCreated: ("Order", "order_id"),
}


class AuditLogHandler:
    """
    Event handler that persists domain events to the audit log.

    Uses dependency injection for the repository to enable testing
    and maintain separation of concerns.
    """

    def __init__(self, repository: AuditLogRepository):
        self.repository = repository

    def __call__(self, event: DomainEvent) -> None:
        """
        Handle a domain event by persisting it to the audit log.

        Called after transaction commit for each domain event.
        Failures are logged but don't break operations.
        """
        try:
            aggregate_info = EVENT_AGGREGATE_MAP.get(type(event))
            if aggregate_info:
                aggregate_type, id_field = aggregate_info
                aggregate_id = getattr(event, id_field)
            else:
                aggregate_type = "Unknown"
                aggregate_id = None

            self.repository.save(
                event_type=event.get_event_type(),
                event_id=event.event_id,
                occurred_at=event.occurred_at,
                actor_id=getattr(event, "actor_id", "unknown"),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                event_data=event.to_dict(),
            )
        except Exception as e:
            # Log but don't fail - audit logging shouldn't break operations
            logger.error(
                f"Failed to write audit log for {event.get_event_type()}: {e}",
                exc_info=True,
            )


def create_audit_log_handler(repository: AuditLogRepository) -> AuditLogHandler:
    """
    Factory function to create an audit log handler with its dependencies.

    Args:
        repository: The audit log repository to use for persistence.

    Returns:
        A configured AuditLogHandler instance.
    """
    return AuditLogHandler(repository)
