"""Tests for user-group-aware feature flags."""

import pytest
from uuid import uuid4

from domain.user_context import Role, UserContext


@pytest.mark.django_db
class TestFeatureFlagTargeting:
    """Integration tests for feature flag targeting with user groups."""

    def test_non_targeted_flag_enabled_for_all(self) -> None:
        """A flag with no target groups is enabled for everyone when enabled=True."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )

        repo = DjangoFeatureFlagRepository()
        repo.save("global_flag", enabled=True, description="Global flag")

        adapter = DjangoFeatureFlagAdapter()

        # Enabled without user context
        assert adapter.is_enabled("global_flag") is True

        # Enabled with any user context
        user_context = UserContext(user_id=uuid4(), username="user", role=Role.CUSTOMER)
        assert adapter.is_enabled("global_flag", user_context) is True

    def test_non_targeted_flag_disabled_for_all(self) -> None:
        """A flag with enabled=False is disabled for everyone (master kill switch)."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )

        repo = DjangoFeatureFlagRepository()
        repo.save("disabled_flag", enabled=False, description="Disabled flag")

        adapter = DjangoFeatureFlagAdapter()

        assert adapter.is_enabled("disabled_flag") is False
        user_context = UserContext(user_id=uuid4(), username="user", role=Role.CUSTOMER)
        assert adapter.is_enabled("disabled_flag", user_context) is False

    def test_targeted_flag_disabled_without_user_context(self) -> None:
        """A targeted flag returns False when no user context is provided."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("beta_testers", "Beta testing group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("beta_feature", enabled=True, description="Beta feature")
        flag_repo.add_target_group("beta_feature", group.id)

        adapter = DjangoFeatureFlagAdapter()

        # Without user context, targeted flag is disabled
        assert adapter.is_enabled("beta_feature") is False

    def test_targeted_flag_enabled_for_user_in_group(self) -> None:
        """A targeted flag is enabled for users in the target group."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("beta_testers", "Beta testing group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("beta_feature", enabled=True, description="Beta feature")
        flag_repo.add_target_group("beta_feature", group.id)

        adapter = DjangoFeatureFlagAdapter()

        # User in the target group
        user_context = UserContext(
            user_id=uuid4(),
            username="beta_user",
            role=Role.CUSTOMER,
            group_ids=frozenset([group.id]),
        )
        assert adapter.is_enabled("beta_feature", user_context) is True

    def test_targeted_flag_disabled_for_user_not_in_group(self) -> None:
        """A targeted flag is disabled for users not in any target group."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("beta_testers", "Beta testing group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("beta_feature", enabled=True, description="Beta feature")
        flag_repo.add_target_group("beta_feature", group.id)

        adapter = DjangoFeatureFlagAdapter()

        # User NOT in the target group
        user_context = UserContext(
            user_id=uuid4(),
            username="regular_user",
            role=Role.CUSTOMER,
            group_ids=frozenset(),  # No groups
        )
        assert adapter.is_enabled("beta_feature", user_context) is False

    def test_targeted_flag_enabled_for_any_group(self) -> None:
        """A flag with multiple targets is enabled if user is in ANY target group."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group1 = group_repo.save("beta_testers", "Beta testing group")
        group2 = group_repo.save("power_users", "Power users group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("new_feature", enabled=True, description="New feature")
        flag_repo.add_target_group("new_feature", group1.id)
        flag_repo.add_target_group("new_feature", group2.id)

        adapter = DjangoFeatureFlagAdapter()

        # User in first group only
        user_in_group1 = UserContext(
            user_id=uuid4(),
            username="user1",
            role=Role.CUSTOMER,
            group_ids=frozenset([group1.id]),
        )
        assert adapter.is_enabled("new_feature", user_in_group1) is True

        # User in second group only
        user_in_group2 = UserContext(
            user_id=uuid4(),
            username="user2",
            role=Role.CUSTOMER,
            group_ids=frozenset([group2.id]),
        )
        assert adapter.is_enabled("new_feature", user_in_group2) is True

        # User in neither group
        user_in_neither = UserContext(
            user_id=uuid4(),
            username="user3",
            role=Role.CUSTOMER,
            group_ids=frozenset([uuid4()]),  # Different group
        )
        assert adapter.is_enabled("new_feature", user_in_neither) is False

    def test_targeted_flag_master_kill_switch(self) -> None:
        """Even with targets, enabled=False disables for everyone."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("beta_testers", "Beta testing group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("beta_feature", enabled=False, description="Disabled")
        flag_repo.add_target_group("beta_feature", group.id)

        adapter = DjangoFeatureFlagAdapter()

        # User in target group but flag is disabled
        user_context = UserContext(
            user_id=uuid4(),
            username="beta_user",
            role=Role.CUSTOMER,
            group_ids=frozenset([group.id]),
        )
        assert adapter.is_enabled("beta_feature", user_context) is False

    def test_clear_targeting_enables_for_all(self) -> None:
        """Setting empty target groups makes flag global again."""
        from infrastructure.django_app.feature_flags import (
            DjangoFeatureFlagAdapter,
            DjangoFeatureFlagRepository,
        )
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("beta_testers", "Beta testing group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("beta_feature", enabled=True, description="Beta")
        flag_repo.add_target_group("beta_feature", group.id)

        adapter = DjangoFeatureFlagAdapter()

        # Initially disabled for user not in group
        user_context = UserContext(
            user_id=uuid4(),
            username="user",
            role=Role.CUSTOMER,
            group_ids=frozenset(),
        )
        assert adapter.is_enabled("beta_feature", user_context) is False

        # Clear targeting
        flag_repo.set_target_groups("beta_feature", set())

        # Now enabled for everyone
        assert adapter.is_enabled("beta_feature", user_context) is True


@pytest.mark.django_db
class TestFeatureFlagRepositoryTargeting:
    """Tests for FeatureFlagRepository targeting methods."""

    def test_set_target_groups(self) -> None:
        """Test setting target groups for a flag."""
        from infrastructure.django_app.feature_flags import DjangoFeatureFlagRepository
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group1 = group_repo.save("group1", "Group 1")
        group2 = group_repo.save("group2", "Group 2")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("test_flag", enabled=True)

        # Set targets
        flag = flag_repo.set_target_groups("test_flag", {group1.id, group2.id})

        assert len(flag.target_group_ids) == 2
        assert group1.id in flag.target_group_ids
        assert group2.id in flag.target_group_ids

    def test_add_target_group(self) -> None:
        """Test adding a target group to a flag."""
        from infrastructure.django_app.feature_flags import DjangoFeatureFlagRepository
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("test_group", "Test group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("test_flag", enabled=True)

        # Add target
        flag = flag_repo.add_target_group("test_flag", group.id)

        assert group.id in flag.target_group_ids

    def test_remove_target_group(self) -> None:
        """Test removing a target group from a flag."""
        from infrastructure.django_app.feature_flags import DjangoFeatureFlagRepository
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group1 = group_repo.save("group1", "Group 1")
        group2 = group_repo.save("group2", "Group 2")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("test_flag", enabled=True)
        flag_repo.set_target_groups("test_flag", {group1.id, group2.id})

        # Remove one target
        flag = flag_repo.remove_target_group("test_flag", group1.id)

        assert group1.id not in flag.target_group_ids
        assert group2.id in flag.target_group_ids

    def test_flag_includes_target_groups_in_get_all(self) -> None:
        """Test that get_all includes target_group_ids."""
        from infrastructure.django_app.feature_flags import DjangoFeatureFlagRepository
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("test_group", "Test group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("test_flag", enabled=True)
        flag_repo.add_target_group("test_flag", group.id)

        flags = flag_repo.get_all()
        flag = next(f for f in flags if f.name == "test_flag")

        assert group.id in flag.target_group_ids

    def test_flag_includes_target_groups_in_get_by_name(self) -> None:
        """Test that get_by_name includes target_group_ids."""
        from infrastructure.django_app.feature_flags import DjangoFeatureFlagRepository
        from infrastructure.django_app.repositories.user_group_repository import (
            DjangoUserGroupRepository,
        )

        group_repo = DjangoUserGroupRepository()
        group = group_repo.save("test_group", "Test group")

        flag_repo = DjangoFeatureFlagRepository()
        flag_repo.save("test_flag", enabled=True)
        flag_repo.add_target_group("test_flag", group.id)

        flag = flag_repo.get_by_name("test_flag")

        assert flag is not None
        assert group.id in flag.target_group_ids
