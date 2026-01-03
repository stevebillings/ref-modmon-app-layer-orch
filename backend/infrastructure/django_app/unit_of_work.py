from contextlib import contextmanager
from typing import Generator

from django.db import transaction

from domain.aggregates.cart.repository import CartRepository
from domain.aggregates.order.repository import OrderRepository
from domain.aggregates.product.repository import ProductRepository
from infrastructure.django_app.repositories.cart_repository import (
    DjangoCartRepository,
)
from infrastructure.django_app.repositories.order_repository import (
    DjangoOrderRepository,
)
from infrastructure.django_app.repositories.product_repository import (
    DjangoProductRepository,
)


class UnitOfWork:
    """
    Unit of Work pattern implementation for Django.

    Provides transaction management and repository access.
    All database operations within a single request should use
    the same UnitOfWork instance to ensure transactional consistency.
    """

    def __init__(self) -> None:
        self._product_repository: ProductRepository | None = None
        self._cart_repository: CartRepository | None = None
        self._order_repository: OrderRepository | None = None

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


@contextmanager
def unit_of_work() -> Generator[UnitOfWork, None, None]:
    """
    Context manager that provides a UnitOfWork with transaction management.

    Usage:
        with unit_of_work() as uow:
            product = uow.get_product_repository().get_by_id(product_id)
            # ... perform operations

    The transaction is committed on successful exit,
    or rolled back if an exception occurs.
    """
    with transaction.atomic():
        yield UnitOfWork()
