"""
Event infrastructure module.

Provides event dispatcher setup and configuration.
"""

from typing import Optional

from domain.aggregates.product.events import StockReserved, StockReleased
from domain.aggregates.cart.events import (
    CartItemAdded,
    CartItemQuantityUpdated,
    CartItemRemoved,
    CartSubmitted,
)
from domain.aggregates.order.events import OrderCreated
from infrastructure.events.dispatcher import SyncEventDispatcher
from infrastructure.events.audit_handler import audit_log_handler


def create_event_dispatcher() -> SyncEventDispatcher:
    """Create and configure the event dispatcher with all handlers."""
    dispatcher = SyncEventDispatcher()

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
        dispatcher.register(event_type, audit_log_handler)

    return dispatcher


# Singleton dispatcher instance
_dispatcher: Optional[SyncEventDispatcher] = None


def get_event_dispatcher() -> SyncEventDispatcher:
    """Get the global event dispatcher instance."""
    global _dispatcher
    if _dispatcher is None:
        _dispatcher = create_event_dispatcher()
    return _dispatcher
