import { Given, When, Then, expect } from '../fixtures/test-fixtures';

// Helper to get actual product name from test context
function getActualName(testContext: Map<string, unknown>, name: string): string {
  return (testContext.get(`productName:${name}`) as string) || name;
}

Given('the product {string} has been deleted', async ({ apiClient, testContext }, name: string) => {
  const product = testContext.get(`product:${name}`) as { id: string } | undefined;
  if (product) {
    await apiClient.deleteProduct(product.id);
  }
});

When(
  'I create a product with name {string} price {string} and stock quantity {int}',
  async ({ page, testContext, testSuffix }, name: string, price: string, stockQuantity: number) => {
    await page.goto('/products');

    // Wait for page to be fully loaded (products table should be visible)
    await page.waitForSelector('[data-testid^="product-row"], [data-testid="empty-state"]', { timeout: 10000 });

    // Use unique product name to avoid conflicts between test runs
    const uniqueName = `${name}${testSuffix}`;
    testContext.set(`productName:${name}`, uniqueName);

    // Fill the product form using unique placeholders
    await page.getByPlaceholder('Enter product name').fill(uniqueName);
    await page.getByPlaceholder('0.00').fill(price.replace('$', ''));
    // Stock quantity input with placeholder "0" - use the one inside the Add New Product form
    await page.locator('input[placeholder="0"]').first().fill(String(stockQuantity));
    await page.getByRole('button', { name: /add product/i }).click();

    // Wait a bit for the product to be created
    await page.waitForTimeout(500);

    // Search for the newly created product to ensure it's visible (pagination might hide it)
    await page.getByPlaceholder('Search products...').fill(uniqueName);
    await page.waitForTimeout(500);

    // Wait for success - product appears in the list
    await expect(page.getByText(uniqueName)).toBeVisible({ timeout: 5000 });
  }
);

When('I delete the product {string}', async ({ page, testContext }, name: string) => {
  await page.goto('/products');

  const actualName = getActualName(testContext, name);

  // Search for the product to ensure it's visible (pagination might hide it)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  // Find and click delete button for the product
  const productRow = page.locator('[data-testid^="product-row"]', { hasText: actualName });
  await productRow.getByRole('button', { name: /delete/i }).click();

  // Confirm deletion in dialog
  await page.getByRole('button', { name: /confirm|yes|delete/i }).click();

  // Wait for product to be removed or marked as deleted
  await page.waitForTimeout(500);
});

When('I restore the product {string}', async ({ page, testContext }, name: string) => {
  await page.goto('/products');

  const actualName = getActualName(testContext, name);

  // Click "Show Deleted" button to show deleted products
  await page.getByRole('button', { name: /show deleted/i }).click();
  await page.waitForTimeout(500);

  // Search for the product to ensure it's visible (pagination might hide it)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  // Find and click restore button for the deleted product
  const productRow = page.locator('[data-testid^="product-row"]', { hasText: actualName });
  await productRow.getByRole('button', { name: /restore/i }).click();

  // Wait for restore to complete
  await page.waitForTimeout(500);
});

Then('the product {string} should exist', async ({ page, testContext }, name: string) => {
  await page.goto('/products');
  const actualName = getActualName(testContext, name);

  // Search for the product to ensure it's visible (pagination might hide it)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  await expect(page.getByText(actualName)).toBeVisible();
});

Then('the product {string} should have price {string}', async ({ page, testContext }, name: string, price: string) => {
  await page.goto('/products');
  const actualName = getActualName(testContext, name);

  // Search for the product to ensure it's visible (pagination might hide it)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  const productRow = page.locator('[data-testid^="product-row"]', { hasText: actualName });
  await expect(productRow.getByText(price)).toBeVisible();
});

Then(
  'the product {string} should have stock quantity {int}',
  async ({ page, testContext }, name: string, stockQuantity: number) => {
    await page.goto('/products');
    const actualName = getActualName(testContext, name);

    // Search for the product to ensure it's visible (pagination might hide it)
    await page.getByPlaceholder('Search products...').fill(actualName);
    await page.waitForTimeout(500);

    const productRow = page.locator('[data-testid^="product-row"]', { hasText: actualName });
    await expect(productRow.getByText(String(stockQuantity))).toBeVisible();
  }
);

Then('the product {string} should be marked as deleted', async ({ page, testContext }, name: string) => {
  await page.goto('/products');

  const actualName = getActualName(testContext, name);

  // Click "Show Deleted" button to show deleted products
  await page.getByRole('button', { name: /show deleted/i }).click();
  await page.waitForTimeout(500);

  // Search for the product to ensure it's visible (pagination might hide it)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  const productRow = page.locator('[data-testid^="product-row"]', { hasText: actualName });
  // Product should show deleted indicator
  await expect(productRow.getByText(/deleted/i)).toBeVisible();
});

Then('the product {string} should not appear in the product catalog', async ({ page, testContext }, name: string) => {
  await page.goto('/products');
  const actualName = getActualName(testContext, name);

  // Search for the product - it should not appear (unless Show Deleted is clicked)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  await expect(page.locator('[data-testid^="product-row"]', { hasText: actualName })).not.toBeVisible();
});

Then(
  'the product {string} should appear when including deleted products',
  async ({ page, testContext }, name: string) => {
    await page.goto('/products');

    const actualName = getActualName(testContext, name);

    // Click "Show Deleted" button to show deleted products
    await page.getByRole('button', { name: /show deleted/i }).click();
    await page.waitForTimeout(500);

    // Search for the product to ensure it's visible (pagination might hide it)
    await page.getByPlaceholder('Search products...').fill(actualName);
    await page.waitForTimeout(500);

    await expect(page.getByText(actualName)).toBeVisible();
  }
);

Then('the product {string} should appear in the product catalog', async ({ page, testContext }, name: string) => {
  await page.goto('/products');
  const actualName = getActualName(testContext, name);

  // Search for the product to ensure it's visible (pagination might hide it)
  await page.getByPlaceholder('Search products...').fill(actualName);
  await page.waitForTimeout(500);

  await expect(page.getByText(actualName)).toBeVisible();
});
