"""BDD tests for user group features."""

import pytest
from pytest_bdd import scenarios

# Import all step definitions
from tests.bdd.steps.common_steps import *  # noqa: F401, F403
from tests.bdd.steps.product_steps import *  # noqa: F401, F403
from tests.bdd.steps.user_group_steps import *  # noqa: F401, F403

# Load all scenarios from user group feature files (shared location at repo root)
scenarios("../../../features/admin/user_groups.feature")


# Mark all tests in this module as requiring database access
pytestmark = pytest.mark.django_db
