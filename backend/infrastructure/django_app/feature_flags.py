import logging
from typing import List, Optional, Set
from uuid import UUID

from application.ports.feature_flags import FeatureFlagPort
from application.ports.feature_flag_repository import FeatureFlag, FeatureFlagRepository
from domain.user_context import UserContext
from infrastructure.django_app.models import (
    FeatureFlagModel,
    FeatureFlagTargetModel,
)

logger = logging.getLogger(__name__)


class DjangoFeatureFlagAdapter(FeatureFlagPort):
    """
    Django ORM implementation of the feature flag port.

    Stores flags in the database. Unknown flags default to disabled.
    Supports user group targeting for granular feature rollouts.
    """

    def is_enabled(
        self, flag_name: str, user_context: Optional[UserContext] = None
    ) -> bool:
        """
        Check if a feature flag is enabled for a user.

        Targeting logic:
            - If flag doesn't exist: False
            - If flag.enabled is False: False (master kill switch)
            - If flag.enabled is True AND no target groups: True (enabled for all)
            - If flag.enabled is True AND has target groups:
              - If user_context is None: False (can't determine membership)
              - If user is in ANY target group: True
              - Otherwise: False

        Returns False on database errors (safe default).
        """
        try:
            flag = FeatureFlagModel.objects.prefetch_related(
                "target_groups__group"
            ).get(name=flag_name)

            # Master kill switch
            if not flag.enabled:
                return False

            # Get target group IDs
            target_group_ids = {target.group_id for target in flag.target_groups.all()}

            # No targeting = enabled for everyone
            if not target_group_ids:
                return True

            # Has targeting but no user context = disabled
            if user_context is None:
                return False

            # Check if user is in any target group
            return user_context.is_in_any_group(target_group_ids)

        except FeatureFlagModel.DoesNotExist:
            return False
        except Exception as e:
            logger.error(f"Error checking feature flag '{flag_name}': {e}")
            return False


class DjangoFeatureFlagRepository(FeatureFlagRepository):
    """
    Django ORM implementation of the feature flag repository.

    Provides CRUD operations for feature flag management.
    """

    def _to_domain(self, model: FeatureFlagModel) -> FeatureFlag:
        """Convert ORM model to domain object."""
        target_group_ids = frozenset(
            target.group_id for target in model.target_groups.all()
        )
        return FeatureFlag(
            name=model.name,
            enabled=model.enabled,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
            target_group_ids=target_group_ids,
        )

    def get_all(self) -> List[FeatureFlag]:
        """Get all feature flags."""
        return [
            self._to_domain(m)
            for m in FeatureFlagModel.objects.prefetch_related("target_groups").all()
        ]

    def get_by_name(self, name: str) -> Optional[FeatureFlag]:
        """Get a feature flag by name."""
        try:
            model = FeatureFlagModel.objects.prefetch_related("target_groups").get(
                name=name
            )
            return self._to_domain(model)
        except FeatureFlagModel.DoesNotExist:
            return None

    def exists(self, name: str) -> bool:
        """Check if a feature flag exists."""
        return FeatureFlagModel.objects.filter(name=name).exists()

    def save(self, name: str, enabled: bool, description: str = "") -> FeatureFlag:
        """Create or update a feature flag."""
        model, _ = FeatureFlagModel.objects.update_or_create(
            name=name,
            defaults={"enabled": enabled, "description": description},
        )
        model.refresh_from_db()
        return self._to_domain(model)

    def delete(self, name: str) -> bool:
        """Delete a feature flag by name."""
        deleted_count, _ = FeatureFlagModel.objects.filter(name=name).delete()
        return deleted_count > 0

    def set_target_groups(self, flag_name: str, group_ids: Set[UUID]) -> FeatureFlag:
        """Set the target groups for a feature flag (replaces existing)."""
        flag = FeatureFlagModel.objects.get(name=flag_name)
        # Clear existing targets
        FeatureFlagTargetModel.objects.filter(feature_flag=flag).delete()
        # Add new targets
        for group_id in group_ids:
            FeatureFlagTargetModel.objects.create(
                feature_flag=flag,
                group_id=group_id,
            )
        flag.refresh_from_db()
        return self._to_domain(flag)

    def add_target_group(self, flag_name: str, group_id: UUID) -> FeatureFlag:
        """Add a target group to a feature flag."""
        flag = FeatureFlagModel.objects.get(name=flag_name)
        FeatureFlagTargetModel.objects.get_or_create(
            feature_flag=flag,
            group_id=group_id,
        )
        flag.refresh_from_db()
        return self._to_domain(flag)

    def remove_target_group(self, flag_name: str, group_id: UUID) -> FeatureFlag:
        """Remove a target group from a feature flag."""
        flag = FeatureFlagModel.objects.get(name=flag_name)
        FeatureFlagTargetModel.objects.filter(
            feature_flag=flag,
            group_id=group_id,
        ).delete()
        flag.refresh_from_db()
        return self._to_domain(flag)


# Singleton instances for easy access
_feature_flags: Optional[FeatureFlagPort] = None
_feature_flag_repository: Optional[FeatureFlagRepository] = None


def get_feature_flags() -> FeatureFlagPort:
    """Get the feature flag adapter singleton."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = DjangoFeatureFlagAdapter()
    return _feature_flags


def get_feature_flag_repository() -> FeatureFlagRepository:
    """Get the feature flag repository singleton."""
    global _feature_flag_repository
    if _feature_flag_repository is None:
        _feature_flag_repository = DjangoFeatureFlagRepository()
    return _feature_flag_repository
