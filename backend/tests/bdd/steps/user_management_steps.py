"""User management step definitions."""

from typing import Any, Dict
from uuid import uuid4

from django.contrib.auth.models import User
from pytest_bdd import given, when, then, parsers

from application.services.user_service import UserService
from domain.user_context import Role, UserContext
from infrastructure.django_app.models import UserProfile


def _create_database_user_with_role(username: str, role: str) -> UserContext:
    """Create a real Django user with profile and return UserContext."""
    try:
        django_user = User.objects.get(username=username)
        profile = django_user.profile
        # Update role if different
        if profile.role != role:
            profile.role = role
            profile.save()
    except User.DoesNotExist:
        # Create Django User - the post_save signal auto-creates UserProfile
        django_user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password="testpassword",
        )
        # Get the profile that was created by the signal
        profile = django_user.profile
        # Update role if needed
        if role != "customer":
            profile.role = role
            profile.save()
    # Return UserContext with the real profile ID
    return UserContext(
        user_id=profile.id,
        username=username,
        role=Role.ADMIN if role == "admin" else Role.CUSTOMER,
    )


# ============================================================================
# GIVEN steps
# ============================================================================


@given(parsers.parse('an admin "{username}" exists'))
def admin_exists(context: Dict[str, Any], username: str) -> None:
    """Ensure a named admin exists with a real database user profile."""
    if username not in context["named_users"]:
        context["named_users"][username] = _create_database_user_with_role(username, "admin")


# ============================================================================
# WHEN steps
# ============================================================================


@when("I list all users")
def list_all_users(
    context: Dict[str, Any],
    user_service: UserService,
) -> None:
    """List all users (expected to succeed)."""
    users = user_service.get_all(context["current_user_context"])
    context["user_list"] = users


@when("I try to list all users")
def try_list_all_users(
    context: Dict[str, Any],
    user_service: UserService,
) -> None:
    """Try to list all users (may fail)."""
    try:
        users = user_service.get_all(context["current_user_context"])
        context["user_list"] = users
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I view user "{username}" details'))
def view_user_details(
    context: Dict[str, Any],
    user_service: UserService,
    username: str,
) -> None:
    """View a user's details (expected to succeed)."""
    user_ctx = context["named_users"].get(username)
    if user_ctx is None:
        raise ValueError(f"User '{username}' not found in context")

    user_info = user_service.get_by_id(user_ctx.user_id, context["current_user_context"])
    context["viewed_user"] = user_info


@when(parsers.parse('I try to view user "{username}" details'))
def try_view_user_details(
    context: Dict[str, Any],
    user_service: UserService,
    username: str,
) -> None:
    """Try to view a user's details (may fail)."""
    try:
        user_ctx = context["named_users"].get(username)
        if user_ctx is None:
            raise ValueError(f"User '{username}' not found in context")

        user_info = user_service.get_by_id(user_ctx.user_id, context["current_user_context"])
        context["viewed_user"] = user_info
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when("I try to view nonexistent user details")
def try_view_nonexistent_user(
    context: Dict[str, Any],
    user_service: UserService,
) -> None:
    """Try to view a nonexistent user's details."""
    try:
        user_info = user_service.get_by_id(uuid4(), context["current_user_context"])
        context["viewed_user"] = user_info
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I update user "{username}" role to "{role}"'))
def update_user_role(
    context: Dict[str, Any],
    user_service: UserService,
    username: str,
    role: str,
) -> None:
    """Update a user's role (expected to succeed)."""
    user_ctx = context["named_users"].get(username)
    if user_ctx is None:
        raise ValueError(f"User '{username}' not found in context")

    new_role = Role.ADMIN if role == "admin" else Role.CUSTOMER
    user_info = user_service.update_role(
        user_ctx.user_id, new_role, context["current_user_context"]
    )
    context["updated_user"] = user_info


@when(parsers.parse('I try to update user "{username}" role to "{role}"'))
def try_update_user_role(
    context: Dict[str, Any],
    user_service: UserService,
    username: str,
    role: str,
) -> None:
    """Try to update a user's role (may fail)."""
    try:
        user_ctx = context["named_users"].get(username)
        if user_ctx is None:
            raise ValueError(f"User '{username}' not found in context")

        new_role = Role.ADMIN if role == "admin" else Role.CUSTOMER
        user_info = user_service.update_role(
            user_ctx.user_id, new_role, context["current_user_context"]
        )
        context["updated_user"] = user_info
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I try to update nonexistent user role to "{role}"'))
def try_update_nonexistent_user_role(
    context: Dict[str, Any],
    user_service: UserService,
    role: str,
) -> None:
    """Try to update a nonexistent user's role."""
    try:
        new_role = Role.ADMIN if role == "admin" else Role.CUSTOMER
        user_info = user_service.update_role(
            uuid4(), new_role, context["current_user_context"]
        )
        context["updated_user"] = user_info
        context["error"] = None
    except Exception as e:
        context["error"] = e


# ============================================================================
# THEN steps
# ============================================================================


@then(parsers.parse('I should see user "{username}" in the list'))
def user_should_be_in_list(
    context: Dict[str, Any],
    username: str,
) -> None:
    """Verify a user appears in the user list."""
    user_list = context.get("user_list", [])
    usernames = [u.username for u in user_list]
    assert username in usernames, f"User '{username}' not found in list: {usernames}"


@then(parsers.parse('I should see the user has role "{role}"'))
def user_should_have_role_in_view(
    context: Dict[str, Any],
    role: str,
) -> None:
    """Verify the viewed user has the expected role."""
    viewed_user = context.get("viewed_user")
    assert viewed_user is not None, "No user was viewed"
    expected_role = Role.ADMIN if role == "admin" else Role.CUSTOMER
    assert viewed_user.role == expected_role, (
        f"Expected role '{role}', got '{viewed_user.role.value}'"
    )


@then(parsers.parse('I should see the user has username "{username}"'))
def user_should_have_username(
    context: Dict[str, Any],
    username: str,
) -> None:
    """Verify the viewed user has the expected username."""
    viewed_user = context.get("viewed_user")
    assert viewed_user is not None, "No user was viewed"
    assert viewed_user.username == username, (
        f"Expected username '{username}', got '{viewed_user.username}'"
    )


@then(parsers.parse('I should see the user is in group "{group_name}"'))
def user_should_be_in_group(
    context: Dict[str, Any],
    group_name: str,
) -> None:
    """Verify the viewed user is in a specific group."""
    viewed_user = context.get("viewed_user")
    assert viewed_user is not None, "No user was viewed"

    group = context["user_groups"].get(group_name)
    if group is None:
        raise ValueError(f"Group '{group_name}' not found in context")

    assert group.id in viewed_user.group_ids, (
        f"User should be in group '{group_name}'"
    )


@then("I should see the user has no groups")
def user_should_have_no_groups(context: Dict[str, Any]) -> None:
    """Verify the viewed user has no group memberships."""
    viewed_user = context.get("viewed_user")
    assert viewed_user is not None, "No user was viewed"
    assert len(viewed_user.group_ids) == 0, (
        f"User should have no groups, but has {len(viewed_user.group_ids)}"
    )


@then(parsers.parse('user "{username}" should have role "{role}"'))
def user_should_have_role(
    context: Dict[str, Any],
    user_service: UserService,
    admin_user_context: UserContext,
    username: str,
    role: str,
) -> None:
    """Verify a user has the expected role."""
    user_ctx = context["named_users"].get(username)
    if user_ctx is None:
        raise ValueError(f"User '{username}' not found in context")

    user_info = user_service.get_by_id(user_ctx.user_id, admin_user_context)
    expected_role = Role.ADMIN if role == "admin" else Role.CUSTOMER
    assert user_info.role == expected_role, (
        f"Expected role '{role}', got '{user_info.role.value}'"
    )
