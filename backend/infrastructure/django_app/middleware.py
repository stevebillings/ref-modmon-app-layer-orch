import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable

from django.http import HttpRequest, HttpResponse

from application.ports.email import IncidentDetails

logger = logging.getLogger(__name__)

# Thread pool for async notification dispatch
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="incident_notify")


class IncidentNotificationMiddleware:
    """
    Middleware to capture unhandled exceptions and send incident notifications.

    Catches exceptions during request processing and dispatches notifications
    asynchronously so they don't block the error response. The feature flag
    check happens in the notifier, so this middleware always captures errors
    but only sends notifications when enabled.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        return self.get_response(request)

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> HttpResponse | None:
        """
        Called when a view raises an exception.

        Captures exception details and dispatches notification asynchronously.
        Returns None to let Django's normal error handling continue.
        """
        # Build incident details
        user_id = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)

        incident = IncidentDetails(
            error_type=type(exception).__name__,
            error_message=str(exception),
            request_path=request.path,
            request_method=request.method or "UNKNOWN",
            timestamp=datetime.now(timezone.utc),
            traceback=traceback.format_exc(),
            user_id=user_id,
        )

        # Dispatch notification asynchronously
        _executor.submit(self._send_notification, incident)

        # Return None to let Django's normal error handling continue
        return None

    def _send_notification(self, incident: IncidentDetails) -> None:
        """Send notification in background thread."""
        try:
            # Import here to avoid circular imports and ensure
            # Django is fully initialized
            from infrastructure.django_app.incident_notifier import (
                get_incident_notifier,
            )

            notifier = get_incident_notifier()
            notifier.notify_if_enabled(incident)
        except Exception as e:
            logger.error(f"Failed to send incident notification: {e}")
