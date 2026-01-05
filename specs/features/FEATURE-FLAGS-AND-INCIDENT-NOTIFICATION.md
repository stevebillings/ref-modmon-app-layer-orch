# Feature Flags and Incident Notification

This document specifies the feature flag system and its first use case: incident email notifications for server errors.

## Overview

Feature flags enable toggling features on/off without code changes or deployments. This system provides:

1. **Simple on/off toggles** - Boolean flags stored in the database
2. **Admin management API** - CRUD endpoints for flag administration
3. **Clean hexagonal architecture** - Port/adapter pattern for swappable implementations
4. **Incident email notifications** - First feature controlled by a flag

## Feature Flag System

### Architecture

The feature flag system follows the hexagonal architecture pattern:

```
┌─────────────────────────────────────────────┐
│           Application Layer                 │
│                                             │
│         ┌─────────────────────┐             │
│         │ FeatureFlagPort     │             │
│         │ (interface)         │             │
│         │                     │             │
│         │ is_enabled(name)    │             │
│         └──────────┬──────────┘             │
└────────────────────┼────────────────────────┘
                     │
┌────────────────────┼────────────────────────┐
│ Infrastructure     │                        │
│         ┌──────────▼──────────┐             │
│         │ DjangoFeatureFlag   │             │
│         │ Adapter             │             │
│         │                     │             │
│         │ - Queries DB        │             │
│         │ - Returns False for │             │
│         │   unknown flags     │             │
│         └─────────────────────┘             │
└─────────────────────────────────────────────┘
```

### Port Interface

Located at `application/ports/feature_flags.py`:

```python
class FeatureFlagPort(ABC):
    @abstractmethod
    def is_enabled(self, flag_name: str) -> bool:
        """Returns True if flag exists and is enabled, False otherwise."""
        pass
```

### Database Model

The `FeatureFlagModel` stores flags with:
- `name` (unique) - Flag identifier
- `enabled` - Boolean toggle
- `description` - Human-readable description
- `created_at`, `updated_at` - Timestamps

### Behavior

- Unknown flags default to **disabled** (False)
- Database errors default to **disabled** (fail safe)
- Flag changes take effect immediately (no caching)

### Admin API Endpoints

All endpoints require admin authentication:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/feature-flags/` | List all flags |
| POST | `/api/admin/feature-flags/create/` | Create a new flag |
| GET | `/api/admin/feature-flags/{name}/` | Get flag details |
| PUT | `/api/admin/feature-flags/{name}/` | Update flag |
| DELETE | `/api/admin/feature-flags/{name}/` | Delete flag |

#### Create Request

```json
{
  "name": "incident_email_notifications",
  "enabled": false,
  "description": "Send email alerts on 500 errors"
}
```

#### Response Format

```json
{
  "name": "incident_email_notifications",
  "enabled": false,
  "description": "Send email alerts on 500 errors",
  "created_at": "2025-01-05T10:30:00Z",
  "updated_at": "2025-01-05T10:30:00Z"
}
```

## Incident Email Notification

### Purpose

Notify developers when server errors (500s) occur in production. This is controlled by the `incident_email_notifications` feature flag.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Middleware (captures exceptions)                            │
│                                                             │
│   process_exception(request, exception)                     │
│       │                                                     │
│       ▼                                                     │
│   IncidentDetails (value object)                            │
│       │                                                     │
│       ▼ (async, non-blocking)                               │
│   IncidentNotifier                                          │
│       │                                                     │
│       ├──► FeatureFlagPort.is_enabled("incident_email...")  │
│       │       │                                             │
│       │       └──► If disabled, stop here                   │
│       │                                                     │
│       └──► EmailPort.send_incident_alert(...)               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Components

#### IncidentDetails (Value Object)

Located at `application/ports/email.py`:

```python
@dataclass(frozen=True)
class IncidentDetails:
    error_type: str
    error_message: str
    request_path: str
    request_method: str
    timestamp: datetime
    traceback: str
    user_id: str | None = None
```

#### EmailPort (Interface)

```python
class EmailPort(ABC):
    @abstractmethod
    def send_incident_alert(
        self, incident: IncidentDetails, recipients: list[str]
    ) -> None:
        pass
```

#### IncidentNotifier (Service)

Coordinates the feature flag check and email sending:

```python
class IncidentNotifier:
    def __init__(self, feature_flags: FeatureFlagPort, email: EmailPort):
        self.feature_flags = feature_flags
        self.email = email

    def notify_if_enabled(self, incident: IncidentDetails) -> None:
        if not self.feature_flags.is_enabled("incident_email_notifications"):
            return  # Feature disabled, skip notification

        recipients = settings.INCIDENT_NOTIFICATION_RECIPIENTS
        self.email.send_incident_alert(incident, recipients)
```

#### IncidentNotificationMiddleware

Captures unhandled exceptions and dispatches notifications asynchronously:

```python
class IncidentNotificationMiddleware:
    def process_exception(self, request, exception):
        incident = IncidentDetails(
            error_type=type(exception).__name__,
            error_message=str(exception),
            request_path=request.path,
            # ... other fields
        )

        # Dispatch async to not block error response
        executor.submit(notifier.notify_if_enabled, incident)

        return None  # Let Django's error handling continue
```

### Configuration

In `settings.py`:

```python
# Email backend (console for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'incidents@example.com'

# Incident notification recipients
INCIDENT_NOTIFICATION_RECIPIENTS = ['dev-team@example.com']

# Middleware (must be added)
MIDDLEWARE = [
    # ... other middleware ...
    'infrastructure.django_app.middleware.IncidentNotificationMiddleware',
]
```

### Email Format

Subject: `[INCIDENT] {ErrorType} on {RequestPath}`

Body:
```
Server Incident Alert
========================

Error Type: ValueError
Error Message: Something went wrong

Request Details:
- Method: POST
- Path: /api/products/create/
- User ID: user-123
- Timestamp: 2025-01-05T10:30:00Z

Traceback:
{full traceback}
```

## Usage

### Enable Incident Notifications

1. Create the feature flag (admin only):

```bash
curl -X POST http://localhost:8000/api/admin/feature-flags/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "incident_email_notifications", "enabled": true, "description": "Email alerts for 500 errors"}'
```

2. Configure recipients in settings:

```python
INCIDENT_NOTIFICATION_RECIPIENTS = ['dev@company.com', 'oncall@company.com']
```

3. For production, configure SMTP:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
```

### Disable Incident Notifications

Toggle the flag off without code changes:

```bash
curl -X PUT http://localhost:8000/api/admin/feature-flags/incident_email_notifications/ \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}'
```

## Design Decisions

### Why Database Storage?

- Flags can be changed without deployment
- Works in multi-server environments
- Audit trail via standard database backups

### Why Async Notification?

- Doesn't block error response to client
- Failed notifications don't affect application behavior
- Background thread pool handles delivery

### Why Fail-Safe Defaults?

- Unknown flags return `false` (disabled)
- Database errors return `false` (disabled)
- Notification failures are logged but don't break requests

## Future Enhancements

The current implementation is intentionally minimal. Potential enhancements:

1. **User/context-aware flags** - Enable features for specific users or roles
2. **Percentage rollouts** - Enable for X% of requests
3. **Flag dependencies** - Flag A requires Flag B to be enabled
4. **Caching** - Cache flag values to reduce DB queries
5. **External providers** - Adapter for LaunchDarkly, Flagsmith, etc.
