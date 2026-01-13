"""Tests for UserService."""

from uuid import uuid4
from typing import Dict, List, Optional, Set

import pytest

from application.services.user_service import UserNotFoundError, UserService
from domain.exceptions import PermissionDeniedError
from domain.user_context import Role, UserContext
from domain.user_info import UserInfo


class FakeUserRepository:
    """Fake user repository for testing."""

    def __init__(self) -> None:
        self._users: Dict[str, UserInfo] = {}

    def add_user(self, user: UserInfo) -> None:
        self._users[str(user.id)] = user

    def get_all(self) -> List[UserInfo]:
        return list(self._users.values())

    def get_by_id(self, user_id) -> Optional[UserInfo]:
        return self._users.get(str(user_id))

    def update_role(self, user_id, role: Role) -> Optional[UserInfo]:
        user = self._users.get(str(user_id))
        if user is None:
            return None
        updated = UserInfo(
            id=user.id,
            username=user.username,
            email=user.email,
            role=role,
            group_ids=user.group_ids,
        )
        self._users[str(user_id)] = updated
        return updated


class FakeUserGroupRepository:
    """Fake user group repository for testing."""

    def __init__(self) -> None:
        self._memberships: Dict[str, Set[str]] = {}  # user_id -> set of group_ids

    def add_user_to_group(self, user_id, group_id) -> None:
        uid = str(user_id)
        if uid not in self._memberships:
            self._memberships[uid] = set()
        self._memberships[uid].add(str(group_id))

    def remove_user_from_group(self, user_id, group_id) -> None:
        uid = str(user_id)
        if uid in self._memberships:
            self._memberships[uid].discard(str(group_id))

    def get_groups_for_user(self, user_id) -> frozenset:
        uid = str(user_id)
        return frozenset(self._memberships.get(uid, set()))


@pytest.fixture
def admin_context():
    return UserContext(
        user_id=uuid4(),
        username="admin",
        role=Role.ADMIN,
    )


@pytest.fixture
def customer_context():
    return UserContext(
        user_id=uuid4(),
        username="customer",
        role=Role.CUSTOMER,
    )


@pytest.fixture
def user_repo():
    return FakeUserRepository()


@pytest.fixture
def group_repo():
    return FakeUserGroupRepository()


@pytest.fixture
def service(user_repo, group_repo):
    return UserService(user_repo, group_repo)


class TestUserServiceGetAll:
    def test_get_all_returns_all_users(self, service, user_repo, admin_context):
        user1 = UserInfo(
            id=uuid4(),
            username="user1",
            email="user1@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user2 = UserInfo(
            id=uuid4(),
            username="user2",
            email="user2@example.com",
            role=Role.ADMIN,
            group_ids=frozenset(),
        )
        user_repo.add_user(user1)
        user_repo.add_user(user2)

        result = service.get_all(admin_context)

        assert len(result) == 2
        usernames = {u.username for u in result}
        assert usernames == {"user1", "user2"}

    def test_get_all_requires_admin(self, service, customer_context):
        with pytest.raises(PermissionDeniedError):
            service.get_all(customer_context)


class TestUserServiceGetById:
    def test_get_by_id_returns_user(self, service, user_repo, admin_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)

        result = service.get_by_id(user.id, admin_context)

        assert result.username == "testuser"
        assert result.email == "test@example.com"

    def test_get_by_id_not_found_raises(self, service, admin_context):
        with pytest.raises(UserNotFoundError):
            service.get_by_id(uuid4(), admin_context)

    def test_get_by_id_requires_admin(self, service, user_repo, customer_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)

        with pytest.raises(PermissionDeniedError):
            service.get_by_id(user.id, customer_context)


class TestUserServiceUpdateRole:
    def test_update_role_changes_role(self, service, user_repo, admin_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)

        result = service.update_role(user.id, Role.ADMIN, admin_context)

        assert result.role == Role.ADMIN
        assert result.username == "testuser"

    def test_update_role_not_found_raises(self, service, admin_context):
        with pytest.raises(UserNotFoundError):
            service.update_role(uuid4(), Role.ADMIN, admin_context)

    def test_update_role_requires_admin(self, service, user_repo, customer_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)

        with pytest.raises(PermissionDeniedError):
            service.update_role(user.id, Role.ADMIN, customer_context)


class TestUserServiceGroupMembership:
    def test_add_to_group(self, service, user_repo, group_repo, admin_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)
        group_id = uuid4()

        service.add_to_group(user.id, group_id, admin_context)

        memberships = group_repo.get_groups_for_user(user.id)
        assert str(group_id) in memberships

    def test_add_to_group_user_not_found(self, service, admin_context):
        with pytest.raises(UserNotFoundError):
            service.add_to_group(uuid4(), uuid4(), admin_context)

    def test_add_to_group_requires_admin(self, service, user_repo, customer_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)

        with pytest.raises(PermissionDeniedError):
            service.add_to_group(user.id, uuid4(), customer_context)

    def test_remove_from_group(self, service, user_repo, group_repo, admin_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)
        group_id = uuid4()
        group_repo.add_user_to_group(user.id, group_id)

        service.remove_from_group(user.id, group_id, admin_context)

        memberships = group_repo.get_groups_for_user(user.id)
        assert str(group_id) not in memberships

    def test_remove_from_group_user_not_found(self, service, admin_context):
        with pytest.raises(UserNotFoundError):
            service.remove_from_group(uuid4(), uuid4(), admin_context)

    def test_remove_from_group_requires_admin(self, service, user_repo, customer_context):
        user = UserInfo(
            id=uuid4(),
            username="testuser",
            email="test@example.com",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        user_repo.add_user(user)

        with pytest.raises(PermissionDeniedError):
            service.remove_from_group(user.id, uuid4(), customer_context)
