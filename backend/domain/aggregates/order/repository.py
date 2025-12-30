from abc import ABC, abstractmethod
from typing import List

from domain.aggregates.order.entities import Order


class OrderRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Order]:
        """Get all orders ordered by submitted_at descending (newest first)."""
        pass

    @abstractmethod
    def save(self, order: Order) -> Order:
        """Save an order and its items."""
        pass
