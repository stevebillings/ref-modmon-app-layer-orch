from typing import List
from uuid import UUID

from domain.aggregates.order.entities import Order, OrderItem
from domain.aggregates.order.repository import OrderRepository
from infrastructure.django_app.models import OrderItemModel, OrderModel


class DjangoOrderRepository(OrderRepository):
    def get_all(self) -> List[Order]:
        """Get all orders ordered by submitted_at descending (newest first)."""
        return [
            self._to_domain(model)
            for model in OrderModel.objects.prefetch_related("items").all()
        ]

    def save(self, order: Order) -> Order:
        """Save an order and its items."""
        model = OrderModel.objects.create(id=order.id)
        for item in order.items:
            OrderItemModel.objects.create(
                id=item.id,
                order=model,
                product_id=item.product_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
            )
        model.refresh_from_db()
        return self._to_domain(model)

    def _to_domain(self, model: OrderModel) -> Order:
        """Convert ORM model to domain entity."""
        items = [self._item_to_domain(item, model.id) for item in model.items.all()]
        return Order(
            id=model.id,
            items=items,
            submitted_at=model.submitted_at,
        )

    @staticmethod
    def _item_to_domain(model: OrderItemModel, order_id: UUID) -> OrderItem:
        """Convert ORM order item to domain entity."""
        return OrderItem(
            id=model.id,
            order_id=order_id,
            product_id=model.product_id,
            product_name=model.product_name,
            unit_price=model.unit_price,
            quantity=model.quantity,
        )
