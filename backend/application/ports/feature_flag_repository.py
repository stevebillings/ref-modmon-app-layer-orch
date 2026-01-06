from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FeatureFlag:
    """
    Domain representation of a feature flag.

    Immutable value object for feature flag data.
    """

    name: str
    enabled: bool
    description: str
    created_at: datetime
    updated_at: datetime


class FeatureFlagRepository(ABC):
    """
    Repository port for feature flag CRUD operations.

    Provides full lifecycle management of feature flags.
    For simple flag checking, use FeatureFlagPort instead.
    """

    @abstractmethod
    def get_all(self) -> list[FeatureFlag]:
        """Get all feature flags."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> FeatureFlag | None:
        """
        Get a feature flag by name.

        Returns None if flag doesn't exist.
        """
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a feature flag exists."""
        pass

    @abstractmethod
    def save(self, name: str, enabled: bool, description: str = "") -> FeatureFlag:
        """
        Create or update a feature flag.

        Args:
            name: Unique flag name
            enabled: Whether the flag is enabled
            description: Optional description

        Returns:
            The saved feature flag
        """
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        """
        Delete a feature flag by name.

        Returns True if deleted, False if flag didn't exist.
        """
        pass
