from abc import ABC, abstractmethod
from uuid import UUID

from domain.aggregates.cart.entities import Cart, CartItem


class CartRepository(ABC):
    @abstractmethod
    def get_cart(self) -> Cart:
        """Get the singleton cart. Creates it if it doesn't exist."""
        pass

    @abstractmethod
    def save(self, cart: Cart) -> Cart:
        """Save the cart and its items."""
        pass

    @abstractmethod
    def add_item(self, cart_id: UUID, item: CartItem) -> CartItem:
        """Add an item to the cart."""
        pass

    @abstractmethod
    def update_item(self, item: CartItem) -> CartItem:
        """Update an existing cart item."""
        pass

    @abstractmethod
    def delete_item(self, item_id: UUID) -> None:
        """Delete a cart item by its ID."""
        pass

    @abstractmethod
    def clear_items(self, cart_id: UUID) -> None:
        """Remove all items from the cart."""
        pass
