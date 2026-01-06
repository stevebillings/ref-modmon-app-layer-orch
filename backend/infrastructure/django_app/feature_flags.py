import logging

from application.ports.feature_flags import FeatureFlagPort
from application.ports.feature_flag_repository import FeatureFlag, FeatureFlagRepository
from infrastructure.django_app.models import FeatureFlagModel

logger = logging.getLogger(__name__)


class DjangoFeatureFlagAdapter(FeatureFlagPort):
    """
    Django ORM implementation of the feature flag port.

    Stores flags in the database. Unknown flags default to disabled.
    """

    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Returns False if flag doesn't exist or on database errors.
        """
        try:
            flag = FeatureFlagModel.objects.get(name=flag_name)
            return flag.enabled
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
        return FeatureFlag(
            name=model.name,
            enabled=model.enabled,
            description=model.description,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_all(self) -> list[FeatureFlag]:
        """Get all feature flags."""
        return [self._to_domain(m) for m in FeatureFlagModel.objects.all()]

    def get_by_name(self, name: str) -> FeatureFlag | None:
        """Get a feature flag by name."""
        try:
            model = FeatureFlagModel.objects.get(name=name)
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


# Singleton instances for easy access
_feature_flags: FeatureFlagPort | None = None
_feature_flag_repository: FeatureFlagRepository | None = None


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
