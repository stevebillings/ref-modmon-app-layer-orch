from datetime import datetime
from typing import Any
from uuid import UUID

from application.ports.audit_log_repository import AuditLogEntry, AuditLogRepository
from infrastructure.django_app.models import AuditLogModel


class DjangoAuditLogRepository(AuditLogRepository):
    """
    Django ORM implementation of the audit log repository.

    Persists audit log entries to the database.
    """

    def _to_domain(self, model: AuditLogModel) -> AuditLogEntry:
        """Convert ORM model to domain object."""
        return AuditLogEntry(
            id=model.id,
            event_type=model.event_type,
            event_id=model.event_id,
            occurred_at=model.occurred_at,
            actor_id=model.actor_id,
            aggregate_type=model.aggregate_type,
            aggregate_id=model.aggregate_id,
            event_data=model.event_data,
            created_at=model.created_at,
        )

    def save(
        self,
        event_type: str,
        event_id: UUID,
        occurred_at: datetime,
        actor_id: str,
        aggregate_type: str,
        aggregate_id: UUID | None,
        event_data: dict[str, Any],
    ) -> AuditLogEntry:
        """Save an audit log entry."""
        # Build kwargs, using event_id as fallback for aggregate_id if not provided
        # (UUIDField doesn't accept None without null=True on the model)
        model = AuditLogModel.objects.create(
            event_type=event_type,
            event_id=event_id,
            occurred_at=occurred_at,
            actor_id=actor_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id if aggregate_id is not None else event_id,
            event_data=event_data,
        )
        return self._to_domain(model)


# Singleton instance
_audit_log_repository: AuditLogRepository | None = None


def get_audit_log_repository() -> AuditLogRepository:
    """Get the audit log repository singleton."""
    global _audit_log_repository
    if _audit_log_repository is None:
        _audit_log_repository = DjangoAuditLogRepository()
    return _audit_log_repository
