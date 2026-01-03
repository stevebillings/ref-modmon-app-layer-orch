from abc import ABC, abstractmethod
from typing import Any

from domain.aggregates.cart.repository import CartRepository
from domain.aggregates.order.repository import OrderRepository
from domain.aggregates.product.repository import ProductRepository


class UnitOfWork(ABC):
    """
    Abstract Unit of Work port.

    Provides transaction management, repository access, and event collection.
    Implementations are responsible for:
    - Managing database transactions
    - Providing repository instances
    - Collecting and dispatching domain events after commit
    """

    @abstractmethod
    def get_product_repository(self) -> ProductRepository:
        """Get the product repository."""
        pass

    @abstractmethod
    def get_cart_repository(self) -> CartRepository:
        """Get the cart repository."""
        pass

    @abstractmethod
    def get_order_repository(self) -> OrderRepository:
        """Get the order repository."""
        pass

    @abstractmethod
    def collect_events_from(self, aggregate: Any) -> None:
        """
        Collect domain events from an aggregate after saving.

        Call this after saving each modified aggregate. Events are queued
        for dispatch after the transaction commits.
        """
        pass

    @abstractmethod
    def dispatch_events(self) -> None:
        """
        Dispatch all collected events to handlers.

        Called after transaction commit. Clears the event queue after dispatch.
        """
        pass
