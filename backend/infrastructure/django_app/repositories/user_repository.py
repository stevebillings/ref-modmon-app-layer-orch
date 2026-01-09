"""
Django ORM implementation of the UserRepository.

Provides read/write access to user profiles for admin management.
"""

from uuid import UUID

from application.ports.user_repository import UserRepository
from domain.user_context import Role
from domain.user_info import UserInfo
from infrastructure.django_app.models import (
    UserGroupMembershipModel,
    UserProfile,
)


class DjangoUserRepository(UserRepository):
    """
    Django ORM implementation of UserRepository.

    Queries UserProfile and related models to provide user management.
    """

    def _to_domain(self, profile: UserProfile, group_ids: frozenset[UUID]) -> UserInfo:
        """Convert ORM model to domain object."""
        return UserInfo(
            id=profile.id,
            username=profile.user.username,
            email=profile.user.email,
            role=Role(profile.role),
            group_ids=group_ids,
        )

    def _get_group_ids(self, profile_id: UUID) -> frozenset[UUID]:
        """Get all group IDs for a user profile."""
        memberships = UserGroupMembershipModel.objects.filter(
            user_profile_id=profile_id
        ).values_list("group_id", flat=True)
        return frozenset(memberships)

    def get_all(self) -> list[UserInfo]:
        """Get all users with their profile information."""
        profiles = UserProfile.objects.select_related("user").order_by("user__username")

        # Batch load group memberships for efficiency
        profile_ids = [p.id for p in profiles]
        memberships = UserGroupMembershipModel.objects.filter(
            user_profile_id__in=profile_ids
        ).values("user_profile_id", "group_id")

        # Build group_ids map
        group_ids_by_profile: dict[UUID, set[UUID]] = {pid: set() for pid in profile_ids}
        for m in memberships:
            group_ids_by_profile[m["user_profile_id"]].add(m["group_id"])

        return [
            self._to_domain(p, frozenset(group_ids_by_profile.get(p.id, set())))
            for p in profiles
        ]

    def get_by_id(self, user_id: UUID) -> UserInfo | None:
        """Get a user by their profile ID."""
        try:
            profile = UserProfile.objects.select_related("user").get(id=user_id)
            group_ids = self._get_group_ids(user_id)
            return self._to_domain(profile, group_ids)
        except UserProfile.DoesNotExist:
            return None

    def update_role(self, user_id: UUID, role: Role) -> UserInfo | None:
        """Update a user's role."""
        try:
            profile = UserProfile.objects.select_related("user").get(id=user_id)
            profile.role = role.value
            profile.save(update_fields=["role"])
            group_ids = self._get_group_ids(user_id)
            return self._to_domain(profile, group_ids)
        except UserProfile.DoesNotExist:
            return None


# Singleton instance for easy access
_user_repository: UserRepository | None = None


def get_user_repository() -> UserRepository:
    """Get the user repository singleton."""
    global _user_repository
    if _user_repository is None:
        _user_repository = DjangoUserRepository()
    return _user_repository
