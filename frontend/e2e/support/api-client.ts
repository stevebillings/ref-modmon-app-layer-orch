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
}
