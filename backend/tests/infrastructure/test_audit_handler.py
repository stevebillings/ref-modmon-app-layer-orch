"""Unit tests for AuditLogHandler with mock repository."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import pytest

from application.ports.audit_log_repository import AuditLogEntry, AuditLogRepository
from domain.aggregates.product.events import StockReserved
from domain.aggregates.cart.events import CartItemAdded
from infrastructure.events.audit_handler import AuditLogHandler, create_audit_log_handler


class MockAuditLogRepository(AuditLogRepository):
    """In-memory mock implementation for testing."""

    def __init__(self) -> None:
        self.entries: List[AuditLogEntry] = []
        self.save_calls: List[Dict[str, Any]] = []

    def save(
        self,
        event_type: str,
        event_id: UUID,
        occurred_at: datetime,
        actor_id: str,
        aggregate_type: str,
        aggregate_id: Optional[UUID],
        event_data: Dict[str, Any],
    ) -> AuditLogEntry:
        # Track the call for assertions
        self.save_calls.append({
            "event_type": event_type,
            "event_id": event_id,
            "occurred_at": occurred_at,
            "actor_id": actor_id,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "event_data": event_data,
        })

        entry = AuditLogEntry(
            id=uuid4(),
            event_type=event_type,
            event_id=event_id,
            occurred_at=occurred_at,
            actor_id=actor_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            event_data=event_data,
            created_at=datetime.now(timezone.utc),
        )
        self.entries.append(entry)
        return entry


class FailingAuditLogRepository(AuditLogRepository):
    """Mock that always fails - for testing error handling."""

    def save(
        self,
        event_type: str,
        event_id: UUID,
        occurred_at: datetime,
        actor_id: str,
        aggregate_type: str,
        aggregate_id: Optional[UUID],
        event_data: Dict[str, Any],
    ) -> AuditLogEntry:
        raise Exception("Database connection failed")


class TestAuditLogHandlerWithMock:
    """Unit tests for AuditLogHandler using mock repository."""

    def test_handler_saves_stock_reserved_event(self) -> None:
        repo = MockAuditLogRepository()
        handler = AuditLogHandler(repo)

        product_id = uuid4()
        event = StockReserved(
            product_id=product_id,
            product_name="Test Product",
            quantity_reserved=5,
            remaining_stock=95,
            actor_id="user123",
        )

        handler(event)

        assert len(repo.save_calls) == 1
        call = repo.save_calls[0]
        assert call["event_type"] == "StockReserved"
        assert call["aggregate_type"] == "Product"
        assert call["aggregate_id"] == product_id
        assert call["actor_id"] == "user123"
        assert call["event_data"]["quantity_reserved"] == 5

    def test_handler_saves_cart_item_added_event(self) -> None:
        from decimal import Decimal

        repo = MockAuditLogRepository()
        handler = AuditLogHandler(repo)

        cart_id = uuid4()
        product_id = uuid4()
        event = CartItemAdded(
            cart_id=cart_id,
            product_id=product_id,
            product_name="Widget",
            quantity=3,
            unit_price=Decimal("19.99"),
            actor_id="shopper456",
        )

        handler(event)

        assert len(repo.save_calls) == 1
        call = repo.save_calls[0]
        assert call["event_type"] == "CartItemAdded"
        assert call["aggregate_type"] == "Cart"
        assert call["aggregate_id"] == cart_id
        assert call["actor_id"] == "shopper456"

    def test_handler_handles_unknown_event_type(self) -> None:
        """Unknown event types should still be saved with 'Unknown' aggregate type."""
        from dataclasses import dataclass, field
        from datetime import datetime
        from domain.events import DomainEvent, _now_utc

        @dataclass(frozen=True)
        class UnknownEvent(DomainEvent):
            some_field: str = ""
            event_id: UUID = field(default_factory=uuid4)
            occurred_at: datetime = field(default_factory=_now_utc)

        repo = MockAuditLogRepository()
        handler = AuditLogHandler(repo)

        event = UnknownEvent(some_field="test_value")

        handler(event)

        assert len(repo.save_calls) == 1
        call = repo.save_calls[0]
        assert call["aggregate_type"] == "Unknown"
        assert call["aggregate_id"] is None

    def test_handler_catches_repository_exceptions(self) -> None:
        """Handler should not raise exceptions - just log errors."""
        repo = FailingAuditLogRepository()
        handler = AuditLogHandler(repo)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="user",
        )

        # Should not raise - errors are caught and logged
        handler(event)

    def test_create_audit_log_handler_factory(self) -> None:
        """Test the factory function creates a handler with the repository."""
        repo = MockAuditLogRepository()
        handler = create_audit_log_handler(repo)

        assert isinstance(handler, AuditLogHandler)
        assert handler.repository is repo

    def test_handler_preserves_event_id_and_timestamp(self) -> None:
        repo = MockAuditLogRepository()
        handler = AuditLogHandler(repo)

        event = StockReserved(
            product_id=uuid4(),
            product_name="Test",
            quantity_reserved=1,
            remaining_stock=99,
            actor_id="user",
        )

        handler(event)

        call = repo.save_calls[0]
        assert call["event_id"] == event.event_id
        assert call["occurred_at"] == event.occurred_at

    def test_handler_uses_default_actor_id_when_missing(self) -> None:
        """Events without actor_id should use 'unknown' as default."""
        from dataclasses import dataclass, field
        from datetime import datetime
        from domain.events import DomainEvent, _now_utc

        @dataclass(frozen=True)
        class NoActorEvent(DomainEvent):
            value: int = 0
            event_id: UUID = field(default_factory=uuid4)
            occurred_at: datetime = field(default_factory=_now_utc)

        repo = MockAuditLogRepository()
        handler = AuditLogHandler(repo)

        event = NoActorEvent(value=42)

        handler(event)

        call = repo.save_calls[0]
        assert call["actor_id"] == "unknown"
