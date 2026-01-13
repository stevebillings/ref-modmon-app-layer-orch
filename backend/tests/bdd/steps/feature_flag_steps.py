"""Feature flag-related step definitions."""

from typing import Any, Dict

from pytest_bdd import given, when, then, parsers

from application.services.feature_flag_service import FeatureFlagService
from domain.user_context import UserContext


# ============================================================================
# GIVEN steps
# ============================================================================


@given(parsers.parse('a feature flag "{name}" exists and is disabled'))
def feature_flag_exists_disabled(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Create a disabled feature flag."""
    flag = feature_flag_service.create(
        name=name,
        enabled=False,
        description="",
        user_context=admin_user_context,
    )
    context["feature_flags"][name] = flag


@given(parsers.parse('a feature flag "{name}" exists and is enabled'))
def feature_flag_exists_enabled(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Create an enabled feature flag."""
    flag = feature_flag_service.create(
        name=name,
        enabled=True,
        description="",
        user_context=admin_user_context,
    )
    context["feature_flags"][name] = flag


# ============================================================================
# WHEN steps
# ============================================================================


@when(parsers.parse('I create a feature flag "{name}" with description "{description}"'))
def create_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
    description: str,
) -> None:
    """Create a feature flag (expected to succeed)."""
    flag = feature_flag_service.create(
        name=name,
        enabled=False,
        description=description,
        user_context=context["current_user_context"],
    )
    context["feature_flags"][name] = flag


@when(parsers.parse('I try to create a feature flag "{name}" with description "{description}"'))
def try_create_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
    description: str,
) -> None:
    """Try to create a feature flag (may fail)."""
    try:
        flag = feature_flag_service.create(
            name=name,
            enabled=False,
            description=description,
            user_context=context["current_user_context"],
        )
        context["feature_flags"][name] = flag
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I enable the feature flag "{name}"'))
def enable_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
) -> None:
    """Enable a feature flag (expected to succeed)."""
    flag = feature_flag_service.update(
        flag_name=name,
        enabled=True,
        description=None,
        user_context=context["current_user_context"],
    )
    context["feature_flags"][name] = flag


@when(parsers.parse('I try to enable the feature flag "{name}"'))
def try_enable_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
) -> None:
    """Try to enable a feature flag (may fail)."""
    try:
        flag = feature_flag_service.update(
            flag_name=name,
            enabled=True,
            description=None,
            user_context=context["current_user_context"],
        )
        context["feature_flags"][name] = flag
        context["error"] = None
    except Exception as e:
        context["error"] = e


@when(parsers.parse('I disable the feature flag "{name}"'))
def disable_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
) -> None:
    """Disable a feature flag (expected to succeed)."""
    flag = feature_flag_service.update(
        flag_name=name,
        enabled=False,
        description=None,
        user_context=context["current_user_context"],
    )
    context["feature_flags"][name] = flag


@when(parsers.parse('I delete the feature flag "{name}"'))
def delete_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
) -> None:
    """Delete a feature flag (expected to succeed)."""
    feature_flag_service.delete(
        flag_name=name,
        user_context=context["current_user_context"],
    )
    if name in context["feature_flags"]:
        del context["feature_flags"][name]


@when(parsers.parse('I try to delete the feature flag "{name}"'))
def try_delete_feature_flag(
    context: Dict[str, Any],
    feature_flag_service: FeatureFlagService,
    name: str,
) -> None:
    """Try to delete a feature flag (may fail)."""
    try:
        feature_flag_service.delete(
            flag_name=name,
            user_context=context["current_user_context"],
        )
        if name in context["feature_flags"]:
            del context["feature_flags"][name]
        context["error"] = None
    except Exception as e:
        context["error"] = e


# ============================================================================
# THEN steps
# ============================================================================


@then(parsers.parse('the feature flag "{name}" should exist'))
def feature_flag_should_exist(
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a feature flag exists."""
    flags = feature_flag_service.get_all(admin_user_context)
    assert any(f.name == name for f in flags), f"Feature flag '{name}' not found"


@then(parsers.parse('the feature flag "{name}" should not exist'))
def feature_flag_should_not_exist(
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a feature flag does not exist."""
    flags = feature_flag_service.get_all(admin_user_context)
    assert not any(f.name == name for f in flags), f"Feature flag '{name}' should not exist"


@then(parsers.parse('the feature flag "{name}" should be enabled'))
def feature_flag_should_be_enabled(
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a feature flag is enabled."""
    flag = feature_flag_service.get_by_name(name, admin_user_context)
    assert flag is not None, f"Feature flag '{name}' not found"
    assert flag.enabled, f"Feature flag '{name}' should be enabled"


@then(parsers.parse('the feature flag "{name}" should be disabled'))
def feature_flag_should_be_disabled(
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
) -> None:
    """Verify a feature flag is disabled."""
    flag = feature_flag_service.get_by_name(name, admin_user_context)
    assert flag is not None, f"Feature flag '{name}' not found"
    assert not flag.enabled, f"Feature flag '{name}' should be disabled"


@then(parsers.parse('the feature flag "{name}" should have description "{expected_desc}"'))
def feature_flag_should_have_description(
    feature_flag_service: FeatureFlagService,
    admin_user_context: UserContext,
    name: str,
    expected_desc: str,
) -> None:
    """Verify a feature flag has the expected description."""
    flag = feature_flag_service.get_by_name(name, admin_user_context)
    assert flag is not None, f"Feature flag '{name}' not found"
    assert flag.description == expected_desc, (
        f"Expected description '{expected_desc}', got '{flag.description}'"
    )
