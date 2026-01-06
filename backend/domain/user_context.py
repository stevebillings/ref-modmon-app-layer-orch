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


class Capability(Enum):
    """User capabilities for fine-grained UI control."""

    # Product capabilities
    PRODUCTS_VIEW = "products:view"
    PRODUCTS_CREATE = "products:create"
    PRODUCTS_DELETE = "products:delete"
    PRODUCTS_RESTORE = "products:restore"
    PRODUCTS_VIEW_DELETED = "products:view_deleted"
    PRODUCTS_REPORT = "products:report"

    # Cart capabilities
    CART_VIEW = "cart:view"
    CART_MODIFY = "cart:modify"
    CART_SUBMIT = "cart:submit"

    # Order capabilities
    ORDERS_VIEW_OWN = "orders:view_own"
    ORDERS_VIEW_ALL = "orders:view_all"

    # Feature flag capabilities
    FEATURE_FLAGS_MANAGE = "feature_flags:manage"


ROLE_CAPABILITIES: dict[Role, frozenset["Capability"]] = {
    Role.ADMIN: frozenset(
        {
            Capability.PRODUCTS_VIEW,
            Capability.PRODUCTS_CREATE,
            Capability.PRODUCTS_DELETE,
            Capability.PRODUCTS_RESTORE,
            Capability.PRODUCTS_VIEW_DELETED,
            Capability.PRODUCTS_REPORT,
            Capability.CART_VIEW,
            Capability.CART_MODIFY,
            Capability.CART_SUBMIT,
            Capability.ORDERS_VIEW_OWN,
            Capability.ORDERS_VIEW_ALL,
            Capability.FEATURE_FLAGS_MANAGE,
        }
    ),
    Role.CUSTOMER: frozenset(
        {
            Capability.PRODUCTS_VIEW,
            Capability.CART_VIEW,
            Capability.CART_MODIFY,
            Capability.CART_SUBMIT,
            Capability.ORDERS_VIEW_OWN,
        }
    ),
}


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

    def get_capabilities(self) -> frozenset[Capability]:
        """Return the set of capabilities for this user's role."""
        return ROLE_CAPABILITIES.get(self.role, frozenset())

    def has_capability(self, capability: Capability) -> bool:
        """Check if user has a specific capability."""
        return capability in self.get_capabilities()
