"""BDD tests for order features."""

import pytest
from pytest_bdd import scenarios

# Import all step definitions
from tests.bdd.steps.common_steps import *  # noqa: F401, F403
from tests.bdd.steps.product_steps import *  # noqa: F401, F403
from tests.bdd.steps.cart_steps import *  # noqa: F401, F403
from tests.bdd.steps.order_steps import *  # noqa: F401, F403

# Load all scenarios from order feature files
scenarios("../../features/order/view_orders.feature")


# Mark all tests in this module as requiring database access
pytestmark = pytest.mark.django_db
