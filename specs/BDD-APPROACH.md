# Behavior Driven Development (BDD) Approach

This document proposes a BDD approach for documenting use cases as executable specifications.

## Why BDD for This Project

BDD is well-suited for this reference project because:

1. **Ubiquitous language alignment** - Gherkin scenarios use the same domain terms defined in GLOSSARY.md
2. **Living documentation** - Feature files serve as both requirements and tests
3. **Use case focus** - Each scenario maps to a specific user action or business rule
4. **DDD synergy** - BDD's outside-in approach complements DDD's domain focus

## Recommended Tool: pytest-bdd

For a Python/Django project, `pytest-bdd` provides:
- Integration with existing pytest infrastructure
- Gherkin syntax (Given/When/Then)
- Reusable step definitions
- Fixtures for test setup
- Parametrized scenarios for edge cases

## Database Isolation and Test Independence

BDD tests use Django's test database infrastructure via pytest-django. Key points:

**Fresh Database Per Test Run:**
- Tests use SQLite (as configured in Django settings), but specifically a **test database** that pytest-django creates automatically
- The `db` fixture (from pytest-django) and `@pytest.mark.django_db` decorator enable database access
- Each test starts with a **clean, empty database** - Django's test framework handles this automatically

**No Pre-Existing State Required:**
- Tests do NOT depend on any pre-existing database state
- The `Background` steps in feature files create all necessary data fresh for each scenario
- For example, `Given a product "Laptop" exists...` creates the product via the application service

**How It Works:**
```gherkin
Background:
  Given I am logged in as a Customer
  And a product "Laptop" exists with price "$999.99" and stock quantity 10
```

This `Background` runs before each scenario, creating the product from scratch via step definitions:

```python
@given(parsers.parse('a product "{name}" exists with price "${price}" and stock quantity {qty:d}'))
def product_exists(context, product_service, admin_user_context, name, price, qty):
    product = product_service.create_product(
        user_context=admin_user_context,
        name=name,
        price=Decimal(price),
        stock_quantity=qty,
    )
    context["products"][name] = product
```

This ensures tests are:
- **Isolated** - No test affects another
- **Repeatable** - Same results every run
- **Self-contained** - No external setup scripts needed

## Directory Structure

```
backend/
├── features/                      # Gherkin feature files
│   ├── product/
│   │   ├── create_product.feature
│   │   ├── delete_product.feature
│   │   └── list_products.feature
│   ├── cart/
│   │   ├── add_to_cart.feature
│   │   ├── update_cart_item.feature
│   │   ├── remove_from_cart.feature
│   │   └── submit_cart.feature
│   └── order/
│       └── view_orders.feature
├── tests/
│   └── bdd/                       # Step definitions and conftest
│       ├── conftest.py            # Shared fixtures
│       ├── steps/
│       │   ├── common_steps.py    # Shared Given steps
│       │   ├── product_steps.py
│       │   ├── cart_steps.py
│       │   └── order_steps.py
│       └── test_features.py       # pytest-bdd test collection
```

## Example Feature Files

### Product: Create Product

```gherkin
# features/product/create_product.feature

Feature: Create Product
  As an Admin
  I want to create new products
  So that customers can purchase them

  Background:
    Given I am logged in as an Admin

  Scenario: Successfully create a product
    When I create a product with:
      | name        | price | stock_quantity |
      | Widget Pro  | 29.99 | 100            |
    Then the product "Widget Pro" should exist
    And the product "Widget Pro" should have stock quantity 100
    And a "ProductCreated" audit log entry should be recorded

  Scenario: Cannot create product with duplicate name
    Given a product "Widget Pro" exists
    When I create a product with name "Widget Pro"
    Then I should receive a "DuplicateProductError"

  Scenario: Cannot create product as Customer
    Given I am logged in as a Customer
    When I create a product with name "Widget Pro"
    Then I should receive a "PermissionDeniedError"

  Scenario Outline: Validation errors
    When I create a product with:
      | name   | price   | stock_quantity   |
      | <name> | <price> | <stock_quantity> |
    Then I should receive a validation error for "<field>"

    Examples:
      | name | price | stock_quantity | field          |
      |      | 29.99 | 100            | name           |
      | Widget | -5.00 | 100          | price          |
      | Widget | 29.99 | -10          | stock_quantity |
```

### Cart: Add to Cart

```gherkin
# features/cart/add_to_cart.feature

Feature: Add Item to Cart
  As a Customer
  I want to add products to my cart
  So that I can purchase them later

  Background:
    Given I am logged in as a Customer
    And a product "Laptop" exists with price $999.99 and stock quantity 10

  Scenario: Successfully add item to cart
    When I add 2 "Laptop" to my cart
    Then my cart should contain 2 "Laptop" at $999.99 each
    And the product "Laptop" should have stock quantity 8
    And a "StockReserved" event should be raised
    And a "CartItemAdded" event should be raised

  Scenario: Add same product twice merges quantities
    Given my cart contains 2 "Laptop"
    When I add 3 "Laptop" to my cart
    Then my cart should contain 5 "Laptop"
    And the product "Laptop" should have stock quantity 5

  Scenario: Cannot add more than available stock
    When I add 15 "Laptop" to my cart
    Then I should receive an "InsufficientStockError"
    And my cart should be empty
    And the product "Laptop" should have stock quantity 10

  Scenario: Cart item snapshots product price
    Given I add 1 "Laptop" to my cart
    When the product "Laptop" price changes to $1099.99
    Then my cart item should still show $999.99 per unit
```

### Cart: Submit Cart

```gherkin
# features/cart/submit_cart.feature

Feature: Submit Cart
  As a Customer
  I want to submit my cart
  So that I can complete my purchase

  Background:
    Given I am logged in as a Customer
    And a product "Headphones" exists with price $149.99 and stock quantity 20
    And my cart contains 2 "Headphones"

  Scenario: Successfully submit cart with verified address
    Given I have a valid shipping address:
      | street_line_1 | city     | state | postal_code | country |
      | 123 Main St   | Portland | OR    | 97201       | US      |
    When I submit my cart
    Then an Order should be created with:
      | item_count | total   |
      | 2          | $299.98 |
    And the Order should have a verified shipping address
    And my cart should be empty
    And a "CartSubmitted" event should be raised
    And an "OrderCreated" event should be raised

  Scenario: Cannot submit empty cart
    Given my cart is empty
    When I submit my cart
    Then I should receive an "EmptyCartError"

  Scenario: Cannot submit without verified address
    When I submit my cart without a shipping address
    Then I should receive an "AddressVerificationError"

  Scenario: Order preserves item snapshots after product deletion
    When I submit my cart
    And the product "Headphones" is soft-deleted
    Then my order should still show "Headphones" at $149.99
```

### Order: View Orders

```gherkin
# features/order/view_orders.feature

Feature: View Orders
  As a user
  I want to view order history
  So that I can see my past purchases

  Background:
    Given a Customer "alice" exists
    And a Customer "bob" exists
    And "alice" has submitted an order for "Widget" x 2
    And "bob" has submitted an order for "Gadget" x 1

  Scenario: Customer sees only their own orders
    Given I am logged in as Customer "alice"
    When I view my orders
    Then I should see 1 order
    And the order should contain "Widget" x 2

  Scenario: Admin sees all orders
    Given I am logged in as an Admin
    When I view all orders
    Then I should see 2 orders
    And I should see orders from both "alice" and "bob"
```

## How Step Matching Works

The `@given`, `@when`, and `@then` decorators are **functional, not just documentation**. They register each Python function with pytest-bdd's step matching system.

**At runtime, pytest-bdd:**

1. Reads the `.feature` file
2. For each step (e.g., `When I add 2 "Laptop" to my cart`), scans all imported step definitions for a matching decorator pattern
3. Extracts values using `parsers.parse()` placeholders (e.g., `{qty:d}` extracts `2`, `"{product_name}"` extracts `"Laptop"`)
4. Calls the decorated function with those extracted values plus any pytest fixtures

**If no matching decorator is found**, pytest-bdd raises:
```
StepDefNotFound: Step "When I add 2 'Laptop' to my cart" is not defined
```

**Analogy:** Think of it like Flask/FastAPI route decorators:
- `@app.route("/users/{id}")` connects a function to a URL pattern
- `@when(parsers.parse('I add {qty:d} "{name}" to my cart'))` connects a function to a Gherkin step pattern

Both are functional decorators that register the function in a framework's routing/matching system.

## Step Definition Examples

```python
# tests/bdd/steps/cart_steps.py

from pytest_bdd import given, when, then, parsers
from decimal import Decimal

@given(parsers.parse('a product "{name}" exists with price ${price:f} and stock quantity {qty:d}'))
def product_exists(product_service, name, price, qty, admin_context):
    product_service.create_product(
        name=name,
        price=Decimal(str(price)),
        stock_quantity=qty,
        user_context=admin_context
    )

@given(parsers.parse('my cart contains {qty:d} "{product_name}"'))
def cart_contains(cart_service, customer_context, qty, product_name):
    cart_service.add_item(
        product_name=product_name,
        quantity=qty,
        user_context=customer_context
    )

@when(parsers.parse('I add {qty:d} "{product_name}" to my cart'))
def add_to_cart(cart_service, customer_context, qty, product_name, context):
    try:
        cart_service.add_item(
            product_name=product_name,
            quantity=qty,
            user_context=customer_context
        )
        context['error'] = None
    except Exception as e:
        context['error'] = e

@then(parsers.parse('my cart should contain {qty:d} "{product_name}" at ${price:f} each'))
def cart_contains_item(cart_service, customer_context, qty, product_name, price):
    cart = cart_service.get_cart(customer_context)
    item = next(i for i in cart.items if i.product_name == product_name)
    assert item.quantity == qty
    assert item.unit_price == Decimal(str(price))

@then(parsers.parse('the product "{name}" should have stock quantity {qty:d}'))
def product_has_stock(product_service, name, qty):
    product = product_service.get_by_name(name)
    assert product.stock_quantity == qty

@then(parsers.parse('I should receive an "{error_type}"'))
def should_receive_error(context, error_type):
    assert context['error'] is not None
    assert type(context['error']).__name__ == error_type
```

## Shared Fixtures

```python
# tests/bdd/conftest.py

import pytest
from backend.application.services.product_service import ProductService
from backend.application.services.cart_service import CartService
from backend.domain.user_context import UserContext, Role

@pytest.fixture
def admin_context():
    return UserContext(
        user_id=uuid4(),
        username="admin",
        role=Role.ADMIN
    )

@pytest.fixture
def customer_context():
    return UserContext(
        user_id=uuid4(),
        username="customer",
        role=Role.CUSTOMER
    )

@pytest.fixture
def context():
    """Mutable context for passing data between steps."""
    return {}

@pytest.fixture
def product_service(unit_of_work):
    return ProductService(unit_of_work)

@pytest.fixture
def cart_service(unit_of_work, address_verification_port):
    return CartService(unit_of_work, address_verification_port)
```

## Test Execution

```bash
# Run all BDD tests
pytest tests/bdd/

# Run specific feature
pytest tests/bdd/ -k "add_to_cart"

# Generate test report
pytest tests/bdd/ --html=report.html
```

## Integration with Existing Tests

BDD tests complement (not replace) existing tests:

| Test Type | Purpose | Location |
|-----------|---------|----------|
| Unit tests | Test individual functions/methods in isolation | `tests/unit/` |
| BDD tests | Test use cases end-to-end through application services | `tests/bdd/` |
| Integration tests | Test infrastructure (repositories, adapters) | `tests/integration/` |

## Use Case Coverage

The feature files should cover these use cases:

### Product Use Cases
- [ ] List products (with pagination and filtering)
- [ ] Create product (admin only)
- [ ] Delete product (admin only, soft delete)
- [ ] Restore product (admin only)

### Cart Use Cases
- [ ] View cart
- [ ] Add item to cart (with stock reservation)
- [ ] Update item quantity (with stock adjustment)
- [ ] Remove item from cart (with stock release)
- [ ] Verify shipping address
- [ ] Submit cart (create order)

### Order Use Cases
- [ ] View own orders (customer)
- [ ] View all orders (admin)

## Benefits of This Approach

1. **Executable documentation** - Feature files describe system behavior in plain language
2. **Ubiquitous language enforcement** - Steps use terms from GLOSSARY.md
3. **Use case traceability** - Each scenario maps to a specific user story
4. **Regression safety** - Changes that break behavior fail the tests
5. **Onboarding aid** - New developers understand system behavior by reading features
6. **Stakeholder communication** - Non-technical stakeholders can read and validate scenarios
