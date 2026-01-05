import logging

from application.ports.feature_flags import FeatureFlagPort
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


# Singleton instance for easy access
_feature_flags: FeatureFlagPort | None = None


def get_feature_flags() -> FeatureFlagPort:
    """Get the feature flag adapter singleton."""
    global _feature_flags
    if _feature_flags is None:
        _feature_flags = DjangoFeatureFlagAdapter()
    return _feature_flags
