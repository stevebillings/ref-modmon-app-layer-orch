import { Given, When, Then, expect } from '../fixtures/test-fixtures';

// Feature Flag Targeting Steps

Given(
  'the flag {string} has target group {string}',
  async ({ apiClient, testContext }, flagName: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    const actualFlagName = testContext.get(`featureFlagName:${flagName}`) as string || flagName;
    const groupId = testContext.get(`userGroupId:${groupName}`) as string;

    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    await apiClient.addTargetGroupToFlag(actualFlagName, groupId);
  }
);

When(
  'I add target group {string} to flag {string}',
  async ({ apiClient, testContext }, groupName: string, flagName: string) => {
    await apiClient.loginAsAdmin();

    const actualFlagName = testContext.get(`featureFlagName:${flagName}`) as string || flagName;
    const groupId = testContext.get(`userGroupId:${groupName}`) as string;

    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    await apiClient.addTargetGroupToFlag(actualFlagName, groupId);
  }
);

When(
  'I remove target group {string} from flag {string}',
  async ({ apiClient, testContext }, groupName: string, flagName: string) => {
    await apiClient.loginAsAdmin();

    const actualFlagName = testContext.get(`featureFlagName:${flagName}`) as string || flagName;
    const groupId = testContext.get(`userGroupId:${groupName}`) as string;

    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    await apiClient.removeTargetGroupFromFlag(actualFlagName, groupId);
  }
);

When(
  'I set target groups {string} for flag {string}',
  async ({ apiClient, testContext }, groupNames: string, flagName: string) => {
    await apiClient.loginAsAdmin();

    const actualFlagName = testContext.get(`featureFlagName:${flagName}`) as string || flagName;

    // Parse comma-separated group names
    const names = groupNames.split(',').map(n => n.trim());
    const groupIds: string[] = [];

    for (const name of names) {
      const groupId = testContext.get(`userGroupId:${name}`) as string;
      if (!groupId) {
        throw new Error(`Group "${name}" not found in context`);
      }
      groupIds.push(groupId);
    }

    await apiClient.setFlagTargetGroups(actualFlagName, groupIds);
  }
);

Then(
  'the flag {string} should have target group {string}',
  async ({ apiClient, testContext }, flagName: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    const actualFlagName = testContext.get(`featureFlagName:${flagName}`) as string || flagName;
    const groupId = testContext.get(`userGroupId:${groupName}`) as string;

    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    const flag = await apiClient.getFeatureFlag(actualFlagName);
    expect(flag.target_group_ids).toContain(groupId);
  }
);

Then(
  'the flag {string} should not have target group {string}',
  async ({ apiClient, testContext }, flagName: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    const actualFlagName = testContext.get(`featureFlagName:${flagName}`) as string || flagName;
    const groupId = testContext.get(`userGroupId:${groupName}`) as string;

    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    const flag = await apiClient.getFeatureFlag(actualFlagName);
    expect(flag.target_group_ids).not.toContain(groupId);
  }
);
