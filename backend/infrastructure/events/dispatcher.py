"""
Synchronous in-process event dispatcher.

Dispatches domain events to registered handlers. For production,
could be replaced with an async/message queue dispatcher.
"""

import logging
from typing import Callable, Dict, List, Type

from domain.events import DomainEvent
from domain.event_dispatcher import EventDispatcher


EventHandler = Callable[[DomainEvent], None]
logger = logging.getLogger(__name__)


class SyncEventDispatcher(EventDispatcher):
    """
    Synchronous event dispatcher.

    Dispatches events to registered handlers in-process.
    Handler exceptions are logged but don't prevent other handlers from running.
    """

    def __init__(self) -> None:
        self._handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def register(
        self, event_type: Type[DomainEvent], handler: EventHandler
    ) -> None:
        """Register a handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def dispatch(self, events: List[DomainEvent]) -> None:
        """Dispatch each event to its registered handlers."""
        for event in events:
            handlers = self._handlers.get(type(event), [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    # Log but don't fail - event handling shouldn't break operations
                    logger.error(
                        f"Error in handler for {event.get_event_type()}: {e}",
                        exc_info=True,
                    )
