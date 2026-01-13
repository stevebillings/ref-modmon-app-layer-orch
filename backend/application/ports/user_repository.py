"""
Port (interface) for user repository operations.

Provides read/write access to user profiles for admin management.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.user_context import Role
from domain.user_info import UserInfo


class UserRepository(ABC):
    """
    Repository interface for user management operations.

    Used by admin functionality to list, view, and update users.
    """

    @abstractmethod
    def get_all(self) -> List[UserInfo]:
        """Get all users with their profile information."""
        pass

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> Optional[UserInfo]:
        """Get a user by their profile ID."""
        pass

    @abstractmethod
    def update_role(self, user_id: UUID, role: Role) -> Optional[UserInfo]:
        """
        Update a user's role.

        Returns the updated UserInfo, or None if user not found.
        """
        pass
