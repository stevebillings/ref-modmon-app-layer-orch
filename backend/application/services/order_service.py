from typing import List

from domain.aggregates.order.entities import Order
from infrastructure.django_app.unit_of_work import UnitOfWork


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_all_orders(self) -> List[Order]:
        """Get all orders ordered by submitted_at descending (newest first)."""
        return self.uow.orders.get_all()
