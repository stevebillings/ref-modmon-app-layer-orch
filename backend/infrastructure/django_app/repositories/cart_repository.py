from uuid import UUID

from domain.aggregates.cart.entities import Cart, CartItem
from domain.aggregates.cart.repository import CartRepository
from infrastructure.django_app.models import CartItemModel, CartModel

# Fixed UUID for the singleton cart - ensures get_or_create atomicity
SINGLETON_CART_ID = UUID("00000000-0000-0000-0000-000000000001")


class DjangoCartRepository(CartRepository):
    def get_cart(self) -> Cart:
        """Get the singleton cart. Creates it if it doesn't exist."""
        # Use get_or_create with a fixed ID for atomicity - prevents race condition
        # where concurrent requests could both create a cart
        model, _ = CartModel.objects.get_or_create(id=SINGLETON_CART_ID)
        return self._to_domain(model)

    def save(self, cart: Cart) -> Cart:
        """
        Save the cart and its items.

        Compares current state with database and handles add/update/delete.
        """
        # Get current item IDs from database
        current_ids = set(
            CartItemModel.objects.filter(cart_id=cart.id).values_list(
                "id", flat=True
            )
        )
        new_ids = {item.id for item in cart.items}

        # Delete removed items
        removed_ids = current_ids - new_ids
        if removed_ids:
            CartItemModel.objects.filter(id__in=removed_ids).delete()

        # Upsert current items
        for item in cart.items:
            CartItemModel.objects.update_or_create(
                id=item.id,
                defaults={
                    "cart_id": cart.id,
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "unit_price": item.unit_price,
                    "quantity": item.quantity,
                },
            )

        return cart

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
