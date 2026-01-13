"""Unit tests for UserGroupService with mock repository."""

from uuid import UUID, uuid4
from typing import Dict, FrozenSet, List, Optional, Set

import pytest

from application.ports.user_group_repository import UserGroupRepository
from application.services.user_group_service import (
    DuplicateUserGroupError,
    UserGroupNotFoundError,
    UserGroupService,
)
from domain.exceptions import PermissionDeniedError
from domain.user_context import Role, UserContext
from domain.user_groups import UserGroup


class MockUserGroupRepository(UserGroupRepository):
    """In-memory mock implementation for testing."""

    def __init__(self) -> None:
        self._groups: Dict[UUID, UserGroup] = {}
        self._names: Dict[str, UUID] = {}
        self._memberships: Dict[UUID, Set[UUID]] = {}  # group_id -> set of user_ids

    def get_all(self) -> List[UserGroup]:
        return list(self._groups.values())

    def get_by_id(self, group_id: UUID) -> Optional[UserGroup]:
        return self._groups.get(group_id)

    def get_by_name(self, name: str) -> Optional[UserGroup]:
        group_id = self._names.get(name)
        if group_id:
            return self._groups.get(group_id)
        return None

    def exists(self, name: str) -> bool:
        return name in self._names

    def save(self, name: str, description: str = "") -> UserGroup:
        existing_id = self._names.get(name)
        if existing_id:
            # Update existing
            group = UserGroup(id=existing_id, name=name, description=description)
            self._groups[existing_id] = group
            return group
        else:
            # Create new
            new_id = uuid4()
            group = UserGroup(id=new_id, name=name, description=description)
            self._groups[new_id] = group
            self._names[name] = new_id
            return group

    def delete(self, group_id: UUID) -> bool:
        if group_id in self._groups:
            group = self._groups[group_id]
            del self._groups[group_id]
            del self._names[group.name]
            self._memberships.pop(group_id, None)
            return True
        return False

    def get_groups_for_user(self, user_id: UUID) -> List[UserGroup]:
        groups = []
        for group_id, user_ids in self._memberships.items():
            if user_id in user_ids:
                group = self._groups.get(group_id)
                if group:
                    groups.append(group)
        return groups

    def get_group_ids_for_user(self, user_id: UUID) -> FrozenSet[UUID]:
        group_ids = set()
        for group_id, user_ids in self._memberships.items():
            if user_id in user_ids:
                group_ids.add(group_id)
        return frozenset(group_ids)

    def add_user_to_group(self, user_id: UUID, group_id: UUID) -> None:
        if group_id not in self._memberships:
            self._memberships[group_id] = set()
        self._memberships[group_id].add(user_id)

    def remove_user_from_group(self, user_id: UUID, group_id: UUID) -> None:
        if group_id in self._memberships:
            self._memberships[group_id].discard(user_id)

    def get_user_ids_in_group(self, group_id: UUID) -> List[UUID]:
        return list(self._memberships.get(group_id, set()))


def make_admin_context() -> UserContext:
    """Create an admin user context."""
    return UserContext(user_id=uuid4(), username="admin", role=Role.ADMIN)


def make_customer_context() -> UserContext:
    """Create a customer user context."""
    return UserContext(user_id=uuid4(), username="customer", role=Role.CUSTOMER)


class TestUserGroupServiceCRUD:
    """Unit tests for UserGroupService CRUD operations."""

    def test_get_all_returns_all_groups(self) -> None:
        repo = MockUserGroupRepository()
        repo.save("beta_testers", "Beta testing group")
        repo.save("internal_users", "Internal users")
        service = UserGroupService(repo)

        groups = service.get_all(make_admin_context())

        assert len(groups) == 2
        names = [g.name for g in groups]
        assert "beta_testers" in names
        assert "internal_users" in names

    def test_get_all_requires_admin(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(PermissionDeniedError):
            service.get_all(make_customer_context())

    def test_get_by_id_returns_group(self) -> None:
        repo = MockUserGroupRepository()
        created = repo.save("test_group", "A test group")
        service = UserGroupService(repo)

        group = service.get_by_id(created.id, make_admin_context())

        assert group.name == "test_group"
        assert group.description == "A test group"

    def test_get_by_id_not_found_raises(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(UserGroupNotFoundError):
            service.get_by_id(uuid4(), make_admin_context())

    def test_create_group(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        group = service.create(
            name="new_group",
            description="A new group",
            user_context=make_admin_context(),
        )

        assert group.name == "new_group"
        assert group.description == "A new group"
        assert repo.exists("new_group")

    def test_create_duplicate_raises(self) -> None:
        repo = MockUserGroupRepository()
        repo.save("existing", "Existing group")
        service = UserGroupService(repo)

        with pytest.raises(DuplicateUserGroupError) as exc_info:
            service.create("existing", "", make_admin_context())

        assert exc_info.value.name == "existing"

    def test_create_empty_name_raises(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(ValueError) as exc_info:
            service.create("", "", make_admin_context())

        assert "required" in str(exc_info.value).lower()

    def test_create_requires_admin(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(PermissionDeniedError):
            service.create("group", "", make_customer_context())

    def test_delete_group(self) -> None:
        repo = MockUserGroupRepository()
        created = repo.save("delete_me", "To be deleted")
        service = UserGroupService(repo)

        service.delete(created.id, make_admin_context())

        assert not repo.exists("delete_me")

    def test_delete_not_found_raises(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(UserGroupNotFoundError):
            service.delete(uuid4(), make_admin_context())

    def test_delete_requires_admin(self) -> None:
        repo = MockUserGroupRepository()
        created = repo.save("protected", "Protected group")
        service = UserGroupService(repo)

        with pytest.raises(PermissionDeniedError):
            service.delete(created.id, make_customer_context())

        assert repo.exists("protected")


class TestUserGroupServiceMembership:
    """Unit tests for UserGroupService membership operations."""

    def test_add_user_to_group(self) -> None:
        repo = MockUserGroupRepository()
        group = repo.save("test_group", "Test group")
        service = UserGroupService(repo)

        user_id = uuid4()
        service.add_user(group.id, user_id, make_admin_context())

        users = repo.get_user_ids_in_group(group.id)
        assert user_id in users

    def test_add_user_to_nonexistent_group_raises(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(UserGroupNotFoundError):
            service.add_user(uuid4(), uuid4(), make_admin_context())

    def test_add_user_requires_admin(self) -> None:
        repo = MockUserGroupRepository()
        group = repo.save("test_group", "Test group")
        service = UserGroupService(repo)

        with pytest.raises(PermissionDeniedError):
            service.add_user(group.id, uuid4(), make_customer_context())

    def test_remove_user_from_group(self) -> None:
        repo = MockUserGroupRepository()
        group = repo.save("test_group", "Test group")
        user_id = uuid4()
        repo.add_user_to_group(user_id, group.id)
        service = UserGroupService(repo)

        service.remove_user(group.id, user_id, make_admin_context())

        users = repo.get_user_ids_in_group(group.id)
        assert user_id not in users

    def test_remove_user_from_nonexistent_group_raises(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(UserGroupNotFoundError):
            service.remove_user(uuid4(), uuid4(), make_admin_context())

    def test_get_users_in_group(self) -> None:
        repo = MockUserGroupRepository()
        group = repo.save("test_group", "Test group")
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        repo.add_user_to_group(user_id_1, group.id)
        repo.add_user_to_group(user_id_2, group.id)
        service = UserGroupService(repo)

        users = service.get_users_in_group(group.id, make_admin_context())

        assert len(users) == 2
        assert user_id_1 in users
        assert user_id_2 in users

    def test_get_users_in_nonexistent_group_raises(self) -> None:
        repo = MockUserGroupRepository()
        service = UserGroupService(repo)

        with pytest.raises(UserGroupNotFoundError):
            service.get_users_in_group(uuid4(), make_admin_context())
