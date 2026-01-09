"""BDD tests for user management features."""

import pytest
from pytest_bdd import scenarios

# Import all step definitions
from tests.bdd.steps.common_steps import *  # noqa: F401, F403
from tests.bdd.steps.product_steps import *  # noqa: F401, F403
from tests.bdd.steps.user_group_steps import *  # noqa: F401, F403
from tests.bdd.steps.user_management_steps import *  # noqa: F401, F403

# Load all scenarios from user management feature file
scenarios("../../../features/admin/user_management.feature")


# Mark all tests in this module as requiring database access
pytestmark = pytest.mark.django_db
