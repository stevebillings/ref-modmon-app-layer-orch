import { Given, When, Then, expect } from '../fixtures/test-fixtures';

// User Management Steps

Given(
  'an admin {string} exists',
  async ({ testContext }, username: string) => {
    // Admin users are created during test setup
    // Just record the username for later use
    testContext.set(`admin:${username}`, { username, role: 'admin' });
  }
);

When(
  'I list all users',
  async ({ apiClient, testContext }) => {
    // Use API to list users (no admin UI exists for this)
    await apiClient.loginAsAdmin();
    const users = await apiClient.getUsers();
    testContext.set('userList', users.results);
  }
);

When(
  'I view user {string} details',
  async ({ apiClient, testContext }, username: string) => {
    // Use API to get user details (no admin UI exists for this)
    await apiClient.loginAsAdmin();

    // Get user ID
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    testContext.set('viewedUser', user);
  }
);

When(
  'I update user {string} role to {string}',
  async ({ apiClient, testContext }, username: string, role: string) => {
    await apiClient.loginAsAdmin();

    // Get user ID
    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    await apiClient.updateUserRole(user.id, role);
    testContext.set(`updatedUser:${username}`, { ...user, role });
  }
);

Then(
  'I should see user {string} in the list',
  async ({ testContext }, username: string) => {
    const userList = testContext.get('userList') as Array<{ username: string }> | undefined;
    if (!userList) {
      throw new Error('User list not found in context');
    }
    const found = userList.some(u => u.username === username);
    expect(found).toBe(true);
  }
);

Then(
  'I should see the user has role {string}',
  async ({ testContext }, expectedRole: string) => {
    const user = testContext.get('viewedUser') as { role: string } | undefined;
    if (!user) {
      throw new Error('No user was viewed');
    }
    expect(user.role).toBe(expectedRole);
  }
);

Then(
  'I should see the user has username {string}',
  async ({ testContext }, expectedUsername: string) => {
    const user = testContext.get('viewedUser') as { username: string } | undefined;
    if (!user) {
      throw new Error('No user was viewed');
    }
    expect(user.username).toBe(expectedUsername);
  }
);

Then(
  'I should see the user is in group {string}',
  async ({ testContext }, groupName: string) => {
    const user = testContext.get('viewedUser') as { group_ids: string[] } | undefined;
    if (!user) {
      throw new Error('No user was viewed');
    }

    const groupId = testContext.get(`userGroupId:${groupName}`) as string;
    if (!groupId) {
      throw new Error(`Group "${groupName}" not found in context`);
    }

    expect(user.group_ids).toContain(groupId);
  }
);

Then(
  'I should see the user has no groups',
  async ({ testContext }) => {
    const user = testContext.get('viewedUser') as { group_ids: string[] } | undefined;
    if (!user) {
      throw new Error('No user was viewed');
    }
    expect(user.group_ids.length).toBe(0);
  }
);

Then(
  'user {string} should have role {string}',
  async ({ apiClient }, username: string, expectedRole: string) => {
    await apiClient.loginAsAdmin();

    const users = await apiClient.getUsers();
    const user = users.results.find(u => u.username === username);
    if (!user) {
      throw new Error(`User "${username}" not found`);
    }

    expect(user.role).toBe(expectedRole);
  }
);
