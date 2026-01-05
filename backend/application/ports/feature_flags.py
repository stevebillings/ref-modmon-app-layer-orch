from abc import ABC, abstractmethod


class FeatureFlagPort(ABC):
    """
    Port for checking feature flag status.

    Implementations may use database, config files, external services, etc.
    Unknown flags should default to disabled (False).
    """

    @abstractmethod
    def is_enabled(self, flag_name: str) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            flag_name: The unique name of the feature flag.

        Returns:
            True if the flag exists and is enabled, False otherwise.
        """
        pass
