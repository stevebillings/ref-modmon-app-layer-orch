from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from domain.aggregates.order.entities import Order


class OrderRepository(ABC):
    @abstractmethod
    def get_all(self) -> List[Order]:
        """Get all orders ordered by submitted_at descending (newest first)."""
        pass

    @abstractmethod
    def get_all_for_user(self, user_id: UUID) -> List[Order]:
        """Get all orders for a specific user, ordered by submitted_at descending."""
        pass

    @abstractmethod
    def save(self, order: Order) -> Order:
        """Save an order and its items."""
        pass

    @abstractmethod
    def has_user_used_coupon(self, user_id: UUID, coupon_id: UUID) -> bool:
        """Return True if the user has any prior order that used the given coupon."""
        pass
