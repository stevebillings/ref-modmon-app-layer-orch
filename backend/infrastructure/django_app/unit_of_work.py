from contextlib import contextmanager
from typing import Any, Generator, List, Optional

from django.db import transaction

from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.cart.repository import CartRepository
from domain.aggregates.order.repository import OrderRepository
from domain.aggregates.product.repository import ProductRepository
from domain.event_dispatcher import EventDispatcher
from domain.events import DomainEvent
from infrastructure.django_app.repositories.cart_repository import (
    DjangoCartRepository,
)
from infrastructure.django_app.repositories.order_repository import (
    DjangoOrderRepository,
)
from infrastructure.django_app.repositories.product_repository import (
    DjangoProductRepository,
)


class DjangoUnitOfWork(UnitOfWork):
    """
    Unit of Work pattern implementation for Django.

    Provides transaction management, repository access, and event collection.
    All database operations within a single request should use
    the same UnitOfWork instance to ensure transactional consistency.

    Events are collected from aggregates after saves and dispatched
    after the transaction commits successfully.
    """

    def __init__(self, event_dispatcher: Optional[EventDispatcher] = None) -> None:
        self._product_repository: Optional[ProductRepository] = None
        self._cart_repository: Optional[CartRepository] = None
        self._order_repository: Optional[OrderRepository] = None
        self._event_dispatcher = event_dispatcher
        self._collected_events: List[DomainEvent] = []

    def get_product_repository(self) -> ProductRepository:
        if self._product_repository is None:
            self._product_repository = DjangoProductRepository()
        return self._product_repository

    def get_cart_repository(self) -> CartRepository:
        if self._cart_repository is None:
            self._cart_repository = DjangoCartRepository()
        return self._cart_repository

    def get_order_repository(self) -> OrderRepository:
        if self._order_repository is None:
            self._order_repository = DjangoOrderRepository()
        return self._order_repository

    def collect_events_from(self, aggregate: Any) -> None:
        """
        Collect domain events from an aggregate after saving.

        Call this after saving each modified aggregate. Events are queued
        for dispatch after the transaction commits.
        """
        if hasattr(aggregate, "get_domain_events"):
            self._collected_events.extend(aggregate.get_domain_events())
            aggregate.clear_domain_events()

    def dispatch_events(self) -> None:
        """
        Dispatch all collected events to handlers.

        Called after transaction commit. Clears the event queue after dispatch.
        """
        if self._event_dispatcher and self._collected_events:
            self._event_dispatcher.dispatch(self._collected_events)
        self._collected_events = []


@contextmanager
def unit_of_work(
    event_dispatcher: Optional[EventDispatcher] = None,
) -> Generator[UnitOfWork, None, None]:
    """
    Context manager that provides a UnitOfWork with transaction management.

    Usage:
        with unit_of_work(dispatcher) as uow:
            product = uow.get_product_repository().get_by_id(product_id)
            # ... perform operations
            uow.collect_events_from(product)

    The transaction is committed on successful exit,
    or rolled back if an exception occurs.
    Events are dispatched after successful commit.
    """
    uow = DjangoUnitOfWork(event_dispatcher)
    with transaction.atomic():
        yield uow
    # After successful commit, dispatch events
    uow.dispatch_events()
