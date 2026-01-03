"""
Abstract event dispatcher interface.

Defines the contract for dispatching domain events. Concrete implementations
live in the infrastructure layer.
"""

from abc import ABC, abstractmethod
from typing import List

from domain.events import DomainEvent


class EventDispatcher(ABC):
    """
    Abstract dispatcher for domain events.

    Implementations in the infrastructure layer handle the actual
    dispatching to registered handlers.
    """

    @abstractmethod
    def dispatch(self, events: List[DomainEvent]) -> None:
        """Dispatch events to all registered handlers."""
        pass
