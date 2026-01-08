# Behavior Driven Development (BDD) Approach

This document describes the BDD approach for documenting use cases as executable specifications, shared across both backend and frontend.

## Why BDD for This Project

BDD is well-suited for this reference project because:

1. **Ubiquitous language alignment** - Gherkin scenarios use the same domain terms defined in GLOSSARY.md
2. **Living documentation** - Feature files serve as both requirements and tests
3. **Use case focus** - Each scenario maps to a specific user action or business rule
4. **DDD synergy** - BDD's outside-in approach complements DDD's domain focus
5. **Cross-layer validation** - Same scenarios verify behavior in both backend and frontend

## Shared Feature Files

Feature files are stored at the repository root in `/features/` and shared between backend and frontend tests:

```
/features/
├── product/
│   ├── create_product.feature
│   └── delete_product.feature
├── cart/
│   ├── add_to_cart.feature
│   ├── update_cart_item.feature
│   ├── remove_from_cart.feature
│   └── submit_cart.feature
└── order/
    └── view_orders.feature
```

## Tag Convention

Tags control which layer(s) run each scenario:

| Tag | Meaning |
|-----|---------|
| `@backend @frontend` | Run on both layers - core behavior verifiable through UI |
| `@backend-only` | Internal verification (stock quantities, exception types, domain events) |
| `@frontend-only` | UI-specific behavior (loading states, animations, visual feedback) |

### Example

```gherkin
@backend @frontend
Scenario: Successfully add item to cart
  When I add 2 "Laptop" to my cart
  Then my cart should contain 2 "Laptop" at "$999.99" each

@backend-only
Scenario: Adding to cart reserves stock
  When I add 2 "Laptop" to my cart
  Then the product "Laptop" should have stock quantity 8
```

The first scenario tests UI-visible behavior (cart contents), while the second verifies internal state (stock reservation) that only the backend can directly observe.

## Backend: pytest-bdd

### Directory Structure

```
/backend/
├── tests/
│   └── bdd/
│       ├── conftest.py            # Fixtures and tag filtering
│       ├── steps/
│       │   ├── common_steps.py    # Login, product setup
│       │   ├── product_steps.py   # Product CRUD
│       │   ├── cart_steps.py      # Cart operations
│       │   └── order_steps.py     # Order viewing
│       ├── test_product_features.py
│       ├── test_cart_features.py
│       └── test_order_features.py
```

### Configuration

The test modules link feature files to step definitions:

```python
# backend/tests/bdd/test_cart_features.py
from pytest_bdd import scenarios
from tests.bdd.steps.common_steps import *
from tests.bdd.steps.cart_steps import *

scenarios("../../../features/cart/add_to_cart.feature")
scenarios("../../../features/cart/submit_cart.feature")

pytestmark = pytest.mark.django_db
```

### Tag Filtering

Backend tests skip `@frontend-only` scenarios via a pytest hook:

```python
# backend/tests/bdd/conftest.py
def pytest_bdd_apply_tag(tag: str, function: Any) -> Any:
    if tag == "frontend-only":
        return pytest.mark.skip(reason="Frontend-only scenario")
    return None
```

### Step Definition Pattern

Backend steps operate at the Application Service level:

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
```

### Running Backend Tests

```bash
cd backend

# Run all BDD tests
pytest tests/bdd/ -v

# Run specific feature
pytest tests/bdd/ -k "add_to_cart"

# Run only @backend-only scenarios
pytest tests/bdd/ -m "backend-only"
```

## Frontend: Playwright + playwright-bdd

### Directory Structure

```
/frontend/
├── e2e/
│   ├── fixtures/
│   │   └── test-fixtures.ts       # Custom Playwright fixtures
│   ├── support/
│   │   └── api-client.ts          # API client for test data setup
│   └── steps/
│       ├── common.steps.ts        # Login, product setup
│       ├── product.steps.ts       # Product CRUD
│       ├── cart.steps.ts          # Cart operations
│       └── order.steps.ts         # Order viewing
├── playwright.config.ts
└── .features-gen/                  # Auto-generated test files
```

### Configuration

```typescript
// frontend/playwright.config.ts
import { defineBddConfig, cucumberReporter } from 'playwright-bdd';

const testDir = defineBddConfig({
  featuresRoot: projectRoot,
  features: path.join(projectRoot, 'features/**/*.feature'),
  steps: ['e2e/steps/**/*.ts', 'e2e/fixtures/test-fixtures.ts'],
  tags: '@frontend and not @backend-only',
});

export default defineConfig({
  testDir,
  webServer: [
    {
      command: 'cd ../backend && python manage.py runserver 8000',
      url: 'http://localhost:8000/api/health/',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
    },
  ],
});
```

### Custom Fixtures

```typescript
// frontend/e2e/fixtures/test-fixtures.ts
import { test as base, createBdd } from 'playwright-bdd';
import { ApiClient } from '../support/api-client';

type TestFixtures = {
  testContext: Map<string, unknown>;
  apiClient: ApiClient;
};

export const test = base.extend<TestFixtures>({
  testContext: async ({}, use) => {
    await use(new Map());
  },
  apiClient: async ({ request }, use) => {
    await use(new ApiClient(request));
  },
});

export const { Given, When, Then } = createBdd(test);
```

### Step Definition Pattern

Frontend steps drive the browser to perform actions:

```typescript
// frontend/e2e/steps/cart.steps.ts
import { Given, When, Then, expect } from '../fixtures/test-fixtures';

When('I add {int} {string} to my cart', async ({ page }, quantity: number, productName: string) => {
  await page.goto('/products');

  const productRow = page.locator('[data-testid^="product-row"]', { hasText: productName });
  const quantityInput = productRow.locator('input[type="number"]');

  if (await quantityInput.isVisible()) {
    await quantityInput.fill(String(quantity));
  }

  await productRow.getByRole('button', { name: /add to cart/i }).click();
  await page.waitForTimeout(500);
});

Then('my cart should contain {int} {string} at {string} each',
  async ({ page }, quantity: number, productName: string, price: string) => {
    await page.goto('/cart');

    const cartItem = page.locator('[data-testid^="cart-item"]', { hasText: productName });
    await expect(cartItem).toBeVisible();
    await expect(cartItem.getByText(price)).toBeVisible();
    await expect(cartItem.getByText(String(quantity))).toBeVisible();
  }
);
```

### API Client for Test Data Setup

Frontend tests use an API client to set up data via the backend API:

```typescript
// frontend/e2e/support/api-client.ts
export class ApiClient {
  async loginAsAdmin(): Promise<void> {
    await this.getSession();
    await this.request.post(`${API_BASE}/auth/login/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { username: 'admin', password: 'admin' },
    });
  }

  async createProduct(name: string, price: string, stockQuantity: number) {
    const response = await this.request.post(`${API_BASE}/products/create/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { name, price: price.replace('$', ''), stock_quantity: stockQuantity },
    });
    return response.json();
  }
}
```

### Running Frontend E2E Tests

```bash
cd frontend

# Generate BDD test files from features
npx bddgen

# Run all E2E tests
npm run test:e2e

# Run with UI mode (for debugging)
npm run test:e2e:ui

# Run specific feature
npm run test:e2e -- --grep "Add Item to Cart"
```

## Data-TestId Attributes

Frontend components include `data-testid` attributes for reliable E2E selectors:

| Component | TestId Pattern |
|-----------|----------------|
| ProductList rows | `product-row-{id}` |
| CartView items | `cart-item-{id}` |
| OrderList items | `order-item-{id}` |
| ErrorAlert | `error-alert` |
| EmptyState | `empty-state` |

## GitHub Actions CI/CD

Example workflow for running both backend and frontend BDD tests:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-bdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest tests/bdd/ -v

  frontend-e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && python manage.py migrate
      - run: cd frontend && npm ci
      - run: cd frontend && npx playwright install --with-deps chromium
      - run: cd frontend && npm run test:e2e
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: frontend/playwright-report/
```

## Test Isolation Strategy

Frontend E2E tests use a **data isolation** approach rather than resetting the database between each scenario:

1. **Database resets once** before all tests via `global-setup.ts`
2. **Each test uses unique data** with a `testSuffix` (e.g., `Product-1767887829452-7fw3k`)
3. **Assertions filter by suffix** to only verify data from the current test
4. **Dedicated users** (e.g., `noorders`) handle scenarios requiring specific state

This approach is faster than per-scenario database resets and avoids container restart overhead.

## E2E Testing with Separate Repositories

When frontend and backend are in different Git repositories, additional coordination is needed for E2E tests. Here are the main approaches:

### Option 1: Docker Compose (Recommended)

Backend repo publishes a Docker image. Frontend repo uses docker-compose to spin up the backend:

```yaml
# frontend/.github/workflows/e2e.yml
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Start backend
        run: docker-compose -f docker-compose.test.yml up -d --wait
      - name: Install dependencies
        run: npm ci && npx playwright install --with-deps chromium
      - name: Run E2E tests
        run: npm run test:e2e
```

```yaml
# frontend/docker-compose.test.yml
services:
  backend:
    image: ghcr.io/your-org/backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///test.db
      - DJANGO_SETTINGS_MODULE=infrastructure.django_app.settings
    command: >
      sh -c "python manage.py migrate &&
             python manage.py reset_test_db &&
             python manage.py runserver 0.0.0.0:8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health/"]
      interval: 5s
      timeout: 5s
      retries: 5
```

**Pros**: Clean separation, backend team controls their image, simple frontend CI setup
**Cons**: Backend must publish Docker images, slight delay waiting for container

### Option 2: Checkout Both Repos

Clone both repositories in the CI workflow:

```yaml
# frontend/.github/workflows/e2e.yml
jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: your-org/backend
          path: backend
          token: ${{ secrets.BACKEND_REPO_TOKEN }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Start backend
        run: |
          cd backend
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py reset_test_db
          python manage.py runserver 8000 &
      - name: Run E2E tests
        run: npm run test:e2e
```

**Pros**: No Docker image publishing required, always uses latest backend code
**Cons**: Requires cross-repo access token, tighter coupling between repos

### Option 3: Deployed Test Environment

Point E2E tests at a staging/test backend deployment:

```yaml
- name: Run E2E tests
  run: npm run test:e2e
  env:
    API_BASE_URL: https://api-staging.yourapp.com
```

**Pros**: Simple setup, tests real deployment
**Cons**: Shared state between test runs, cannot easily reset database, network latency

### Option 4: Dedicated E2E Repository

A third repository orchestrates both services:

```
e2e-tests/
├── docker-compose.yml      # Pulls frontend + backend images
├── tests/
│   └── features/           # Shared feature files
├── playwright.config.ts
└── .github/workflows/
    └── e2e.yml
```

**Pros**: E2E tests are fully independent, clear ownership
**Cons**: Another repository to maintain, coordination overhead

### Enabling Per-Scenario Database Resets

If you need to reset the database between scenarios (rather than using data isolation), the backend should expose a test-only endpoint:

```python
# backend/infrastructure/django_app/views.py (only enabled in test/CI mode)
@api_view(['POST'])
def reset_test_database(request):
    if not settings.ENABLE_TEST_ENDPOINTS:
        return Response(status=404)
    call_command('reset_test_db')
    return Response({'status': 'reset complete'})
```

```typescript
// frontend/e2e/fixtures/test-fixtures.ts
test.beforeEach(async ({ request }) => {
  await request.post('http://localhost:8000/api/test/reset-db/');
});
```

### Recommendation

**Docker Compose** is the cleanest approach for separate repositories:
- Backend team maintains their image and test data seeding
- Frontend team has a stable, versioned contract to test against
- Database resets happen at container startup (fast)
- CI is self-contained with no external dependencies

## Same Scenario, Different Implementations

The same Gherkin scenario runs differently on each layer:

| Step | Backend | Frontend |
|------|---------|----------|
| `Given a product exists` | Calls `ProductService.create_product()` | Calls API via `apiClient.createProduct()` |
| `When I add 2 to cart` | Calls `CartService.add_item()` | Navigates to products page, fills form, clicks button |
| `Then cart should contain` | Queries `CartService.get_cart()` | Navigates to cart page, asserts visible text |

This provides comprehensive testing:
- **Backend tests** verify business logic in isolation (fast, focused)
- **Frontend tests** verify the full user flow through the browser (slower, end-to-end)

## Benefits of This Approach

| Benefit | Description |
|---------|-------------|
| Single source of truth | One set of feature files defines expected behavior |
| Stakeholder readable | Non-technical people can validate scenarios |
| Fast feedback | Backend tests run in seconds |
| Full coverage | Frontend tests verify the complete user experience |
| Regression safety | Changes that break behavior fail tests on both layers |
| Debugging support | Playwright traces show exactly what happened on failure |
