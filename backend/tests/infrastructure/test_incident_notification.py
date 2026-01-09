"""Tests for incident notification infrastructure."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from application.ports.email import EmailPort, IncidentDetails
from application.ports.feature_flags import FeatureFlagPort
from infrastructure.django_app.incident_notifier import (
    INCIDENT_EMAIL_FLAG,
    IncidentNotifier,
)
from infrastructure.django_app.models import FeatureFlagModel


@pytest.fixture
def sample_incident() -> IncidentDetails:
    """Create a sample incident for testing."""
    return IncidentDetails(
        error_type="ValueError",
        error_message="Something went wrong",
        request_path="/api/test/",
        request_method="POST",
        timestamp=datetime.now(timezone.utc),
        traceback="Traceback (most recent call last):\n  ...",
        user_id="user-123",
    )


class TestIncidentDetails:
    """Tests for the IncidentDetails value object."""

    def test_incident_details_is_immutable(self, sample_incident: IncidentDetails) -> None:
        with pytest.raises(AttributeError):
            sample_incident.error_type = "NewError"  # type: ignore

    def test_incident_details_optional_user_id(self) -> None:
        incident = IncidentDetails(
            error_type="Error",
            error_message="message",
            request_path="/",
            request_method="GET",
            timestamp=datetime.now(timezone.utc),
            traceback="",
        )
        assert incident.user_id is None


class TestIncidentNotifier:
    """Tests for the IncidentNotifier service."""

    def test_notify_when_flag_enabled(self, sample_incident: IncidentDetails) -> None:
        mock_flags = MagicMock(spec=FeatureFlagPort)
        mock_flags.is_enabled.return_value = True
        mock_email = MagicMock(spec=EmailPort)

        notifier = IncidentNotifier(feature_flags=mock_flags, email=mock_email)

        with patch(
            "infrastructure.django_app.incident_notifier.settings"
        ) as mock_settings:
            mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = ["dev@example.com"]
            notifier.notify_if_enabled(sample_incident)

        mock_flags.is_enabled.assert_called_once_with(INCIDENT_EMAIL_FLAG, None)
        mock_email.send_incident_alert.assert_called_once_with(
            sample_incident, ["dev@example.com"]
        )

    def test_no_notification_when_flag_disabled(
        self, sample_incident: IncidentDetails
    ) -> None:
        mock_flags = MagicMock(spec=FeatureFlagPort)
        mock_flags.is_enabled.return_value = False
        mock_email = MagicMock(spec=EmailPort)

        notifier = IncidentNotifier(feature_flags=mock_flags, email=mock_email)
        notifier.notify_if_enabled(sample_incident)

        mock_flags.is_enabled.assert_called_once_with(INCIDENT_EMAIL_FLAG, None)
        mock_email.send_incident_alert.assert_not_called()

    def test_no_notification_when_no_recipients(
        self, sample_incident: IncidentDetails
    ) -> None:
        mock_flags = MagicMock(spec=FeatureFlagPort)
        mock_flags.is_enabled.return_value = True
        mock_email = MagicMock(spec=EmailPort)

        notifier = IncidentNotifier(feature_flags=mock_flags, email=mock_email)

        with patch(
            "infrastructure.django_app.incident_notifier.settings"
        ) as mock_settings:
            mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = []
            notifier.notify_if_enabled(sample_incident)

        mock_email.send_incident_alert.assert_not_called()


@pytest.mark.django_db
class TestIncidentNotifierIntegration:
    """Integration tests with real feature flags."""

    def test_integration_with_real_feature_flag(
        self, sample_incident: IncidentDetails
    ) -> None:
        # Create the flag in disabled state
        FeatureFlagModel.objects.create(
            name=INCIDENT_EMAIL_FLAG,
            enabled=False,
        )

        from infrastructure.django_app.feature_flags import DjangoFeatureFlagAdapter

        mock_email = MagicMock(spec=EmailPort)
        notifier = IncidentNotifier(
            feature_flags=DjangoFeatureFlagAdapter(),
            email=mock_email,
        )

        with patch(
            "infrastructure.django_app.incident_notifier.settings"
        ) as mock_settings:
            mock_settings.INCIDENT_NOTIFICATION_RECIPIENTS = ["dev@example.com"]

            # Flag disabled - no notification
            notifier.notify_if_enabled(sample_incident)
            mock_email.send_incident_alert.assert_not_called()

            # Enable the flag
            flag = FeatureFlagModel.objects.get(name=INCIDENT_EMAIL_FLAG)
            flag.enabled = True
            flag.save()

            # Now notification should be sent
            notifier.notify_if_enabled(sample_incident)
            mock_email.send_incident_alert.assert_called_once()
