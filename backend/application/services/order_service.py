from typing import List

from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.order.entities import Order


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all_orders(self) -> List[Order]:
        """Get all orders ordered by submitted_at descending (newest first)."""
        return self.uow.get_order_repository().get_all()
