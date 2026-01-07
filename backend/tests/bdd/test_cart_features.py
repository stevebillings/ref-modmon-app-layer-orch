"""BDD tests for cart features."""

import pytest
from pytest_bdd import scenarios

# Import all step definitions
from tests.bdd.steps.common_steps import *  # noqa: F401, F403
from tests.bdd.steps.product_steps import *  # noqa: F401, F403
from tests.bdd.steps.cart_steps import *  # noqa: F401, F403

# Load all scenarios from cart feature files
scenarios("../../features/cart/add_to_cart.feature")
scenarios("../../features/cart/update_cart_item.feature")
scenarios("../../features/cart/remove_from_cart.feature")
scenarios("../../features/cart/submit_cart.feature")


# Mark all tests in this module as requiring database access
pytestmark = pytest.mark.django_db
