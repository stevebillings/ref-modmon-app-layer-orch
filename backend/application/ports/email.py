from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class IncidentDetails:
    """
    Value object containing details about a server incident.

    Used to communicate incident information between layers
    without coupling to specific error types or frameworks.
    """

    error_type: str
    error_message: str
    request_path: str
    request_method: str
    timestamp: datetime
    traceback: str
    user_id: str | None = None


class EmailPort(ABC):
    """
    Port for sending emails.

    Implementations may use SMTP, external services (SendGrid, etc.),
    or mock implementations for testing.
    """

    @abstractmethod
    def send_incident_alert(
        self, incident: IncidentDetails, recipients: list[str]
    ) -> None:
        """
        Send an incident alert email to the specified recipients.

        Args:
            incident: Details about the server incident.
            recipients: List of email addresses to notify.

        Raises:
            Exception: If email sending fails (implementations should log
                      but may choose to suppress or re-raise).
        """
        pass
