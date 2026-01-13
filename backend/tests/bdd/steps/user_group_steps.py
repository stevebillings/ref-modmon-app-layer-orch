"""User group-related step definitions."""

from typing import Any, Dict

from pytest_bdd import given, when, then, parsers

from application.services.user_group_service import UserGroupService
from domain.user_context import UserContext


# ============================================================================
# GIVEN steps
# ============================================================================


@given(parsers.parse('a user group "{name}" exists with description "{description}"'))
def user_group_exists(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    name: str,
    description: str,
) -> None:
    """Create a user group."""
    group = user_group_service.create(
        name=name,
        description=description,
        user_context=admin_user_context,
    )
    context["user_groups"][name] = group


@given(parsers.parse('user "{username}" is a member of group "{group_name}"'))
def user_is_member_of_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    username: str,
    group_name: str,
) -> None:
    """Add a user to a group."""
    user = context["named_users"].get(username)
    if user is None:
        raise ValueError(f"User '{username}' not found in context")

    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    user_group_service.add_user(
        group_id=group.id,
        target_user_id=user.user_id,
        user_context=admin_user_context,
    )


# ============================================================================
# WHEN steps
# ============================================================================


@when(parsers.parse('I create a user group "{name}" with description "{description}"'))
def create_user_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    name: str,
    description: str,
) -> None:
    """Create a user group (expected to succeed)."""
    group = user_group_service.create(
        name=name,
        description=description,
        user_context=context["current_user_context"],
    )
    context["user_groups"][name] = group


@when(parsers.parse('I try to create a user group "{name}" with description "{description}"'))
def try_create_user_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    name: str,
    description: str,
) -> None:
    """Try to create a user group (may fail)."""
    try:
        group = user_group_service.create(
            name=name,
            description=description,
            user_context=context["current_user_context"],
        )
        context["user_groups"][name] = group
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when('I try to create a user group "" with description "No name"')
def try_create_user_group_empty_name(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
) -> None:
    """Try to create a user group with empty name."""
    try:
        user_group_service.create(
            name="",
            description="No name",
            user_context=context["current_user_context"],
        )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I delete the user group "{name}"'))
def delete_user_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    name: str,
) -> None:
    """Delete a user group (expected to succeed)."""
    group = context["user_groups"].get(name)
    if group is None:
        raise ValueError(f"Group '{name}' not found in context")

    user_group_service.delete(
        group_id=group.id,
        user_context=context["current_user_context"],
    )
    del context["user_groups"][name]


@when(parsers.parse('I try to delete the user group "{name}"'))
def try_delete_user_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    name: str,
) -> None:
    """Try to delete a user group (may fail)."""
    try:
        group = context["user_groups"].get(name)
        if group is None:
            raise ValueError(f"Group '{name}' not found in context")

        user_group_service.delete(
            group_id=group.id,
            user_context=context["current_user_context"],
        )
        del context["user_groups"][name]
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I add user "{username}" to the group "{group_name}"'))
def add_user_to_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    username: str,
    group_name: str,
) -> None:
    """Add a user to a group (expected to succeed)."""
    user = context["named_users"].get(username)
    if user is None:
        raise ValueError(f"User '{username}' not found in context")

    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    user_group_service.add_user(
        group_id=group.id,
        target_user_id=user.user_id,
        user_context=context["current_user_context"],
    )


@when(parsers.parse('I try to add user "{username}" to the group "{group_name}"'))
def try_add_user_to_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    username: str,
    group_name: str,
) -> None:
    """Try to add a user to a group (may fail)."""
    try:
        user = context["named_users"].get(username)
        if user is None:
            raise ValueError(f"User '{username}' not found in context")

        group = context["user_groups"].get(group_name)
        if group is None:
            raise ValueError(f"Group '{group_name}' not found in context")

        user_group_service.add_user(
            group_id=group.id,
            target_user_id=user.user_id,
            user_context=context["current_user_context"],
        )
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I remove user "{username}" from the group "{group_name}"'))
def remove_user_from_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    username: str,
    group_name: str,
) -> None:
    """Remove a user from a group (expected to succeed)."""
    user = context["named_users"].get(username)
    if user is None:
        raise ValueError(f"User '{username}' not found in context")

    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    user_group_service.remove_user(
        group_id=group.id,
        target_user_id=user.user_id,
        user_context=context["current_user_context"],
    )


# ============================================================================
# THEN steps
# ============================================================================


@then(parsers.parse('the user group "{name}" should exist'))
def user_group_should_exist(
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a user group exists."""
    groups = user_group_service.get_all(admin_user_context)
    assert any(g.name == name for g in groups), f"User group '{name}' not found"


@then(parsers.parse('the user group "{name}" should not exist'))
def user_group_should_not_exist(
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a user group does not exist."""
    groups = user_group_service.get_all(admin_user_context)
    assert not any(g.name == name for g in groups), f"User group '{name}' should not exist"


@then(parsers.parse('the user group "{name}" should have description "{expected_desc}"'))
def user_group_should_have_description(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    name: str,
    expected_desc: str,
) -> None:
    """Verify a user group has the expected description."""
    groups = user_group_service.get_all(admin_user_context)
    group = next((g for g in groups if g.name == name), None)
    assert group is not None, f"User group '{name}' not found"
    assert group.description == expected_desc, (
        f"Expected description '{expected_desc}', got '{group.description}'"
    )


@then(parsers.parse('user "{username}" should be a member of group "{group_name}"'))
def user_should_be_member_of_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    username: str,
    group_name: str,
) -> None:
    """Verify a user is a member of a group."""
    user = context["named_users"].get(username)
    if user is None:
        raise ValueError(f"User '{username}' not found in context")

    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    members = user_group_service.get_users_in_group(group.id, admin_user_context)
    assert user.user_id in members, f"User '{username}' should be a member of '{group_name}'"


@then(parsers.parse('user "{username}" should not be a member of group "{group_name}"'))
def user_should_not_be_member_of_group(
    context: Dict[str, Any],
    user_group_service: UserGroupService,
    admin_user_context: UserContext,
    username: str,
    group_name: str,
) -> None:
    """Verify a user is not a member of a group."""
    user = context["named_users"].get(username)
    if user is None:
        raise ValueError(f"User '{username}' not found in context")

    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    members = user_group_service.get_users_in_group(group.id, admin_user_context)
    assert user.user_id not in members, f"User '{username}' should not be a member of '{group_name}'"
