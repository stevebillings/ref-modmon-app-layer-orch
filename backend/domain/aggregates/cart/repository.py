from abc import ABC, abstractmethod

from domain.aggregates.cart.entities import Cart


class CartRepository(ABC):
    """
    Repository interface for Cart aggregate.

    Uses whole-aggregate persistence - save() handles all item changes.
    """

    @abstractmethod
    def get_cart(self) -> Cart:
        """Get the singleton cart. Creates it if it doesn't exist."""
        pass

    @abstractmethod
    def save(self, cart: Cart) -> Cart:
        """
        Save the cart and its items.

        Handles add/update/delete of items by comparing with persisted state.
        """
        pass
