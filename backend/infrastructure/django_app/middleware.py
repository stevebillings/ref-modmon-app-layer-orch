import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from application.ports.email import IncidentDetails
from domain.user_context import UserContext

logger = logging.getLogger(__name__)
request_logger = logging.getLogger("infrastructure.request")

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

        Captures exception details, writes to audit log, and dispatches
        notification asynchronously.
        Returns None to let Django's normal error handling continue.
        """
        # Build incident details and user context
        user_id = None
        user_context: UserContext | None = None
        if hasattr(request, "user") and request.user.is_authenticated:
            user_id = str(request.user.id)
            # Build user context for feature flag targeting
            try:
                from infrastructure.django_app.user_context_adapter import (
                    build_user_context,
                )

                user_context = build_user_context(request.user)
            except Exception as e:
                logger.warning(f"Failed to build user context: {e}")

        now = datetime.now(timezone.utc)
        stack_trace = traceback.format_exc()

        incident = IncidentDetails(
            error_type=type(exception).__name__,
            error_message=str(exception),
            request_path=request.path,
            request_method=request.method or "UNKNOWN",
            timestamp=now,
            traceback=stack_trace,
            user_id=user_id,
        )

        # Write to audit log
        self._write_audit_log(exception, stack_trace, user_id, now)

        # Dispatch notification asynchronously
        _executor.submit(self._send_notification, incident, user_context)

        # Return None to let Django's normal error handling continue
        return None

    def _write_audit_log(
        self,
        exception: Exception,
        stack_trace: str,
        user_id: str | None,
        occurred_at: datetime,
    ) -> None:
        """Write exception to audit log."""
        try:
            from infrastructure.django_app.repositories.audit_log_repository import (
                get_audit_log_repository,
            )

            repository = get_audit_log_repository()
            event_id = uuid4()
            repository.save(
                event_type="UnhandledException",
                event_id=event_id,
                occurred_at=occurred_at,
                actor_id=user_id or "anonymous",
                aggregate_type="System",
                aggregate_id=None,
                event_data={
                    "error_type": type(exception).__name__,
                    "message": str(exception),
                    "stacktrace": stack_trace,
                },
            )
        except Exception as e:
            logger.error(f"Failed to write exception to audit log: {e}")

    def _send_notification(
        self, incident: IncidentDetails, user_context: UserContext | None = None
    ) -> None:
        """Send notification in background thread."""
        try:
            # Import here to avoid circular imports and ensure
            # Django is fully initialized
            from infrastructure.django_app.incident_notifier import (
                get_incident_notifier,
            )

            notifier = get_incident_notifier()
            notifier.notify_if_enabled(incident, user_context)
        except Exception as e:
            logger.error(f"Failed to send incident notification: {e}")


class RequestLoggingMiddleware:
    """
    Middleware to log HTTP requests with timing information.

    Logs method, path, status code, duration, and user ID for each request.
    Also generates a unique request ID for correlation across logs and events.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        from infrastructure.django_app.request_context import (
            clear_request_id,
            generate_request_id,
            set_request_id,
        )

        # Generate and set request ID for this request
        request_id = request.META.get("HTTP_X_REQUEST_ID") or generate_request_id()
        set_request_id(request_id)

        start_time = time.perf_counter()

        try:
            response = self.get_response(request)

            duration_ms = (time.perf_counter() - start_time) * 1000

            user_id = None
            if hasattr(request, "user") and request.user.is_authenticated:
                user_id = str(request.user.id)

            request_logger.info(
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "user_id": user_id,
                    "query_string": request.META.get("QUERY_STRING", ""),
                },
            )

            # Record metrics
            from infrastructure.django_app.metrics import record_request

            record_request(request.method or "UNKNOWN", request.path, response.status_code)

            # Add request ID to response headers for client correlation
            response["X-Request-ID"] = request_id

            return response
        finally:
            clear_request_id()
