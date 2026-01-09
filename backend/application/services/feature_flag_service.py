from uuid import UUID

from application.ports.feature_flag_repository import FeatureFlag, FeatureFlagRepository
from domain.exceptions import PermissionDeniedError
from domain.user_context import UserContext


class FeatureFlagNotFoundError(Exception):
    """Raised when a feature flag is not found."""

    def __init__(self, flag_name: str):
        self.flag_name = flag_name
        super().__init__(f"Feature flag '{flag_name}' not found")


class DuplicateFeatureFlagError(Exception):
    """Raised when trying to create a feature flag that already exists."""

    def __init__(self, flag_name: str):
        self.flag_name = flag_name
        super().__init__(f"Feature flag '{flag_name}' already exists")


class FeatureFlagService:
    """
    Application service for feature flag admin operations.

    Provides CRUD operations for feature flags with authorization.
    All operations require admin privileges.
    """

    def __init__(self, repository: FeatureFlagRepository):
        self.repository = repository

    def _require_admin(self, user_context: UserContext, operation: str) -> None:
        """Check that the user is an admin."""
        if not user_context.is_admin():
            raise PermissionDeniedError(
                operation, "Only admins can manage feature flags"
            )

    def get_all(self, user_context: UserContext) -> list[FeatureFlag]:
        """
        Get all feature flags.

        Authorization: Admin only.
        """
        self._require_admin(user_context, "list_feature_flags")
        return self.repository.get_all()

    def get_by_name(
        self, flag_name: str, user_context: UserContext
    ) -> FeatureFlag:
        """
        Get a feature flag by name.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        self._require_admin(user_context, "get_feature_flag")
        flag = self.repository.get_by_name(flag_name)
        if flag is None:
            raise FeatureFlagNotFoundError(flag_name)
        return flag

    def create(
        self,
        name: str,
        enabled: bool,
        description: str,
        user_context: UserContext,
    ) -> FeatureFlag:
        """
        Create a new feature flag.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            DuplicateFeatureFlagError: If flag already exists
        """
        self._require_admin(user_context, "create_feature_flag")

        name = name.strip()
        if not name:
            raise ValueError("Flag name is required")

        if self.repository.exists(name):
            raise DuplicateFeatureFlagError(name)

        return self.repository.save(name, enabled, description)

    def update(
        self,
        flag_name: str,
        enabled: bool | None,
        description: str | None,
        user_context: UserContext,
    ) -> FeatureFlag:
        """
        Update a feature flag.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        self._require_admin(user_context, "update_feature_flag")

        existing = self.repository.get_by_name(flag_name)
        if existing is None:
            raise FeatureFlagNotFoundError(flag_name)

        new_enabled = enabled if enabled is not None else existing.enabled
        new_description = description if description is not None else existing.description

        return self.repository.save(flag_name, new_enabled, new_description)

    def delete(self, flag_name: str, user_context: UserContext) -> None:
        """
        Delete a feature flag.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        self._require_admin(user_context, "delete_feature_flag")

        if not self.repository.delete(flag_name):
            raise FeatureFlagNotFoundError(flag_name)

    def set_target_groups(
        self,
        flag_name: str,
        group_ids: list[UUID],
        user_context: UserContext,
    ) -> FeatureFlag:
        """
        Set the target groups for a feature flag (replaces existing).

        When a flag has target groups, it is only enabled for users in those groups.
        An empty list clears all targeting (flag applies to everyone when enabled).

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        self._require_admin(user_context, "set_flag_target_groups")

        if self.repository.get_by_name(flag_name) is None:
            raise FeatureFlagNotFoundError(flag_name)

        return self.repository.set_target_groups(flag_name, set(group_ids))

    def add_target_group(
        self,
        flag_name: str,
        group_id: UUID,
        user_context: UserContext,
    ) -> FeatureFlag:
        """
        Add a target group to a feature flag.

        Idempotent - no error if group already targeted.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        self._require_admin(user_context, "add_flag_target_group")

        if self.repository.get_by_name(flag_name) is None:
            raise FeatureFlagNotFoundError(flag_name)

        return self.repository.add_target_group(flag_name, group_id)

    def remove_target_group(
        self,
        flag_name: str,
        group_id: UUID,
        user_context: UserContext,
    ) -> FeatureFlag:
        """
        Remove a target group from a feature flag.

        Idempotent - no error if group not targeted.

        Authorization: Admin only.

        Raises:
            PermissionDeniedError: If user is not an admin
            FeatureFlagNotFoundError: If flag doesn't exist
        """
        self._require_admin(user_context, "remove_flag_target_group")

        if self.repository.get_by_name(flag_name) is None:
            raise FeatureFlagNotFoundError(flag_name)

        return self.repository.remove_target_group(flag_name, group_id)
