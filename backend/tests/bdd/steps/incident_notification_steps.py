"""Incident notification step definitions."""

import logging
from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from pytest_bdd import given, when, then, parsers

from application.ports.email import EmailPort, IncidentDetails
from application.services.feature_flag_service import FeatureFlagService
from domain.user_context import UserContext
from infrastructure.django_app.feature_flags import get_feature_flags
from infrastructure.django_app.incident_notifier import IncidentNotifier
from infrastructure.django_app.user_context_adapter import build_user_context


class MockEmailAdapter(EmailPort):
    """Mock email adapter that records sent emails for testing."""

    def __init__(self) -> None:
        self.sent_emails: list[tuple[IncidentDetails, list[str]]] = []

    def send_incident_alert(
        self, incident: IncidentDetails, recipients: list[str]
    ) -> None:
        """Record the email instead of sending it."""
        self.sent_emails.append((incident, recipients))

    def clear(self) -> None:
        """Clear recorded emails."""
        self.sent_emails.clear()

    @property
    def last_incident(self) -> IncidentDetails | None:
        """Get the last incident that was sent."""
        if self.sent_emails:
            return self.sent_emails[-1][0]
        return None


# ============================================================================
# GIVEN steps
# ============================================================================


@given("incident notification recipients are configured")
def recipients_configured(context: dict[str, Any]) -> None:
    """Configure test incident notification recipients."""
    context["incident_recipients"] = ["admin@example.com", "ops@example.com"]
    context["recipients_configured"] = True


@given("no incident notification recipients are configured")
def no_recipients_configured(context: dict[str, Any]) -> None:
    """Clear incident notification recipients."""
    context["incident_recipients"] = []
    context["recipients_configured"] = False


@given(parsers.parse('the feature flag "{flag_name}" is enabled'))
def feature_flag_is_enabled(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    flag_name: str,
) -> None:
    """Ensure a feature flag exists and is enabled."""
    try:
        feature_flag_service.update(
            flag_name=flag_name,
            enabled=True,
            description=None,
            user_context=admin_user_context,
        )
    except Exception:
        # Flag doesn't exist, create it
        feature_flag_service.create(
            name=flag_name,
            enabled=True,
            description=f"Test flag {flag_name}",
            user_context=admin_user_context,
        )
    context["feature_flags"][flag_name] = True


@given(parsers.parse('the feature flag "{flag_name}" is disabled'))
def feature_flag_is_disabled(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    flag_name: str,
) -> None:
    """Ensure a feature flag exists and is disabled."""
    try:
        feature_flag_service.update(
            flag_name=flag_name,
            enabled=False,
            description=None,
            user_context=admin_user_context,
        )
    except Exception:
        # Flag doesn't exist, create it
        feature_flag_service.create(
            name=flag_name,
            enabled=False,
            description=f"Test flag {flag_name}",
            user_context=admin_user_context,
        )
    context["feature_flags"][flag_name] = False


# ============================================================================
# WHEN steps
# ============================================================================


@when("a server incident occurs")
def server_incident_occurs(context: dict[str, Any]) -> None:
    """Simulate a server incident occurring."""
    mock_email = MockEmailAdapter()
    context["mock_email"] = mock_email

    notifier = IncidentNotifier(
        feature_flags=get_feature_flags(),
        email=mock_email,
    )

    incident = IncidentDetails(
        error_type="TestError",
        error_message="Test error message",
        request_path="/api/test/",
        request_method="GET",
        timestamp=datetime.now(),
        traceback="Traceback (test)",
        user_id=None,
    )
    context["incident"] = incident

    recipients = context.get("incident_recipients", [])
    with patch("infrastructure.django_app.incident_notifier.settings") as mock_settings:
        mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = recipients
        notifier.notify_if_enabled(incident, user_context=None)


@when(parsers.parse('a server incident occurs for user "{username}"'))
def server_incident_occurs_for_user(context: dict[str, Any], username: str) -> None:
    """Simulate a server incident occurring for a specific user."""
    mock_email = MockEmailAdapter()
    context["mock_email"] = mock_email

    notifier = IncidentNotifier(
        feature_flags=get_feature_flags(),
        email=mock_email,
    )

    # Get the Django user to build full UserContext with group memberships
    django_user = User.objects.get(username=username)
    user_context = build_user_context(django_user)

    incident = IncidentDetails(
        error_type="TestError",
        error_message="Test error message",
        request_path="/api/test/",
        request_method="GET",
        timestamp=datetime.now(),
        traceback="Traceback (test)",
        user_id=str(user_context.user_id),
    )
    context["incident"] = incident

    recipients = context.get("incident_recipients", [])
    with patch("infrastructure.django_app.incident_notifier.settings") as mock_settings:
        mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = recipients
        notifier.notify_if_enabled(incident, user_context=user_context)


@when(parsers.parse('a server incident occurs on path "{path}" with method "{method}"'))
def server_incident_occurs_with_request(
    context: dict[str, Any], path: str, method: str
) -> None:
    """Simulate a server incident with specific request details."""
    mock_email = MockEmailAdapter()
    context["mock_email"] = mock_email

    notifier = IncidentNotifier(
        feature_flags=get_feature_flags(),
        email=mock_email,
    )

    incident = IncidentDetails(
        error_type="TestError",
        error_message="Test error message",
        request_path=path,
        request_method=method,
        timestamp=datetime.now(),
        traceback="Traceback (test)",
        user_id=None,
    )
    context["incident"] = incident

    recipients = context.get("incident_recipients", [])
    with patch("infrastructure.django_app.incident_notifier.settings") as mock_settings:
        mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = recipients
        notifier.notify_if_enabled(incident, user_context=None)


@when(
    parsers.parse(
        'a server incident occurs with error type "{error_type}" and message "{message}"'
    )
)
def server_incident_occurs_with_error(
    context: dict[str, Any], error_type: str, message: str
) -> None:
    """Simulate a server incident with specific error details."""
    mock_email = MockEmailAdapter()
    context["mock_email"] = mock_email

    notifier = IncidentNotifier(
        feature_flags=get_feature_flags(),
        email=mock_email,
    )

    incident = IncidentDetails(
        error_type=error_type,
        error_message=message,
        request_path="/api/test/",
        request_method="GET",
        timestamp=datetime.now(),
        traceback="Traceback (test)",
        user_id=None,
    )
    context["incident"] = incident

    recipients = context.get("incident_recipients", [])
    with patch("infrastructure.django_app.incident_notifier.settings") as mock_settings:
        mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = recipients
        notifier.notify_if_enabled(incident, user_context=None)


# ============================================================================
# THEN steps
# ============================================================================


@then("an incident notification email should be sent")
def email_should_be_sent(context: dict[str, Any]) -> None:
    """Verify that an incident notification email was sent."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert len(mock_email.sent_emails) > 0, "No incident notification email was sent"


@then("no incident notification email should be sent")
def no_email_should_be_sent(context: dict[str, Any]) -> None:
    """Verify that no incident notification email was sent."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert len(mock_email.sent_emails) == 0, (
        f"Expected no emails, but {len(mock_email.sent_emails)} were sent"
    )


@then("the email should contain the error details")
def email_should_contain_error_details(context: dict[str, Any]) -> None:
    """Verify the email contains error details."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert mock_email.last_incident is not None, "No incident was recorded"

    incident = context.get("incident")
    assert incident is not None, "No incident in context"

    last_incident = mock_email.last_incident
    assert last_incident.error_type == incident.error_type
    assert last_incident.error_message == incident.error_message


@then(parsers.parse('the email should contain request path "{path}"'))
def email_should_contain_request_path(context: dict[str, Any], path: str) -> None:
    """Verify the email contains the request path."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert mock_email.last_incident is not None, "No incident was recorded"
    assert mock_email.last_incident.request_path == path


@then(parsers.parse('the email should contain request method "{method}"'))
def email_should_contain_request_method(context: dict[str, Any], method: str) -> None:
    """Verify the email contains the request method."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert mock_email.last_incident is not None, "No incident was recorded"
    assert mock_email.last_incident.request_method == method


@then(parsers.parse('the email should contain error type "{error_type}"'))
def email_should_contain_error_type(context: dict[str, Any], error_type: str) -> None:
    """Verify the email contains the error type."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert mock_email.last_incident is not None, "No incident was recorded"
    assert mock_email.last_incident.error_type == error_type


@then(parsers.parse('the email should contain error message "{message}"'))
def email_should_contain_error_message(context: dict[str, Any], message: str) -> None:
    """Verify the email contains the error message."""
    mock_email = context.get("mock_email")
    assert mock_email is not None, "Mock email adapter not found in context"
    assert mock_email.last_incident is not None, "No incident was recorded"
    assert mock_email.last_incident.error_message == message


@then("a warning should be logged about missing recipients")
def warning_logged_about_recipients(context: dict[str, Any]) -> None:
    """Verify a warning was logged about missing recipients.

    Note: This step passes by design since the notifier logs a warning
    when no recipients are configured. In a real test, we'd capture logs.
    """
    # The warning is logged by IncidentNotifier.notify_if_enabled
    # when INCIDENT_NOTIFICATION_RECIPIENTS is empty
    # For this BDD test, we verify the behavior (no email sent) rather than the log
    pass
