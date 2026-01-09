"""
Django ORM implementation of the UserGroupRepository.

Provides CRUD operations for user groups and membership management.
"""

from uuid import UUID

from application.ports.user_group_repository import UserGroupRepository
from domain.user_groups import UserGroup
from infrastructure.django_app.models import (
    UserGroupMembershipModel,
    UserGroupModel,
)


class DjangoUserGroupRepository(UserGroupRepository):
    """
    Django ORM implementation of UserGroupRepository.

    Provides CRUD operations for user groups and their memberships.
    """

    def _to_domain(self, model: UserGroupModel) -> UserGroup:
        """Convert ORM model to domain object."""
        return UserGroup(
            id=model.id,
            name=model.name,
            description=model.description,
        )

    def get_all(self) -> list[UserGroup]:
        """Get all user groups."""
        return [self._to_domain(m) for m in UserGroupModel.objects.all()]

    def get_by_id(self, group_id: UUID) -> UserGroup | None:
        """Get a user group by ID."""
        try:
            model = UserGroupModel.objects.get(id=group_id)
            return self._to_domain(model)
        except UserGroupModel.DoesNotExist:
            return None

    def get_by_name(self, name: str) -> UserGroup | None:
        """Get a user group by name."""
        try:
            model = UserGroupModel.objects.get(name=name)
            return self._to_domain(model)
        except UserGroupModel.DoesNotExist:
            return None

    def exists(self, name: str) -> bool:
        """Check if a user group with this name exists."""
        return UserGroupModel.objects.filter(name=name).exists()

    def save(self, name: str, description: str = "") -> UserGroup:
        """Create or update a user group."""
        model, _ = UserGroupModel.objects.update_or_create(
            name=name,
            defaults={"description": description},
        )
        return self._to_domain(model)

    def delete(self, group_id: UUID) -> bool:
        """Delete a user group by ID."""
        deleted_count, _ = UserGroupModel.objects.filter(id=group_id).delete()
        return deleted_count > 0

    def get_groups_for_user(self, user_id: UUID) -> list[UserGroup]:
        """Get all groups a user belongs to."""
        memberships = UserGroupMembershipModel.objects.filter(
            user_profile_id=user_id
        ).select_related("group")
        return [self._to_domain(m.group) for m in memberships]

    def get_group_ids_for_user(self, user_id: UUID) -> frozenset[UUID]:
        """Get all group IDs a user belongs to (optimized for UserContext)."""
        memberships = UserGroupMembershipModel.objects.filter(
            user_profile_id=user_id
        ).values_list("group_id", flat=True)
        return frozenset(memberships)

    def add_user_to_group(self, user_id: UUID, group_id: UUID) -> None:
        """Add a user to a group (idempotent)."""
        UserGroupMembershipModel.objects.get_or_create(
            user_profile_id=user_id,
            group_id=group_id,
        )

    def remove_user_from_group(self, user_id: UUID, group_id: UUID) -> None:
        """Remove a user from a group (idempotent)."""
        UserGroupMembershipModel.objects.filter(
            user_profile_id=user_id,
            group_id=group_id,
        ).delete()

    def get_user_ids_in_group(self, group_id: UUID) -> list[UUID]:
        """Get all user IDs in a group."""
        memberships = UserGroupMembershipModel.objects.filter(
            group_id=group_id
        ).values_list("user_profile_id", flat=True)
        return list(memberships)


# Singleton instance for easy access
_user_group_repository: UserGroupRepository | None = None


def get_user_group_repository() -> UserGroupRepository:
    """Get the user group repository singleton."""
    global _user_group_repository
    if _user_group_repository is None:
        _user_group_repository = DjangoUserGroupRepository()
    return _user_group_repository
