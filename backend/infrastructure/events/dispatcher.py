"""
Event dispatcher with sync and async handler support.

Dispatches domain events to registered handlers. Sync handlers run
immediately in the calling thread. Async handlers run in a background
thread pool for slow or unreliable operations.
"""

import atexit
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Type

from domain.events import DomainEvent
from domain.event_dispatcher import EventDispatcher


EventHandler = Callable[[DomainEvent], None]
logger = logging.getLogger(__name__)

# Module-level thread pool shared by all dispatchers
_executor: Optional[ThreadPoolExecutor] = None


def _get_executor() -> ThreadPoolExecutor:
    """Get or create the shared thread pool executor."""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="event-")
        # Ensure clean shutdown when the application exits
        atexit.register(_shutdown_executor)
    return _executor


def _shutdown_executor() -> None:
    """Shutdown the executor gracefully."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None


class SyncEventDispatcher(EventDispatcher):
    """
    Event dispatcher with sync and async handler support.

    - Sync handlers (register): Run immediately, block until complete.
      Use for fast, critical handlers like audit logging.

    - Async handlers (register_async): Run in background thread pool.
      Use for slow handlers like sending emails or calling external APIs.

    Handler exceptions are logged but don't prevent other handlers from running.
    """

    def __init__(self) -> None:
        self._sync_handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
        self._async_handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}

    def register(
        self, event_type: Type[DomainEvent], handler: EventHandler
    ) -> None:
        """
        Register a synchronous handler for an event type.

        Sync handlers run immediately in the calling thread and block
        until complete. Use for fast, critical handlers like audit logging.
        """
        if event_type not in self._sync_handlers:
            self._sync_handlers[event_type] = []
        self._sync_handlers[event_type].append(handler)

    def register_async(
        self, event_type: Type[DomainEvent], handler: EventHandler
    ) -> None:
        """
        Register an asynchronous handler for an event type.

        Async handlers run in a background thread pool and don't block
        the calling thread. Use for slow handlers like sending emails,
        calling external APIs, or heavy processing.
        """
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)

    def dispatch(self, events: List[DomainEvent]) -> None:
        """
        Dispatch events to all registered handlers.

        Sync handlers run first (in order), then async handlers are
        submitted to the thread pool and return immediately.
        """
        from infrastructure.django_app.metrics import record_domain_event
        from infrastructure.django_app.request_context import get_request_id

        request_id = get_request_id()

        for event in events:
            record_domain_event(event.get_event_type())
            logger.info(
                f"Dispatching domain event: {event.get_event_type()}",
                extra={
                    "event_type": event.get_event_type(),
                    "event_id": str(event.event_id),
                    "request_id": request_id,
                },
            )
            self._dispatch_sync(event)
            self._dispatch_async(event)

    def _dispatch_sync(self, event: DomainEvent) -> None:
        """Run sync handlers immediately in the current thread."""
        handlers = self._sync_handlers.get(type(event), [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    f"Error in sync handler for {event.get_event_type()}: {e}",
                    exc_info=True,
                )

    def _dispatch_async(self, event: DomainEvent) -> None:
        """Submit async handlers to the thread pool."""
        handlers = self._async_handlers.get(type(event), [])
        executor = _get_executor()
        for handler in handlers:
            executor.submit(self._run_async_handler, handler, event)

    def _run_async_handler(
        self, handler: EventHandler, event: DomainEvent
    ) -> None:
        """Execute an async handler with error handling."""
        try:
            handler(event)
        except Exception as e:
            logger.error(
                f"Error in async handler for {event.get_event_type()}: {e}",
                exc_info=True,
            )
