import type { APIRequestContext } from '@playwright/test';

// Use relative paths since baseURL is set in the fixture
const API_BASE = '/api';

export class ApiClient {
  private csrfToken: string | null = null;

  constructor(private request: APIRequestContext) {}

  async getSession(): Promise<{ csrf_token: string; user: unknown }> {
    const response = await this.request.get(`${API_BASE}/auth/session/`);
    const data = await response.json();
    this.csrfToken = data.csrf_token;
    return data;
  }

  async loginAsAdmin(): Promise<void> {
    await this.getSession();
    const response = await this.request.post(`${API_BASE}/auth/login/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { username: 'admin', password: 'admin' },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to login as admin: ${response.status()} ${body}`);
    }
    await this.getSession(); // Refresh CSRF after login
  }

  async loginAsCustomer(username = 'customer'): Promise<void> {
    await this.getSession();
    await this.request.post(`${API_BASE}/auth/login/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { username, password: username },  // Password matches username for test users
    });
    await this.getSession();
  }

  async logout(): Promise<void> {
    await this.request.post(`${API_BASE}/auth/logout/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
    await this.getSession();
  }

  async createProduct(
    name: string,
    price: string,
    stockQuantity: number
  ): Promise<{ id: string; name: string }> {
    const response = await this.request.post(`${API_BASE}/products/create/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: {
        name,
        price: price.replace('$', ''),
        stock_quantity: stockQuantity,
      },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to create product "${name}": ${response.status()} ${body}`);
    }
    return response.json();
  }

  async deleteProduct(productId: string): Promise<void> {
    await this.request.delete(`${API_BASE}/products/${productId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
  }

  async restoreProduct(productId: string): Promise<void> {
    await this.request.post(`${API_BASE}/products/${productId}/restore/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
  }

  async addToCart(productId: string, quantity: number): Promise<void> {
    await this.request.post(`${API_BASE}/cart/items/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: {
        product_id: productId,
        quantity,
      },
    });
  }

  async updateCartItem(productId: string, quantity: number): Promise<void> {
    await this.request.patch(`${API_BASE}/cart/items/${productId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { quantity },
    });
  }

  async removeCartItem(productId: string): Promise<void> {
    await this.request.delete(`${API_BASE}/cart/items/${productId}/remove/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
  }

  async getCart(): Promise<{ items: Array<{ product_id: string }> }> {
    const response = await this.request.get(`${API_BASE}/cart/`);
    return response.json();
  }

  async clearCart(): Promise<void> {
    const cart = await this.getCart();
    for (const item of cart.items) {
      await this.removeCartItem(item.product_id);
    }
  }

  async submitCart(shippingAddress: {
    street_line_1: string;
    street_line_2?: string;
    city: string;
    state: string;
    postal_code: string;
    country: string;
  }): Promise<{ order_id: string }> {
    const response = await this.request.post(`${API_BASE}/cart/submit/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { shipping_address: shippingAddress },
    });
    return response.json();
  }

  async getOrders(): Promise<{ results: Array<{ id: string }> }> {
    const response = await this.request.get(`${API_BASE}/orders/`);
    return response.json();
  }

  // Feature Flag endpoints
  async createFeatureFlag(
    name: string,
    enabled: boolean,
    description: string
  ): Promise<{ name: string; enabled: boolean; description: string }> {
    const response = await this.request.post(`${API_BASE}/admin/feature-flags/create/`, {
      headers: {
        'X-CSRFToken': this.csrfToken!,
        'Content-Type': 'application/json',
      },
      data: JSON.stringify({ name, enabled, description }),
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to create feature flag "${name}": ${response.status()} ${body}`);
    }
    return response.json();
  }

  async getFeatureFlags(): Promise<{ results: Array<{ name: string; enabled: boolean; target_group_ids: string[] }> }> {
    const response = await this.request.get(`${API_BASE}/admin/feature-flags/`);
    return response.json();
  }

  async getFeatureFlag(flagName: string): Promise<{ name: string; enabled: boolean; target_group_ids: string[] }> {
    const response = await this.request.get(`${API_BASE}/admin/feature-flags/${flagName}/`);
    return response.json();
  }

  async updateFeatureFlag(
    flagName: string,
    data: { enabled?: boolean; description?: string }
  ): Promise<{ name: string; enabled: boolean }> {
    const response = await this.request.put(`${API_BASE}/admin/feature-flags/${flagName}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data,
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to update feature flag "${flagName}": ${response.status()} ${body}`);
    }
    return response.json();
  }

  async deleteFeatureFlag(flagName: string): Promise<void> {
    const response = await this.request.delete(`${API_BASE}/admin/feature-flags/${flagName}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to delete feature flag "${flagName}": ${response.status()} ${body}`);
    }
  }

  async addTargetGroupToFlag(flagName: string, groupId: string): Promise<void> {
    const response = await this.request.post(`${API_BASE}/admin/feature-flags/${flagName}/targets/add/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { group_id: groupId },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to add target group to flag "${flagName}": ${response.status()} ${body}`);
    }
  }

  async removeTargetGroupFromFlag(flagName: string, groupId: string): Promise<void> {
    const response = await this.request.delete(`${API_BASE}/admin/feature-flags/${flagName}/targets/${groupId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to remove target group from flag "${flagName}": ${response.status()} ${body}`);
    }
  }

  async setFlagTargetGroups(flagName: string, groupIds: string[]): Promise<void> {
    const response = await this.request.put(`${API_BASE}/admin/feature-flags/${flagName}/targets/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { group_ids: groupIds },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to set target groups for flag "${flagName}": ${response.status()} ${body}`);
    }
  }

  // User Group endpoints
  async createUserGroup(
    name: string,
    description: string
  ): Promise<{ id: string; name: string; description: string }> {
    const response = await this.request.post(`${API_BASE}/admin/user-groups/create/`, {
      headers: {
        'X-CSRFToken': this.csrfToken!,
        'Content-Type': 'application/json',
      },
      data: JSON.stringify({ name, description }),
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to create user group "${name}": ${response.status()} ${body}`);
    }
    return response.json();
  }

  async getUserGroups(): Promise<{ results: Array<{ id: string; name: string; description: string }> }> {
    const response = await this.request.get(`${API_BASE}/admin/user-groups/`);
    return response.json();
  }

  async getUserGroup(groupId: string): Promise<{ id: string; name: string; description: string }> {
    const response = await this.request.get(`${API_BASE}/admin/user-groups/${groupId}/`);
    return response.json();
  }

  async deleteUserGroup(groupId: string): Promise<void> {
    const response = await this.request.delete(`${API_BASE}/admin/user-groups/${groupId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to delete user group: ${response.status()} ${body}`);
    }
  }

  async addUserToGroup(groupId: string, userId: string): Promise<void> {
    const response = await this.request.post(`${API_BASE}/admin/user-groups/${groupId}/users/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { user_id: userId },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to add user to group: ${response.status()} ${body}`);
    }
  }

  async removeUserFromGroup(groupId: string, userId: string): Promise<void> {
    const response = await this.request.delete(`${API_BASE}/admin/user-groups/${groupId}/users/${userId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to remove user from group: ${response.status()} ${body}`);
    }
  }

  async getGroupUsers(groupId: string): Promise<{ user_ids: string[] }> {
    const response = await this.request.get(`${API_BASE}/admin/user-groups/${groupId}/users/`);
    return response.json();
  }

  // User Management endpoints
  async getUsers(): Promise<{ results: Array<{ id: string; username: string; role: string; group_ids: string[] }> }> {
    const response = await this.request.get(`${API_BASE}/admin/users/`);
    return response.json();
  }

  async getUser(userId: string): Promise<{ id: string; username: string; role: string; group_ids: string[] }> {
    const response = await this.request.get(`${API_BASE}/admin/users/${userId}/`);
    return response.json();
  }

  async updateUserRole(userId: string, role: string): Promise<{ id: string; username: string; role: string }> {
    const response = await this.request.put(`${API_BASE}/admin/users/${userId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { role },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to update user role: ${response.status()} ${body}`);
    }
    return response.json();
  }

  async addUserToGroupDirect(userId: string, groupId: string): Promise<void> {
    const response = await this.request.post(`${API_BASE}/admin/users/${userId}/groups/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
      data: { group_id: groupId },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to add user to group: ${response.status()} ${body}`);
    }
  }

  async removeUserFromGroupDirect(userId: string, groupId: string): Promise<void> {
    const response = await this.request.delete(`${API_BASE}/admin/users/${userId}/groups/${groupId}/`, {
      headers: { 'X-CSRFToken': this.csrfToken! },
    });
    if (!response.ok()) {
      const body = await response.text();
      throw new Error(`Failed to remove user from group: ${response.status()} ${body}`);
    }
  }
}
