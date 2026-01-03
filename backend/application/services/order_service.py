from typing import List

from application.ports.unit_of_work import UnitOfWork
from domain.aggregates.order.entities import Order
from domain.user_context import UserContext


class OrderService:
    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def get_orders(self, user_context: UserContext) -> List[Order]:
        """
        Get orders for the authenticated user.

        Admins see all orders; customers see only their own.
        """
        if user_context.is_admin():
            return self.uow.get_order_repository().get_all()
        return self.uow.get_order_repository().get_all_for_user(user_context.user_id)
