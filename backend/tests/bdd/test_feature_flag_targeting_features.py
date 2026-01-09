"""BDD tests for feature flag targeting features."""

import pytest
from pytest_bdd import scenarios

# Import all step definitions
from tests.bdd.steps.common_steps import *  # noqa: F401, F403
from tests.bdd.steps.product_steps import *  # noqa: F401, F403
from tests.bdd.steps.user_group_steps import *  # noqa: F401, F403
from tests.bdd.steps.feature_flag_targeting_steps import *  # noqa: F401, F403

# Load all scenarios from feature flag targeting feature file
scenarios("../../../features/admin/feature_flag_targeting.feature")


# Mark all tests in this module as requiring database access
pytestmark = pytest.mark.django_db
