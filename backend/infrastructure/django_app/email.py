import logging

from django.conf import settings
from django.core.mail import send_mail

from application.ports.email import EmailPort, IncidentDetails

logger = logging.getLogger(__name__)


class DjangoEmailAdapter(EmailPort):
    """
    Django implementation of the email port.

    Uses Django's email backend which can be configured for
    SMTP, console output (development), or other backends.
    """

    def send_incident_alert(
        self, incident: IncidentDetails, recipients: list[str]
    ) -> None:
        """
        Send an incident alert email using Django's mail system.

        Logs errors but does not raise - incident notifications
        should not break the error response flow.
        """
        if not recipients:
            logger.warning("No recipients configured for incident notifications")
            return

        subject = f"[INCIDENT] {incident.error_type} on {incident.request_path}"
        body = f"""Server Incident Alert
========================

Error Type: {incident.error_type}
Error Message: {incident.error_message}

Request Details:
- Method: {incident.request_method}
- Path: {incident.request_path}
- User ID: {incident.user_id or 'Anonymous'}
- Timestamp: {incident.timestamp.isoformat()}

Traceback:
{incident.traceback}
"""

        try:
            from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@example.com")
            send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=recipients,
                fail_silently=False,
            )
            logger.info(f"Incident alert sent to {len(recipients)} recipient(s)")
        except Exception as e:
            logger.error(f"Failed to send incident alert email: {e}")


# Singleton instance
_email_adapter: EmailPort | None = None


def get_email_adapter() -> EmailPort:
    """Get the email adapter singleton."""
    global _email_adapter
    if _email_adapter is None:
        _email_adapter = DjangoEmailAdapter()
    return _email_adapter
