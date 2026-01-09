"""
User groups for feature flag targeting.

User groups are separate from roles - roles are for authorization (what you can do),
while groups are for targeting (which features you see). A user can belong to
multiple groups (e.g., "beta_testers", "internal_users", "enterprise_customers").

This module provides a framework-agnostic representation of user groups.
It contains no Django dependencies.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserGroup:
    """
    Domain representation of a user group.

    Immutable value object. Groups have no behavior - they are
    simply named collections of users for feature flag targeting.
    """

    id: UUID
    name: str
    description: str
