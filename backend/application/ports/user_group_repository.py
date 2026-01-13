"""
Repository port for user group operations.

User groups are collections of users for feature flag targeting.
This port defines the interface for user group persistence.
"""

from abc import ABC, abstractmethod
from typing import FrozenSet, List, Optional
from uuid import UUID

from domain.user_groups import UserGroup


class UserGroupRepository(ABC):
    """
    Repository port for user group CRUD and membership operations.

    Provides full lifecycle management of user groups and their memberships.
    """

    @abstractmethod
    def get_all(self) -> List[UserGroup]:
        """Get all user groups."""
        pass

    @abstractmethod
    def get_by_id(self, group_id: UUID) -> Optional[UserGroup]:
        """
        Get a user group by ID.

        Returns None if group doesn't exist.
        """
        pass

    @abstractmethod
    def get_by_name(self, name: str) -> Optional[UserGroup]:
        """
        Get a user group by name.

        Returns None if group doesn't exist.
        """
        pass

    @abstractmethod
    def exists(self, name: str) -> bool:
        """Check if a user group with this name exists."""
        pass

    @abstractmethod
    def save(self, name: str, description: str = "") -> UserGroup:
        """
        Create or update a user group.

        Args:
            name: Unique group name
            description: Optional description

        Returns:
            The saved user group
        """
        pass

    @abstractmethod
    def delete(self, group_id: UUID) -> bool:
        """
        Delete a user group by ID.

        Returns True if deleted, False if group didn't exist.
        """
        pass

    @abstractmethod
    def get_groups_for_user(self, user_id: UUID) -> List[UserGroup]:
        """Get all groups a user belongs to."""
        pass

    @abstractmethod
    def get_group_ids_for_user(self, user_id: UUID) -> FrozenSet[UUID]:
        """Get all group IDs a user belongs to (optimized for UserContext)."""
        pass

    @abstractmethod
    def add_user_to_group(self, user_id: UUID, group_id: UUID) -> None:
        """
        Add a user to a group.

        Idempotent - no error if user already in group.
        """
        pass

    @abstractmethod
    def remove_user_from_group(self, user_id: UUID, group_id: UUID) -> None:
        """
        Remove a user from a group.

        Idempotent - no error if user not in group.
        """
        pass

    @abstractmethod
    def get_user_ids_in_group(self, group_id: UUID) -> List[UUID]:
        """Get all user IDs in a group."""
        pass
