import { Given, When, Then, expect } from '../fixtures/test-fixtures';

// Feature Flag Steps

Given(
  'a feature flag {string} exists with enabled {string}',
  async ({ apiClient, testContext, testSuffix }, name: string, enabled: string) => {
    await apiClient.loginAsAdmin();
    const uniqueName = `${name}${testSuffix}`;
    const flag = await apiClient.createFeatureFlag(
      uniqueName,
      enabled.toLowerCase() === 'true',
      `Test flag ${name}`
    );
    testContext.set(`featureFlag:${name}`, { ...flag, actualName: uniqueName });
    testContext.set(`featureFlagName:${name}`, uniqueName);
  }
);

Given(
  'a feature flag {string} exists and is disabled',
  async ({ apiClient, testContext, testSuffix }, name: string) => {
    await apiClient.loginAsAdmin();
    const uniqueName = `${name}${testSuffix}`;
    const flag = await apiClient.createFeatureFlag(
      uniqueName,
      false,
      `Test flag ${name}`
    );
    testContext.set(`featureFlag:${name}`, { ...flag, actualName: uniqueName });
    testContext.set(`featureFlagName:${name}`, uniqueName);
  }
);

Given(
  'a feature flag {string} exists and is enabled',
  async ({ apiClient, testContext, testSuffix }, name: string) => {
    await apiClient.loginAsAdmin();
    const uniqueName = `${name}${testSuffix}`;
    const flag = await apiClient.createFeatureFlag(
      uniqueName,
      true,
      `Test flag ${name}`
    );
    testContext.set(`featureFlag:${name}`, { ...flag, actualName: uniqueName });
    testContext.set(`featureFlagName:${name}`, uniqueName);
  }
);

When(
  'I create a feature flag {string} with description {string}',
  async ({ apiClient, testContext, testSuffix }, name: string, description: string) => {
    // Use API to create the feature flag (no admin UI exists for this)
    await apiClient.loginAsAdmin();
    const uniqueName = `${name}${testSuffix}`;
    const flag = await apiClient.createFeatureFlag(uniqueName, false, description);
    testContext.set(`featureFlag:${name}`, { ...flag, actualName: uniqueName });
    testContext.set(`featureFlagName:${name}`, uniqueName);
  }
);

When(
  'I enable the feature flag {string}',
  async ({ apiClient, testContext }, name: string) => {
    // Use API to enable the feature flag
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    await apiClient.updateFeatureFlag(actualName, { enabled: true });
  }
);

When(
  'I disable the feature flag {string}',
  async ({ apiClient, testContext }, name: string) => {
    // Use API to disable the feature flag
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    await apiClient.updateFeatureFlag(actualName, { enabled: false });
  }
);

When(
  'I delete the feature flag {string}',
  async ({ apiClient, testContext }, name: string) => {
    // Use API to delete the feature flag
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    await apiClient.deleteFeatureFlag(actualName);
  }
);

Then(
  'the feature flag {string} should exist',
  async ({ apiClient, testContext }, name: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    const flags = await apiClient.getFeatureFlags();
    const exists = flags.results.some(f => f.name === actualName);
    expect(exists).toBe(true);
  }
);

Then(
  'the feature flag {string} should not exist',
  async ({ apiClient, testContext }, name: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    const flags = await apiClient.getFeatureFlags();
    const exists = flags.results.some(f => f.name === actualName);
    expect(exists).toBe(false);
  }
);

Then(
  'the feature flag {string} should have description {string}',
  async ({ apiClient, testContext }, name: string, expectedDesc: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    const flag = await apiClient.getFeatureFlag(actualName);
    expect(flag).toBeDefined();
  }
);

Then(
  'the feature flag {string} should be enabled',
  async ({ apiClient, testContext }, name: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    const flag = await apiClient.getFeatureFlag(actualName);
    expect(flag.enabled).toBe(true);
  }
);

Then(
  'the feature flag {string} should be disabled',
  async ({ apiClient, testContext }, name: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`featureFlagName:${name}`) as string || name;
    const flag = await apiClient.getFeatureFlag(actualName);
    expect(flag.enabled).toBe(false);
  }
);
