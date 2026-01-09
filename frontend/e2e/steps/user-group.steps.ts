import { Given, When, Then, expect } from '../fixtures/test-fixtures';

// User Group Steps

Given(
  'a user group {string} exists with description {string}',
  async ({ apiClient, testContext, testSuffix }, name: string, description: string) => {
    await apiClient.loginAsAdmin();
    const uniqueName = `${name}${testSuffix}`;
    const group = await apiClient.createUserGroup(uniqueName, description);
    testContext.set(`userGroup:${name}`, { ...group, actualName: uniqueName });
    testContext.set(`userGroupId:${name}`, group.id);
    testContext.set(`userGroupName:${name}`, uniqueName);
  }
);

Given(
  'user {string} is a member of group {string}',
  async ({ apiClient, testContext }, username: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    // Get user ID - need to find the user first
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    const groupId = testContext.get(`userGroupId:${groupName}`) as string;
    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    await apiClient.addUserToGroup(groupId, user.id);
  }
);

When(
  'I create a user group {string} with description {string}',
  async ({ apiClient, testContext, testSuffix }, name: string, description: string) => {
    // Use API to create the user group (no admin UI exists for this)
    await apiClient.loginAsAdmin();
    const uniqueName = `${name}${testSuffix}`;
    const group = await apiClient.createUserGroup(uniqueName, description);
    testContext.set(`userGroup:${name}`, { ...group, actualName: uniqueName });
    testContext.set(`userGroupId:${name}`, group.id);
    testContext.set(`userGroupName:${name}`, uniqueName);
  }
);

When(
  'I delete the user group {string}',
  async ({ page, apiClient, testContext }, name: string) => {
    const groupId = testContext.get(`userGroupId:${name}`) as string;
    if (groupId) {
      await apiClient.loginAsAdmin();
      await apiClient.deleteUserGroup(groupId);
    }
  }
);

When(
  'I add user {string} to the group {string}',
  async ({ apiClient, testContext }, username: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    // Get user ID
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    const groupId = testContext.get(`userGroupId:${groupName}`) as string;
    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    await apiClient.addUserToGroup(groupId, user.id);
  }
);

When(
  'I remove user {string} from the group {string}',
  async ({ apiClient, testContext }, username: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    // Get user ID
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    const groupId = testContext.get(`userGroupId:${groupName}`) as string;
    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    await apiClient.removeUserFromGroup(groupId, user.id);
  }
);

Then(
  'the user group {string} should exist',
  async ({ apiClient, testContext }, name: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`userGroupName:${name}`) as string || name;
    const groups = await apiClient.getUserGroups();
    const exists = groups.results.some(g => g.name === actualName);
    expect(exists).toBe(true);
  }
);

Then(
  'the user group {string} should not exist',
  async ({ apiClient, testContext }, name: string) => {
    await apiClient.loginAsAdmin();
    const actualName = testContext.get(`userGroupName:${name}`) as string || name;
    const groups = await apiClient.getUserGroups();
    const exists = groups.results.some(g => g.name === actualName);
    expect(exists).toBe(false);
  }
);

Then(
  'the user group {string} should have description {string}',
  async ({ apiClient, testContext }, name: string, expectedDesc: string) => {
    await apiClient.loginAsAdmin();
    const groupId = testContext.get(`userGroupId:${name}`) as string;
    if (!groupId) {
      throw new Error(`Group "${name}" not found in context`);
    }
    const group = await apiClient.getUserGroup(groupId);
    expect(group.description).toBe(expectedDesc);
  }
);

Then(
  'user {string} should be a member of group {string}',
  async ({ apiClient, testContext }, username: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    // Get user ID
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    const groupId = testContext.get(`userGroupId:${groupName}`) as string;
    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    const groupUsers = await apiClient.getGroupUsers(groupId);
    expect(groupUsers.user_ids).toContain(user.id);
  }
);

Then(
  'user {string} should not be a member of group {string}',
  async ({ apiClient, testContext }, username: string, groupName: string) => {
    await apiClient.loginAsAdmin();

    // Get user ID
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    const groupId = testContext.get(`userGroupId:${groupName}`) as string;
    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    const groupUsers = await apiClient.getGroupUsers(groupId);
    expect(groupUsers.user_ids).not.toContain(user.id);
  }
);
