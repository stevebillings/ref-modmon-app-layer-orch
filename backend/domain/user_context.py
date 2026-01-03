"""
User context for authorization decisions.

This module provides a framework-agnostic representation of the authenticated
user for use in application services. It contains no Django dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class Role(Enum):
    """User roles for role-based access control."""

    ADMIN = "admin"
    CUSTOMER = "customer"


@dataclass(frozen=True)
class UserContext:
    """
    Immutable user context for authorization decisions.

    Passed from infrastructure layer through application layer to domain
    operations. Contains only the information needed for authorization
    and audit logging.
    """

    user_id: UUID
    username: str
    role: Role

    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.role == Role.ADMIN

    def is_customer(self) -> bool:
        """Check if user has customer role."""
        return self.role == Role.CUSTOMER

    @property
    def actor_id(self) -> str:
        """Return user identifier for audit logging in domain events."""
        return str(self.user_id)
