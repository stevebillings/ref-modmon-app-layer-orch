import logging

from django.conf import settings

from application.ports.email import EmailPort, IncidentDetails
from application.ports.feature_flags import FeatureFlagPort
from domain.user_context import UserContext

logger = logging.getLogger(__name__)

# Feature flag name for incident email notifications
INCIDENT_EMAIL_FLAG = "incident_email_notifications"


class IncidentNotifier:
    """
    Coordinates incident notification with feature flag checking.

    Checks if the incident notification feature is enabled before
    sending emails. This allows the feature to be toggled without
    code changes or deployments.
    """

    def __init__(self, feature_flags: FeatureFlagPort, email: EmailPort):
        self.feature_flags = feature_flags
        self.email = email

    def notify_if_enabled(
        self, incident: IncidentDetails, user_context: UserContext | None = None
    ) -> None:
        """
        Send incident notification if the feature flag is enabled.

        Args:
            incident: Details about the server incident.
            user_context: Optional user context for targeted flag evaluation.
        """
        if not self.feature_flags.is_enabled(INCIDENT_EMAIL_FLAG, user_context):
            logger.debug(
                f"Incident notification skipped - '{INCIDENT_EMAIL_FLAG}' flag is disabled"
            )
            return

        recipients = getattr(settings, "INCIDENT_NOTIFICATION_RECIPIENTS", [])
        if not recipients:
            logger.warning(
                "INCIDENT_NOTIFICATION_RECIPIENTS not configured in settings"
            )
            return

        logger.info(
            f"Sending incident notification for {incident.error_type} "
            f"on {incident.request_path}"
        )
        self.email.send_incident_alert(incident, recipients)


# Singleton instance
_incident_notifier: IncidentNotifier | None = None


def get_incident_notifier() -> IncidentNotifier:
    """Get the incident notifier singleton with dependencies wired up."""
    global _incident_notifier
    if _incident_notifier is None:
        from infrastructure.django_app.email import get_email_adapter
        from infrastructure.django_app.feature_flags import get_feature_flags

        _incident_notifier = IncidentNotifier(
            feature_flags=get_feature_flags(),
            email=get_email_adapter(),
        )
    return _incident_notifier
