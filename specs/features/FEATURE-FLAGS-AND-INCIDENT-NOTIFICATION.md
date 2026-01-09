# Feature Flags and Incident Notification

This document specifies the feature flag system and its first use case: incident email notifications for server errors.

## Overview

Feature flags enable toggling features on/off without code changes or deployments. This system provides:

1. **Simple on/off toggles** - Boolean flags stored in the database
2. **User group targeting** - Enable features for specific groups of users
3. **Admin management API** - CRUD endpoints for flag and group administration
4. **Clean hexagonal architecture** - Port/adapter pattern for swappable implementations
5. **Incident email notifications** - First feature controlled by a flag

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
    def is_enabled(self, flag_name: str, user_context: UserContext | None = None) -> bool:
        """
        Check if a feature flag is enabled for a user.

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
```

### Database Models

#### FeatureFlagModel

Stores flags with:
- `name` (unique) - Flag identifier
- `enabled` - Boolean toggle (master kill switch)
- `description` - Human-readable description
- `created_at`, `updated_at` - Timestamps

#### UserGroupModel

Stores user groups for targeting:
- `id` (UUID) - Primary key
- `name` (unique) - Group identifier (e.g., "beta_testers", "internal_users")
- `description` - Human-readable description
- `created_at` - Timestamp

#### UserGroupMembershipModel

Many-to-many relationship between users and groups:
- `user_profile` - Foreign key to UserProfile
- `group` - Foreign key to UserGroupModel
- `added_at` - Timestamp

#### FeatureFlagTargetModel

Many-to-many relationship between flags and target groups:
- `feature_flag` - Foreign key to FeatureFlagModel
- `group` - Foreign key to UserGroupModel

### Behavior

- Unknown flags default to **disabled** (False)
- Database errors default to **disabled** (fail safe)
- Flag changes take effect immediately (no caching)
- `enabled=False` is a master kill switch - disables for everyone regardless of targeting
- Flags with no target groups are enabled for everyone when `enabled=True`
- Flags with target groups are only enabled for users in those groups

### Admin API Endpoints

All endpoints require admin authentication.

#### Feature Flag Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/feature-flags/` | List all flags |
| POST | `/api/admin/feature-flags/create/` | Create a new flag |
| GET | `/api/admin/feature-flags/{name}/` | Get flag details |
| PUT | `/api/admin/feature-flags/{name}/` | Update flag |
| DELETE | `/api/admin/feature-flags/{name}/` | Delete flag |
| PUT | `/api/admin/feature-flags/{name}/targets/` | Set target groups (replaces existing) |
| POST | `/api/admin/feature-flags/{name}/targets/add/` | Add target group |
| DELETE | `/api/admin/feature-flags/{name}/targets/{group_id}/` | Remove target group |

#### User Group Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/user-groups/` | List all groups |
| POST | `/api/admin/user-groups/create/` | Create a new group |
| GET | `/api/admin/user-groups/{id}/` | Get group details |
| DELETE | `/api/admin/user-groups/{id}/` | Delete group |
| GET | `/api/admin/user-groups/{id}/users/` | List users in group |
| POST | `/api/admin/user-groups/{id}/users/` | Add user to group |
| DELETE | `/api/admin/user-groups/{id}/users/{user_id}/` | Remove user from group |

#### Feature Flag Create Request

```json
{
  "name": "incident_email_notifications",
  "enabled": false,
  "description": "Send email alerts on 500 errors"
}
```

#### Feature Flag Response Format

```json
{
  "name": "incident_email_notifications",
  "enabled": false,
  "description": "Send email alerts on 500 errors",
  "created_at": "2025-01-05T10:30:00Z",
  "updated_at": "2025-01-05T10:30:00Z",
  "target_group_ids": []
}
```

#### User Group Response Format

```json
{
  "id": "uuid-string",
  "name": "beta_testers",
  "description": "Users who have opted into beta testing"
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

## User Group Targeting

### Concept

User groups are separate from roles:
- **Roles** are for authorization (what you CAN do) - e.g., Admin, Customer
- **Groups** are for targeting (which features you SEE) - e.g., beta_testers, internal_users

A user can have one role but belong to multiple groups. Groups enable granular feature rollouts without changing a user's permissions.

### Usage Example

Enable a beta feature for specific users:

1. Create a user group:
```bash
curl -X POST http://localhost:8000/api/admin/user-groups/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "beta_testers", "description": "Users testing new features"}'
```

2. Add users to the group:
```bash
curl -X POST http://localhost:8000/api/admin/user-groups/{group_id}/users/ \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-uuid-here"}'
```

3. Create a feature flag targeting the group:
```bash
curl -X POST http://localhost:8000/api/admin/feature-flags/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "new_dashboard", "enabled": true, "description": "New dashboard UI"}'

curl -X POST http://localhost:8000/api/admin/feature-flags/new_dashboard/targets/add/ \
  -H "Content-Type: application/json" \
  -d '{"group_id": "group-uuid-here"}'
```

4. Check the flag in code:
```python
if feature_flags.is_enabled("new_dashboard", user_context):
    # Show new dashboard to this user
```

### Design Decisions

#### Groups vs Multi-Role

We chose to add a separate groups concept rather than allowing multiple roles because:
- Roles have semantic meaning for authorization
- Groups are ad-hoc collections for targeting
- A user can be a "Customer" role but in "beta_testers" and "power_users" groups

#### Match Logic: ANY

When a flag targets multiple groups, a user matches if they're in ANY group (not ALL). This is the most common pattern for feature rollouts - e.g., "enable for beta testers OR internal users".

## Future Enhancements

Potential enhancements:

1. **Percentage rollouts** - Enable for X% of requests
2. **Flag dependencies** - Flag A requires Flag B to be enabled
3. **Caching** - Cache flag values to reduce DB queries
4. **External providers** - Adapter for LaunchDarkly, Flagsmith, etc.
5. **Role-based targeting** - Target flags to specific roles in addition to groups
