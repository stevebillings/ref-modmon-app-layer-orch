"""Tests for the event dispatcher."""

import threading
import time
from decimal import Decimal
from typing import List
from uuid import uuid4

import pytest

from domain.aggregates.product.events import StockReserved
from domain.aggregates.cart.events import CartItemAdded
from domain.events import DomainEvent
from infrastructure.events.dispatcher import SyncEventDispatcher


class TestSyncEventDispatcher:
    """Tests for sync handler registration and dispatch."""

    def test_register_and_dispatch_sync_handler(self) -> None:
        """Sync handlers are called immediately."""
        dispatcher = SyncEventDispatcher()
        received_events: List[DomainEvent] = []

        def handler(event: DomainEvent) -> None:
            received_events.append(event)

        dispatcher.register(StockReserved, handler)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=5,
            remaining_stock=95,
            actor_id="test",
        )
        dispatcher.dispatch([event])

        assert len(received_events) == 1
        assert received_events[0] == event

    def test_multiple_sync_handlers_same_event(self) -> None:
        """Multiple sync handlers can be registered for same event type."""
        dispatcher = SyncEventDispatcher()
        call_order: List[str] = []

        def handler1(event: DomainEvent) -> None:
            call_order.append("handler1")

        def handler2(event: DomainEvent) -> None:
            call_order.append("handler2")

        dispatcher.register(StockReserved, handler1)
        dispatcher.register(StockReserved, handler2)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="test",
        )
        dispatcher.dispatch([event])

        assert call_order == ["handler1", "handler2"]

    def test_sync_handler_exception_does_not_stop_others(self) -> None:
        """Exception in one sync handler doesn't prevent others from running."""
        dispatcher = SyncEventDispatcher()
        handler2_called = False

        def failing_handler(event: DomainEvent) -> None:
            raise ValueError("Handler failed")

        def handler2(event: DomainEvent) -> None:
            nonlocal handler2_called
            handler2_called = True

        dispatcher.register(StockReserved, failing_handler)
        dispatcher.register(StockReserved, handler2)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="test",
        )
        dispatcher.dispatch([event])

        assert handler2_called


class TestAsyncEventDispatcher:
    """Tests for async handler registration and dispatch."""

    def test_register_async_handler(self) -> None:
        """Async handlers are called in background thread."""
        dispatcher = SyncEventDispatcher()
        received_events: List[DomainEvent] = []
        handler_thread_name: List[str] = []
        event_received = threading.Event()

        def async_handler(event: DomainEvent) -> None:
            received_events.append(event)
            handler_thread_name.append(threading.current_thread().name)
            event_received.set()

        dispatcher.register_async(StockReserved, async_handler)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=5,
            remaining_stock=95,
            actor_id="test",
        )
        dispatcher.dispatch([event])

        # Wait for async handler to complete
        assert event_received.wait(timeout=2.0), "Async handler was not called"
        assert len(received_events) == 1
        assert received_events[0] == event
        assert handler_thread_name[0].startswith("event-")

    def test_async_handler_does_not_block(self) -> None:
        """Async handlers don't block the dispatch call."""
        dispatcher = SyncEventDispatcher()
        handler_started = threading.Event()
        handler_complete = threading.Event()

        def slow_handler(event: DomainEvent) -> None:
            handler_started.set()
            time.sleep(0.1)  # Simulate slow operation
            handler_complete.set()

        dispatcher.register_async(StockReserved, slow_handler)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="test",
        )

        start = time.time()
        dispatcher.dispatch([event])
        dispatch_time = time.time() - start

        # Dispatch should return immediately (not wait for slow handler)
        assert dispatch_time < 0.05, "Dispatch blocked on async handler"

        # But handler should eventually complete
        assert handler_complete.wait(timeout=2.0), "Async handler did not complete"

    def test_sync_runs_before_async(self) -> None:
        """Sync handlers complete before async handlers start."""
        dispatcher = SyncEventDispatcher()
        execution_order: List[str] = []
        async_done = threading.Event()
        lock = threading.Lock()

        def sync_handler(event: DomainEvent) -> None:
            with lock:
                execution_order.append("sync")

        def async_handler(event: DomainEvent) -> None:
            with lock:
                execution_order.append("async")
            async_done.set()

        dispatcher.register(StockReserved, sync_handler)
        dispatcher.register_async(StockReserved, async_handler)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="test",
        )
        dispatcher.dispatch([event])

        # Wait for async to complete
        assert async_done.wait(timeout=2.0)

        # Sync should have run first
        assert execution_order[0] == "sync"

    def test_async_handler_exception_is_logged(self) -> None:
        """Async handler exceptions don't crash the thread pool."""
        dispatcher = SyncEventDispatcher()
        handler2_called = threading.Event()

        def failing_handler(event: DomainEvent) -> None:
            raise ValueError("Async handler failed")

        def handler2(event: DomainEvent) -> None:
            handler2_called.set()

        dispatcher.register_async(StockReserved, failing_handler)
        dispatcher.register_async(StockReserved, handler2)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="test",
        )
        dispatcher.dispatch([event])

        # Second handler should still run despite first one failing
        assert handler2_called.wait(timeout=2.0)


class TestMixedHandlers:
    """Tests for mixing sync and async handlers."""

    def test_different_event_types_different_modes(self) -> None:
        """Can have sync handler for one event, async for another."""
        dispatcher = SyncEventDispatcher()
        sync_called = False
        async_called = threading.Event()

        def sync_handler(event: DomainEvent) -> None:
            nonlocal sync_called
            sync_called = True

        def async_handler(event: DomainEvent) -> None:
            async_called.set()

        dispatcher.register(StockReserved, sync_handler)
        dispatcher.register_async(CartItemAdded, async_handler)

        stock_event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="test",
        )
        cart_event = CartItemAdded(
            cart_id=uuid4(),
            product_id=uuid4(),
            product_name="Test",
            quantity=1,
            unit_price=Decimal("10.00"),
            actor_id="test",
        )

        dispatcher.dispatch([stock_event, cart_event])

        assert sync_called
        assert async_called.wait(timeout=2.0)
