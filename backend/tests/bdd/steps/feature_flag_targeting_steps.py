"""Feature flag targeting step definitions."""

from typing import Any

from django.contrib.auth.models import User
from pytest_bdd import given, when, then, parsers

from application.ports.feature_flags import FeatureFlagPort
from application.services.feature_flag_service import FeatureFlagService
from application.services.user_group_service import UserGroupService
from domain.user_context import UserContext
from infrastructure.django_app.feature_flags import get_feature_flags
from infrastructure.django_app.user_context_adapter import build_user_context


# ============================================================================
# GIVEN steps
# ============================================================================


@given(parsers.parse('a feature flag "{name}" exists with enabled "{enabled}"'))
def feature_flag_exists_with_enabled(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
    enabled: str,
) -> None:
    """Create a feature flag with specified enabled status."""
    flag = feature_flag_service.create(
        name=name,
        enabled=enabled.lower() == "true",
        description=f"Test flag {name}",
        user_context=admin_user_context,
    )
    context["feature_flags"][name] = flag


@given(parsers.parse('the flag "{flag_name}" has target group "{group_name}"'))
def flag_has_target_group(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    flag_name: str,
    group_name: str,
) -> None:
    """Add a target group to a feature flag."""
    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    feature_flag_service.add_target_group(
        flag_name=flag_name,
        group_id=group.id,
        user_context=admin_user_context,
    )


# ============================================================================
# WHEN steps
# ============================================================================


@when(parsers.parse('I add target group "{group_name}" to flag "{flag_name}"'))
def add_target_group_to_flag(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    group_name: str,
    flag_name: str,
) -> None:
    """Add a target group to a feature flag (expected to succeed)."""
    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    feature_flag_service.add_target_group(
        flag_name=flag_name,
        group_id=group.id,
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I try to add target group "{group_name}" to flag "{flag_name}"'))
def try_add_target_group_to_flag(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    group_name: str,
    flag_name: str,
) -> None:
    """Try to add a target group to a feature flag (may fail)."""
    try:
        group = context["user_groups"].get(group_name)
        if group is None:
            raise ValueError(f"Group '{group_name}' not found in context")

        feature_flag_service.add_target_group(
            flag_name=flag_name,
            group_id=group.id,
            user_context=context["current_user_context"],
        )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I remove target group "{group_name}" from flag "{flag_name}"'))
def remove_target_group_from_flag(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    group_name: str,
    flag_name: str,
) -> None:
    """Remove a target group from a feature flag."""
    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    feature_flag_service.remove_target_group(
        flag_name=flag_name,
        group_id=group.id,
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I set target groups "{group_names}" for flag "{flag_name}"'))
def set_target_groups_for_flag(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    group_names: str,
    flag_name: str,
) -> None:
    """Set multiple target groups for a feature flag."""
    names = [name.strip() for name in group_names.split(",")]
    group_ids = []
    for name in names:
        group = context["user_groups"].get(name)
        if group is None:
            raise ValueError(f"Group '{name}' not found in context")
        group_ids.append(group.id)

    feature_flag_service.set_target_groups(
        flag_name=flag_name,
        group_ids=group_ids,
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I clear all target groups from flag "{flag_name}"'))
def clear_target_groups_from_flag(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    flag_name: str,
) -> None:
    """Clear all target groups from a feature flag."""
    feature_flag_service.set_target_groups(
        flag_name=flag_name,
        group_ids=[],
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I check if flag "{flag_name}" is enabled for user "{username}"'))
def check_flag_enabled_for_user(
    context: dict[str, Any],
    flag_name: str,
    username: str,
) -> None:
    """Check if a feature flag is enabled for a specific user."""
    # Get the Django user to build a full UserContext with group memberships
    django_user = User.objects.get(username=username)
    user_context = build_user_context(django_user)

    # Use the feature flag port to check if enabled
    feature_flags: FeatureFlagPort = get_feature_flags()
    context["flag_check_result"] = feature_flags.is_enabled(flag_name, user_context)


# ============================================================================
# THEN steps
# ============================================================================


@then(parsers.parse('the flag "{flag_name}" should have target group "{group_name}"'))
def flag_should_have_target_group(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    flag_name: str,
    group_name: str,
) -> None:
    """Verify a flag has a specific target group."""
    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    flag = feature_flag_service.get_by_name(flag_name, admin_user_context)
    assert group.id in flag.target_group_ids, (
        f"Flag '{flag_name}' should target group '{group_name}'"
    )


@then(parsers.parse('the flag "{flag_name}" should not have target group "{group_name}"'))
def flag_should_not_have_target_group(
    context: dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    flag_name: str,
    group_name: str,
) -> None:
    """Verify a flag does not have a specific target group."""
    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    flag = feature_flag_service.get_by_name(flag_name, admin_user_context)
    assert group.id not in flag.target_group_ids, (
        f"Flag '{flag_name}' should not target group '{group_name}'"
    )


@then(parsers.parse('the flag "{flag_name}" should have no target groups'))
def flag_should_have_no_target_groups(
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    flag_name: str,
) -> None:
    """Verify a flag has no target groups."""
    flag = feature_flag_service.get_by_name(flag_name, admin_user_context)
    assert len(flag.target_group_ids) == 0, (
        f"Flag '{flag_name}' should have no target groups"
    )


@then("the flag should be enabled")
def flag_should_be_enabled(context: dict[str, Any]) -> None:
    """Verify the flag check result is enabled."""
    assert context.get("flag_check_result") is True, "Flag should be enabled"


@then("the flag should be disabled")
def flag_should_be_disabled(context: dict[str, Any]) -> None:
    """Verify the flag check result is disabled."""
    assert context.get("flag_check_result") is False, "Flag should be disabled"
