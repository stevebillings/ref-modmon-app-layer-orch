from abc import ABC, abstractmethod
from typing import Optional

from domain.user_context import UserContext


class FeatureFlagPort(ABC):
    """
    Port for checking feature flag status.

    Implementations may use database, config files, external services, etc.
    Unknown flags should default to disabled (False).
    """

    @abstractmethod
    def is_enabled(
        self, flag_name: str, user_context: Optional[UserContext] = None
    ) -> bool:
        """
        Check if a feature flag is enabled for a user.

        Args:
            flag_name: The unique name of the feature flag.
            user_context: Optional user context for targeted flags.
                         If None, only checks global enabled status.

        Returns:
            True if the flag is enabled for this user, False otherwise.

        Targeting logic:
            - If flag doesn't exist: False
            - If flag.enabled is False: False (master kill switch)
            - If flag.enabled is True AND no target groups: True (enabled for all)
            - If flag.enabled is True AND has target groups:
              - If user_context is None: False (can't determine membership)
              - If user is in ANY target group: True
              - Otherwise: False
        """
        pass
