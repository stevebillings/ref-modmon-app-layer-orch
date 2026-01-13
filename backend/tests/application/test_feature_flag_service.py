"""Unit tests for FeatureFlagService with mock repository."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from uuid import UUID, uuid4

import pytest

from application.ports.feature_flag_repository import FeatureFlag, FeatureFlagRepository
from application.services.feature_flag_service import (
    DuplicateFeatureFlagError,
    FeatureFlagNotFoundError,
    FeatureFlagService,
)
from domain.exceptions import PermissionDeniedError
from domain.user_context import Role, UserContext


class MockFeatureFlagRepository(FeatureFlagRepository):
    """In-memory mock implementation for testing."""

    def __init__(self) -> None:
        self._flags: Dict[str, FeatureFlag] = {}
        self._targets: Dict[str, Set[UUID]] = {}

    def get_all(self) -> List[FeatureFlag]:
        return list(self._flags.values())

    def get_by_name(self, name: str) -> Optional[FeatureFlag]:
        return self._flags.get(name)

    def exists(self, name: str) -> bool:
        return name in self._flags

    def save(self, name: str, enabled: bool, description: str = "") -> FeatureFlag:
        now = datetime.now(timezone.utc)
        existing = self._flags.get(name)
        target_groups = self._targets.get(name, set())
        flag = FeatureFlag(
            name=name,
            enabled=enabled,
            description=description,
            created_at=existing.created_at if existing else now,
            updated_at=now,
            target_group_ids=frozenset(target_groups),
        )
        self._flags[name] = flag
        return flag

    def delete(self, name: str) -> bool:
        if name in self._flags:
            del self._flags[name]
            self._targets.pop(name, None)
            return True
        return False

    def set_target_groups(self, flag_name: str, group_ids: Set[UUID]) -> FeatureFlag:
        self._targets[flag_name] = group_ids
        flag = self._flags[flag_name]
        updated_flag = FeatureFlag(
            name=flag.name,
            enabled=flag.enabled,
            description=flag.description,
            created_at=flag.created_at,
            updated_at=datetime.now(timezone.utc),
            target_group_ids=frozenset(group_ids),
        )
        self._flags[flag_name] = updated_flag
        return updated_flag

    def add_target_group(self, flag_name: str, group_id: UUID) -> FeatureFlag:
        if flag_name not in self._targets:
            self._targets[flag_name] = set()
        self._targets[flag_name].add(group_id)
        return self.set_target_groups(flag_name, self._targets[flag_name])

    def remove_target_group(self, flag_name: str, group_id: UUID) -> FeatureFlag:
        if flag_name in self._targets:
            self._targets[flag_name].discard(group_id)
        return self.set_target_groups(flag_name, self._targets.get(flag_name, set()))


def make_admin_context() -> UserContext:
    """Create an admin user context."""
    return UserContext(user_id=uuid4(), username="admin", role=Role.ADMIN)


def make_customer_context() -> UserContext:
    """Create a customer user context."""
    return UserContext(user_id=uuid4(), username="customer", role=Role.CUSTOMER)


class TestFeatureFlagServiceWithMock:
    """Unit tests for FeatureFlagService using mock repository."""

    def test_get_all_returns_all_flags(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("flag_a", True, "First flag")
        repo.save("flag_b", False, "Second flag")
        service = FeatureFlagService(repo)

        flags = service.get_all(make_admin_context())

        assert len(flags) == 2
        names = [f.name for f in flags]
        assert "flag_a" in names
        assert "flag_b" in names

    def test_get_all_requires_admin(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        with pytest.raises(PermissionDeniedError):
            service.get_all(make_customer_context())

    def test_get_by_name_returns_flag(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("test_flag", True, "A test flag")
        service = FeatureFlagService(repo)

        flag = service.get_by_name("test_flag", make_admin_context())

        assert flag.name == "test_flag"
        assert flag.enabled is True
        assert flag.description == "A test flag"

    def test_get_by_name_not_found_raises(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        with pytest.raises(FeatureFlagNotFoundError) as exc_info:
            service.get_by_name("nonexistent", make_admin_context())

        assert exc_info.value.flag_name == "nonexistent"

    def test_create_flag(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        flag = service.create(
            name="new_flag",
            enabled=True,
            description="A new flag",
            user_context=make_admin_context(),
        )

        assert flag.name == "new_flag"
        assert flag.enabled is True
        assert flag.description == "A new flag"
        assert repo.exists("new_flag")

    def test_create_duplicate_raises(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("existing", False)
        service = FeatureFlagService(repo)

        with pytest.raises(DuplicateFeatureFlagError) as exc_info:
            service.create("existing", True, "", make_admin_context())

        assert exc_info.value.flag_name == "existing"

    def test_create_empty_name_raises(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        with pytest.raises(ValueError) as exc_info:
            service.create("", True, "", make_admin_context())

        assert "required" in str(exc_info.value).lower()

    def test_create_requires_admin(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        with pytest.raises(PermissionDeniedError):
            service.create("flag", True, "", make_customer_context())

    def test_update_flag(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("update_me", False, "Original")
        service = FeatureFlagService(repo)

        updated = service.update(
            flag_name="update_me",
            enabled=True,
            description="Updated",
            user_context=make_admin_context(),
        )

        assert updated.enabled is True
        assert updated.description == "Updated"

    def test_update_partial_enabled_only(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("partial", False, "Keep this description")
        service = FeatureFlagService(repo)

        updated = service.update(
            flag_name="partial",
            enabled=True,
            description=None,
            user_context=make_admin_context(),
        )

        assert updated.enabled is True
        assert updated.description == "Keep this description"

    def test_update_not_found_raises(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        with pytest.raises(FeatureFlagNotFoundError):
            service.update("nonexistent", True, None, make_admin_context())

    def test_delete_flag(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("delete_me", True)
        service = FeatureFlagService(repo)

        service.delete("delete_me", make_admin_context())

        assert not repo.exists("delete_me")

    def test_delete_not_found_raises(self) -> None:
        repo = MockFeatureFlagRepository()
        service = FeatureFlagService(repo)

        with pytest.raises(FeatureFlagNotFoundError):
            service.delete("nonexistent", make_admin_context())

    def test_delete_requires_admin(self) -> None:
        repo = MockFeatureFlagRepository()
        repo.save("protected", True)
        service = FeatureFlagService(repo)

        with pytest.raises(PermissionDeniedError):
            service.delete("protected", make_customer_context())

        # Verify flag still exists
        assert repo.exists("protected")
