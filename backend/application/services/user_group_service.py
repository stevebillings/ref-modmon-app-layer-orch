"""
Application service for user group operations.

Provides CRUD operations for user groups and membership management
with authorization. All operations require admin privileges.
"""

from uuid import UUID

from application.ports.user_group_repository import UserGroupRepository
from domain.exceptions import PermissionDeniedError
from domain.user_context import UserContext
from domain.user_groups import UserGroup


class UserGroupNotFoundError(Exception):
    """Raised when a user group is not found."""

    def __init__(self, identifier: str):
        self.identifier = identifier
        super().__init__(f"User group '{identifier}' not found")


class DuplicateUserGroupError(Exception):
    """Raised when trying to create a user group that already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"User group '{name}' already exists")


class UserGroupService:
    """
    Application service for user group admin operations.

    Provides CRUD operations for user groups and membership management.
    All operations require admin privileges.
    """

    def __init__(self, repository: UserGroupRepository):
        self.repository = repository

    def _require_admin(self, user_context: UserContext, operation: str) -> None:
        """Check that the user is an admin."""
        if not user_context.is_admin():
            raise PermissionDeniedError(
                operation, "Only admins can manage user groups"
            )

    def get_all(self, user_context: UserContext) -> list[UserGroup]:
        """
        Get all user groups.

        Authorization: Admin only.
        """
        self._require_admin(user_context, "list_user_groups")
        return self.repository.get_all()

    def get_by_id(self, group_id: UUID, user_context: UserContext) -> UserGroup:
        """
        Get a user group by ID.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            UserGroupNotFoundError: If group doesn't exist
        """
        self._require_admin(user_context, "get_user_group")
        group = self.repository.get_by_id(group_id)
        if group is None:
            raise UserGroupNotFoundError(str(group_id))
        return group

    def create(
        self,
        name: str,
        description: str,
        user_context: UserContext,
    ) -> UserGroup:
        """
        Create a new user group.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            DuplicateUserGroupError: If group already exists
            ValueError: If name is empty
        """
        self._require_admin(user_context, "create_user_group")

        name = name.strip()
        if not name:
            raise ValueError("Group name is required")

        if self.repository.exists(name):
            raise DuplicateUserGroupError(name)

        return self.repository.save(name, description)

    def update(
        self,
        group_id: UUID,
        description: str | None,
        user_context: UserContext,
    ) -> UserGroup:
        """
        Update a user group.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            UserGroupNotFoundError: If group doesn't exist
        """
        self._require_admin(user_context, "update_user_group")

        existing = self.repository.get_by_id(group_id)
        if existing is None:
            raise UserGroupNotFoundError(str(group_id))

        new_description = (
            description if description is not None else existing.description
        )

        return self.repository.save(existing.name, new_description)

    def delete(self, group_id: UUID, user_context: UserContext) -> None:
        """
        Delete a user group.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            UserGroupNotFoundError: If group doesn't exist
        """
        self._require_admin(user_context, "delete_user_group")

        if not self.repository.delete(group_id):
            raise UserGroupNotFoundError(str(group_id))

    def add_user(
        self,
        group_id: UUID,
        target_user_id: UUID,
        user_context: UserContext,
    ) -> None:
        """
        Add a user to a group.

        Authorization: Admin only.
        Idempotent - no error if user already in group.

        Raises:
            PermissionDeniedError: If user is not an admin
            UserGroupNotFoundError: If group doesn't exist
        """
        self._require_admin(user_context, "add_user_to_group")

        # Verify group exists
        if self.repository.get_by_id(group_id) is None:
            raise UserGroupNotFoundError(str(group_id))

        self.repository.add_user_to_group(target_user_id, group_id)

    def remove_user(
        self,
        group_id: UUID,
        target_user_id: UUID,
        user_context: UserContext,
    ) -> None:
        """
        Remove a user from a group.

        Authorization: Admin only.
        Idempotent - no error if user not in group.

        Raises:
            PermissionDeniedError: If user is not an admin
            UserGroupNotFoundError: If group doesn't exist
        """
        self._require_admin(user_context, "remove_user_from_group")

        # Verify group exists
        if self.repository.get_by_id(group_id) is None:
            raise UserGroupNotFoundError(str(group_id))

        self.repository.remove_user_from_group(target_user_id, group_id)

    def get_users_in_group(
        self,
        group_id: UUID,
        user_context: UserContext,
    ) -> list[UUID]:
        """
        Get all user IDs in a group.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            UserGroupNotFoundError: If group doesn't exist
        """
        self._require_admin(user_context, "list_group_members")

        # Verify group exists
        if self.repository.get_by_id(group_id) is None:
            raise UserGroupNotFoundError(str(group_id))

        return self.repository.get_user_ids_in_group(group_id)

    def get_groups_for_user(
        self,
        target_user_id: UUID,
        user_context: UserContext,
    ) -> list[UserGroup]:
        """
        Get all groups a user belongs to.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
        """
        self._require_admin(user_context, "list_user_groups")
        return self.repository.get_groups_for_user(target_user_id)
