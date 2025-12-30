from typing import List
from uuid import UUID

from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.cart.repository import CartRepository
from infrastructure.django_app.models import CartItemModel, CartModel


class DjangoCartRepository(CartRepository):
    def get_cart(self) -> Cart:
        """Get the singleton cart. Creates it if it doesn't exist."""
        model = CartModel.objects.first()
        if model is None:
            model = CartModel.objects.create()
        return self._to_domain(model)

    def save(self, cart: Cart) -> Cart:
        """Save the cart and its items."""
        # Cart itself has no mutable fields besides items
        # Items are managed via add_item, update_item, delete_item
        model = CartModel.objects.get(id=cart.id)
        return self._to_domain(model)

    def add_item(self, cart_id: UUID, item: CartItem) -> CartItem:
        """Add an item to the cart."""
        model = CartItemModel.objects.create(
            id=item.id,
            cart_id=cart_id,
            product_id=item.product_id,
            product_name=item.product_name,
            unit_price=item.unit_price,
            quantity=item.quantity,
        )
        return self._item_to_domain(model)

    def update_item(self, item: CartItem) -> CartItem:
        """Update an existing cart item."""
        CartItemModel.objects.filter(id=item.id).update(
            quantity=item.quantity
        )
        model = CartItemModel.objects.get(id=item.id)
        return self._item_to_domain(model)

    def delete_item(self, item_id: UUID) -> None:
        """Delete a cart item by its ID."""
        CartItemModel.objects.filter(id=item_id).delete()

    def clear_items(self, cart_id: UUID) -> None:
        """Remove all items from the cart."""
        CartItemModel.objects.filter(cart_id=cart_id).delete()

    def _to_domain(self, model: CartModel) -> Cart:
        """Convert ORM model to domain entity."""
        items = [self._item_to_domain(item) for item in model.items.all()]
        return Cart(
            id=model.id,
            items=items,
            created_at=model.created_at,
        )

    @staticmethod
    def _item_to_domain(model: CartItemModel) -> CartItem:
        """Convert ORM cart item to domain entity."""
        return CartItem(
            id=model.id,
            product_id=model.product_id,
            product_name=model.product_name,
            unit_price=model.unit_price,
            quantity=model.quantity,
        )
