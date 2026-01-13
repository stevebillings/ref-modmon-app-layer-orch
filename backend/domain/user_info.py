"""
Domain entity for user information.

Used for admin user management operations - listing users, viewing details,
updating roles and group memberships.
"""

from dataclasses import dataclass
from typing import FrozenSet
from uuid import UUID

from domain.user_context import Role


@dataclass(frozen=True)
class UserInfo:
    """
    Represents a user's profile information for admin management.

    This is distinct from UserContext which is used for authorization.
    UserInfo is a read model for displaying user details.
    """

    id: UUID
    username: str
    email: str
    role: Role
    group_ids: FrozenSet[UUID]

    @property
    def group_count(self) -> int:
        """Number of groups the user belongs to."""
        return len(self.group_ids)
