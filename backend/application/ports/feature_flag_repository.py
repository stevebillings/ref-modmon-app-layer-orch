from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import FrozenSet, List, Optional, Set
from uuid import UUID


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
    target_group_ids: FrozenSet[UUID] = field(default_factory=frozenset)

    def is_targeted(self) -> bool:
        """Check if this flag has any target groups."""
        return bool(self.target_group_ids)


class FeatureFlagRepository(ABC):
    """
    Repository port for feature flag CRUD operations.

    Provides full lifecycle management of feature flags.
    For simple flag checking, use FeatureFlagPort instead.
    """

    @abstractmethod
    def get_all(self) -> List[FeatureFlag]:
        """Get all feature flags."""
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[FeatureFlag]:
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

    @abstractmethod
    def set_target_groups(self, flag_name: str, group_ids: Set[UUID]) -> FeatureFlag:
        """
        Set the target groups for a feature flag (replaces existing).

        Args:
            flag_name: The flag to update
            group_ids: Set of group IDs to target (empty set clears targeting)

        Returns:
            The updated feature flag
        """
        pass

    @abstractmethod
    def add_target_group(self, flag_name: str, group_id: UUID) -> FeatureFlag:
        """
        Add a target group to a feature flag.

        Idempotent - no error if group already targeted.

        Args:
            flag_name: The flag to update
            group_id: The group ID to add as a target

        Returns:
            The updated feature flag
        """
        pass

    @abstractmethod
    def remove_target_group(self, flag_name: str, group_id: UUID) -> FeatureFlag:
        """
        Remove a target group from a feature flag.

        Idempotent - no error if group not targeted.

        Args:
            flag_name: The flag to update
            group_id: The group ID to remove from targets

        Returns:
            The updated feature flag
        """
        pass
