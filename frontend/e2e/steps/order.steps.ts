import { Given, When, Then, expect } from '../fixtures/test-fixtures';

// Helper to get actual product name from test context
function getActualName(testContext: Map<string, unknown>, name: string): string {
  return (testContext.get(`productName:${name}`) as string) || name;
}

// Helper function to log in via the browser UI
async function loginViaUI(page: import('@playwright/test').Page, username: string, password: string) {
  await page.goto('/login');
  await page.getByPlaceholder('Enter username').fill(username);
  await page.getByPlaceholder('Enter password').fill(password);
  await page.getByRole('button', { name: /login/i }).click();
  await page.waitForURL('/', { timeout: 10000 });
}

Given(
  'a customer {string} has submitted an order for {string} at {string} quantity {int}',
  async ({ apiClient, testContext, testSuffix }, username: string, productName: string, price: string, quantity: number) => {
    // Create product as admin with unique name
    await apiClient.loginAsAdmin();
    const uniqueName = `${productName}${testSuffix}`;
    const product = await apiClient.createProduct(uniqueName, price, 100);
    testContext.set(`product:${productName}`, { ...product, actualName: uniqueName });
    testContext.set(`productName:${productName}`, uniqueName);

    // Login as customer and create order
    await apiClient.loginAsCustomer(username);

    // Add to cart
    await apiClient.addToCart(product.id, quantity);

    // Submit cart with valid address
    await apiClient.submitCart({
      street_line_1: '123 Test St',
      city: 'Portland',
      state: 'OR',
      postal_code: '97201',
      country: 'US',
    });

    // Track that this customer has an order
    const customerOrders = (testContext.get(`orders:${username}`) as Array<unknown>) || [];
    customerOrders.push({ productName: uniqueName, quantity, price });
    testContext.set(`orders:${username}`, customerOrders);
  }
);

Given('I have no previous orders', async ({ page }) => {
  // Use a dedicated user who is never used by other tests
  // The "noorders" user is seeded by reset_test_db and only used here
  // First logout if already logged in, then login as noorders
  await page.goto('/');
  await page.getByRole('button', { name: 'Logout' }).click();
  // Wait for logout to complete, then navigate to login
  await page.waitForTimeout(500);
  await loginViaUI(page, 'noorders', 'noorders');
});

When('I view my orders', async ({ page }) => {
  await page.goto('/orders');
});

When('I view all orders', async ({ page }) => {
  await page.goto('/orders');
});

Then('I should see {int} order', async ({ page, testSuffix }, count: number) => {
  await page.goto('/orders');

  if (count === 0) {
    await expect(page.getByTestId('empty-state')).toBeVisible();
  } else {
    // Filter to only count orders containing products from this test run
    // Products created in this test have names ending with testSuffix
    const orderItems = page.locator('[data-testid^="order-item"]', { hasText: testSuffix });
    await expect(orderItems).toHaveCount(count);
  }
});

Then('I should see {int} orders', async ({ page, testSuffix }, count: number) => {
  await page.goto('/orders');

  if (count === 0) {
    await expect(page.getByTestId('empty-state')).toBeVisible();
  } else {
    // Filter to only count orders containing products from this test run
    // Products created in this test have names ending with testSuffix
    const orderItems = page.locator('[data-testid^="order-item"]', { hasText: testSuffix });
    await expect(orderItems).toHaveCount(count);
  }
});

Then(
  'the order should contain {string} quantity {int}',
  async ({ page, testContext }, productName: string, quantity: number) => {
    const actualName = getActualName(testContext, productName);
    // Find the order item containing this product
    const orderItem = page.locator('[data-testid^="order-item"]', { hasText: actualName });
    await expect(orderItem).toBeVisible();
    // Find the table row with the product name, then check the quantity cell
    const productRow = orderItem.locator('tr', { hasText: actualName });
    await expect(productRow).toBeVisible();
    // The quantity is in the 3rd column (Quantity column)
    await expect(productRow.locator('td').nth(2)).toHaveText(String(quantity));
  }
);

Then('the order should contain {string} at {string} each', async ({ page, testContext }, productName: string, price: string) => {
  const actualName = getActualName(testContext, productName);
  const orderItem = page.locator('[data-testid^="order-item"]', { hasText: actualName });
  await expect(orderItem).toBeVisible();
  await expect(orderItem.getByText(price)).toBeVisible();
});
