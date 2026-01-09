"""BDD tests for incident notification features."""

import pytest
from pytest_bdd import scenarios

# Import all step definitions
from tests.bdd.steps.common_steps import *  # noqa: F401, F403
from tests.bdd.steps.product_steps import *  # noqa: F401, F403
from tests.bdd.steps.user_group_steps import *  # noqa: F401, F403
from tests.bdd.steps.feature_flag_targeting_steps import *  # noqa: F401, F403
from tests.bdd.steps.incident_notification_steps import *  # noqa: F401, F403

# Load all scenarios from incident notification feature file
scenarios("../../../features/system/incident_notifications.feature")


# Mark all tests in this module as requiring database access
pytestmark = pytest.mark.django_db
