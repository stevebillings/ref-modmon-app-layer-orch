import { Given, expect } from '../fixtures/test-fixtures';

// Note: In playwright-bdd, step definitions match regardless of keyword (Given/When/Then)
// So we only need to define each step once

// Helper function to log in via the browser UI
async function loginViaUI(page: import('@playwright/test').Page, username: string, password: string) {
  await page.goto('/login');
  await page.getByPlaceholder('Enter username').fill(username);
  await page.getByPlaceholder('Enter password').fill(password);
  await page.getByRole('button', { name: /login/i }).click();
  // Wait for redirect to home page after successful login
  await page.waitForURL('/', { timeout: 10000 });
}

Given('I am logged in as an Admin', async ({ page }) => {
  await loginViaUI(page, 'admin', 'admin');
  // Verify we're logged in by checking for the username display (exact match)
  await expect(page.getByText('admin', { exact: true })).toBeVisible({ timeout: 5000 });
});

Given('I am logged in as a Customer', async ({ page }) => {
  await loginViaUI(page, 'customer', 'customer');
});

Given('I am logged in as customer {string}', async ({ page, testContext }, username: string) => {
  // For test users, password matches the username
  await loginViaUI(page, username, username);
  testContext.set('currentUser', username);
});

Given(
  'a product {string} exists with price {string} and stock quantity {int}',
  async ({ apiClient, testContext, testSuffix }, name: string, price: string, stockQuantity: number) => {
    // Ensure logged in as admin to create product
    await apiClient.loginAsAdmin();
    // Use unique product name to avoid conflicts between test runs
    const uniqueName = `${name}${testSuffix}`;
    const product = await apiClient.createProduct(uniqueName, price, stockQuantity);
    // Store mapping from logical name to actual product info
    testContext.set(`product:${name}`, { ...product, actualName: uniqueName });
    testContext.set(`productName:${name}`, uniqueName);
  }
);

Given('a customer {string} exists', async ({ testContext }, username: string) => {
  // In the frontend context, customers are created implicitly by the test user fixture
  // Just record the username for later use
  testContext.set(`customer:${username}`, { username });
});
