"""
Application service for user management.

Provides admin functionality for listing users, viewing details,
and updating roles.
"""

from uuid import UUID

from application.ports.user_group_repository import UserGroupRepository
from application.ports.user_repository import UserRepository
from domain.exceptions import PermissionDeniedError
from domain.user_context import Role, UserContext
from domain.user_info import UserInfo


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        super().__init__(f"User '{user_id}' not found")


class UserService:
    """
    Service for user management operations.

    All operations require admin authorization.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        user_group_repository: UserGroupRepository,
    ) -> None:
        self._user_repo = user_repository
        self._group_repo = user_group_repository

    def _require_admin(self, user_context: UserContext) -> None:
        """Ensure the user has admin role."""
        if not user_context.is_admin():
            raise PermissionDeniedError("Admin access required")

    def get_all(self, user_context: UserContext) -> list[UserInfo]:
        """Get all users. Admin only."""
        self._require_admin(user_context)
        return self._user_repo.get_all()

    def get_by_id(self, user_id: UUID, user_context: UserContext) -> UserInfo:
        """Get a user by ID. Admin only."""
        self._require_admin(user_context)
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def update_role(
        self,
        user_id: UUID,
        role: Role,
        user_context: UserContext,
    ) -> UserInfo:
        """Update a user's role. Admin only."""
        self._require_admin(user_context)
        user = self._user_repo.update_role(user_id, role)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def add_to_group(
        self,
        user_id: UUID,
        group_id: UUID,
        user_context: UserContext,
    ) -> UserInfo:
        """Add a user to a group. Admin only."""
        self._require_admin(user_context)

        # Verify user exists
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        # Add to group (group validation happens in repository)
        self._group_repo.add_user_to_group(user_id, group_id)

        # Return updated user info
        return self._user_repo.get_by_id(user_id)  # type: ignore

    def remove_from_group(
        self,
        user_id: UUID,
        group_id: UUID,
        user_context: UserContext,
    ) -> UserInfo:
        """Remove a user from a group. Admin only."""
        self._require_admin(user_context)

        # Verify user exists
        user = self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        # Remove from group
        self._group_repo.remove_user_from_group(user_id, group_id)

        # Return updated user info
        return self._user_repo.get_by_id(user_id)  # type: ignore
