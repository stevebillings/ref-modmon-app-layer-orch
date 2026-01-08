import { test as base, createBdd } from 'playwright-bdd';
import { request as playwrightRequest } from '@playwright/test';
import { ApiClient } from '../support/api-client';

type TestFixtures = {
  testContext: Map<string, unknown>;
  apiClient: ApiClient;
  testSuffix: string;
};

export const test = base.extend<TestFixtures>({
  testContext: async ({}, use) => {
    const context = new Map<string, unknown>();
    await use(context);
  },

  // Unique suffix per test to prevent data conflicts
  testSuffix: async ({}, use) => {
    const suffix = `-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
    await use(suffix);
  },

  apiClient: async ({}, use) => {
    // Create a dedicated API request context for the backend with proper base URL
    // This ensures cookies are properly stored and sent for the backend origin
    const apiContext = await playwrightRequest.newContext({
      baseURL: 'http://localhost:8000',
    });
    const client = new ApiClient(apiContext);
    await use(client);
    await apiContext.dispose();
  },
});

export const { Given, When, Then } = createBdd(test);
export { expect } from '@playwright/test';
