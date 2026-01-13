"""
Event infrastructure module.

Provides event dispatcher setup and configuration.
"""

from typing import Optional

from application.ports.audit_log_repository import AuditLogRepository
from domain.aggregates.product.events import StockReserved, StockReleased
from domain.aggregates.cart.events import (
    CartItemAdded,
    CartItemQuantityUpdated,
    CartItemRemoved,
    CartSubmitted,
)
from domain.aggregates.order.events import OrderCreated
from infrastructure.events.dispatcher import SyncEventDispatcher
from infrastructure.events.audit_handler import create_audit_log_handler


def create_event_dispatcher(
    audit_log_repository: Optional[AuditLogRepository] = None,
) -> SyncEventDispatcher:
    """
    Create and configure the event dispatcher with all handlers.

    Args:
        audit_log_repository: Repository for audit log persistence.
            If None, uses the default Django implementation.
    """
    dispatcher = SyncEventDispatcher()

    # Get audit log repository (lazy import to avoid circular dependencies)
    if audit_log_repository is None:
        from infrastructure.django_app.repositories.audit_log_repository import (
            get_audit_log_repository,
        )
        audit_log_repository = get_audit_log_repository()

    # Create audit handler with injected repository
    audit_handler = create_audit_log_handler(audit_log_repository)

    # Register audit handler for all event types
    all_events = [
        StockReserved,
        StockReleased,
        CartItemAdded,
        CartItemQuantityUpdated,
        CartItemRemoved,
        CartSubmitted,
        OrderCreated,
    ]
    for event_type in all_events:
        dispatcher.register(event_type, audit_handler)

    return dispatcher


# Singleton dispatcher instance
_dispatcher: Optional[SyncEventDispatcher] = None


def get_event_dispatcher() -> SyncEventDispatcher:
    """Get the global event dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = create_event_dispatcher()
    return _dispatcher
