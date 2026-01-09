"""
Adapter to convert Django User to domain UserContext.

This is the bridge between Django's authentication system and the
domain layer's framework-agnostic UserContext.
"""

from django.contrib.auth.models import User

from domain.user_context import Role, UserContext


def build_user_context(user: User) -> UserContext:
    """
    Convert Django User to domain UserContext.

    Args:
        user: Authenticated Django User with related UserProfile

    Returns:
        UserContext for use in application services

    Raises:
        UserProfile.DoesNotExist: If user has no profile
    """
    profile = user.profile  # OneToOne relation

    role = Role.ADMIN if profile.role == "admin" else Role.CUSTOMER

    # Get user's group IDs for feature flag targeting
    group_ids = frozenset(
        membership.group_id for membership in profile.group_memberships.all()
    )

    return UserContext(
        user_id=profile.id,
        username=user.username,
        role=role,
        group_ids=group_ids,
    )
