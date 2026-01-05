"""Integration tests for audit logging."""

from uuid import uuid4

import pytest
from django.test import TestCase

from application.services.cart_service import CartService
from application.services.product_service import ProductService
from domain.user_context import Role, UserContext
from infrastructure.django_app.models import AuditLogModel
from infrastructure.django_app.unit_of_work import unit_of_work
from infrastructure.events import get_event_dispatcher


def make_user_context(role: Role = Role.ADMIN) -> UserContext:
    """Create a test UserContext."""
    return UserContext(user_id=uuid4(), username="testuser", role=role)


class TestAuditLogging(TestCase):
    """Integration tests verifying audit log entries are created."""

    def test_add_item_creates_audit_entries(self) -> None:
        """Adding item to cart creates audit entries for cart and stock events."""
        user_context = make_user_context()

        # Create a product
        with unit_of_work(get_event_dispatcher()) as uow:
            service = ProductService(uow)
            product = service.create_product(
                name="Audit Test Product",
                price="25.00",
                stock_quantity=50,
                user_context=user_context,
            )

        # Add to cart
        with unit_of_work(get_event_dispatcher()) as uow:
            service = CartService(uow)
            service.add_item(str(product.id), quantity=2, user_context=user_context)

        # Verify audit log entries were created
        entries = AuditLogModel.objects.filter(
            aggregate_id=product.id
        ).order_by("occurred_at")

        # Should have StockReserved event
        stock_events = [e for e in entries if e.event_type == "StockReserved"]
        assert len(stock_events) == 1
        assert stock_events[0].actor_id == str(user_context.user_id)
        assert stock_events[0].event_data["quantity_reserved"] == 2

    def test_submit_cart_creates_audit_entries(self) -> None:
        """Submitting cart creates CartSubmitted audit entry."""
        user_context = make_user_context()

        # Create a product and add to cart
        with unit_of_work(get_event_dispatcher()) as uow:
            product_service = ProductService(uow)
            product = product_service.create_product(
                name="Submit Test Product",
                price="15.00",
                stock_quantity=10,
                user_context=user_context,
            )

        with unit_of_work(get_event_dispatcher()) as uow:
            cart_service = CartService(uow)
            cart = cart_service.add_item(str(product.id), quantity=1, user_context=user_context)
            cart_id = cart.id

        # Submit the cart
        with unit_of_work(get_event_dispatcher()) as uow:
            cart_service = CartService(uow)
            cart_service.submit_cart(user_context)

        # Verify CartSubmitted event was logged
        submit_entries = AuditLogModel.objects.filter(
            event_type="CartSubmitted",
            aggregate_id=cart_id,
        )
        assert submit_entries.count() == 1
        entry = submit_entries.first()
        assert entry.event_data["item_count"] == 1

    def test_audit_log_contains_event_details(self) -> None:
        """Audit log entries contain full event details."""
        user_context = make_user_context()

        with unit_of_work(get_event_dispatcher()) as uow:
            service = ProductService(uow)
            product = service.create_product(
                name="Details Test Product",
                price="99.99",
                stock_quantity=25,
                user_context=user_context,
            )

        with unit_of_work(get_event_dispatcher()) as uow:
            service = CartService(uow)
            service.add_item(str(product.id), quantity=5, user_context=user_context)

        entry = AuditLogModel.objects.filter(
            event_type="StockReserved",
            aggregate_id=product.id,
        ).first()

        assert entry is not None
        assert entry.aggregate_type == "Product"
        assert entry.event_data["product_name"] == "Details Test Product"
        assert entry.event_data["quantity_reserved"] == 5
        assert entry.event_data["remaining_stock"] == 20
        assert "event_id" in entry.event_data
        assert "occurred_at" in entry.event_data
