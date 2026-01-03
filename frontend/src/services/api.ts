import type {
  AuthResponse,
  Cart,
  Order,
  OrderListResponse,
  Product,
  ProductFilters,
  ProductListResponse,
  SessionResponse,
} from '../types';

const API_BASE = 'http://localhost:8000/api';

// Store CSRF token for authenticated requests
let csrfToken: string | null = null;

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'An error occurred');
  }
  return response.json();
}

function getHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (csrfToken) {
    headers['X-CSRFToken'] = csrfToken;
  }
  return headers;
}

// Auth API

export async function getSession(): Promise<SessionResponse> {
  const response = await fetch(`${API_BASE}/auth/session/`, {
    credentials: 'include',
  });
  const data = await handleResponse<SessionResponse>(response);
  csrfToken = data.csrf_token;
  return data;
}

export async function login(
  username: string,
  password: string
): Promise<AuthResponse> {
  // Get CSRF token first if we don't have one
  if (!csrfToken) {
    await getSession();
  }

  const response = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: getHeaders(),
    credentials: 'include',
    body: JSON.stringify({ username, password }),
  });
  const data = await handleResponse<AuthResponse>(response);

  // After login, refresh CSRF token since a new session was created
  await getSession();

  return data;
}

export async function logout(): Promise<void> {
  const response = await fetch(`${API_BASE}/auth/logout/`, {
    method: 'POST',
    headers: getHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Logout failed');
  }
  csrfToken = null;
}

// Product API

export async function getProducts(
  filters?: ProductFilters
): Promise<ProductListResponse> {
  const params = new URLSearchParams();

  if (filters) {
    if (filters.page) params.set('page', filters.page.toString());
    if (filters.page_size) params.set('page_size', filters.page_size.toString());
    if (filters.search) params.set('search', filters.search);
    if (filters.min_price) params.set('min_price', filters.min_price);
    if (filters.max_price) params.set('max_price', filters.max_price);
    if (filters.in_stock !== undefined) params.set('in_stock', filters.in_stock.toString());
  }

  const queryString = params.toString();
  const url = queryString
    ? `${API_BASE}/products/?${queryString}`
    : `${API_BASE}/products/`;

  const response = await fetch(url, {
    credentials: 'include',
  });
  return handleResponse<ProductListResponse>(response);
}

export async function createProduct(
  name: string,
  price: string,
  stockQuantity: number
): Promise<Product> {
  const response = await fetch(`${API_BASE}/products/create/`, {
    method: 'POST',
    headers: getHeaders(),
    credentials: 'include',
    body: JSON.stringify({
      name,
      price,
      stock_quantity: stockQuantity,
    }),
  });
  return handleResponse<Product>(response);
}

export async function deleteProduct(productId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/products/${productId}/`, {
    method: 'DELETE',
    headers: getHeaders(),
    credentials: 'include',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete product');
  }
}

// Cart API

export async function getCart(): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/`, {
    credentials: 'include',
  });
  return handleResponse<Cart>(response);
}

export async function addToCart(
  productId: string,
  quantity: number
): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/items/`, {
    method: 'POST',
    headers: getHeaders(),
    credentials: 'include',
    body: JSON.stringify({
      product_id: productId,
      quantity,
    }),
  });
  return handleResponse<Cart>(response);
}

export async function updateCartItem(
  productId: string,
  quantity: number
): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/items/${productId}/`, {
    method: 'PATCH',
    headers: getHeaders(),
    credentials: 'include',
    body: JSON.stringify({ quantity }),
  });
  return handleResponse<Cart>(response);
}

export async function removeFromCart(productId: string): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/items/${productId}/remove/`, {
    method: 'DELETE',
    headers: getHeaders(),
    credentials: 'include',
  });
  return handleResponse<Cart>(response);
}

export async function submitCart(): Promise<Order> {
  const response = await fetch(`${API_BASE}/cart/submit/`, {
    method: 'POST',
    headers: getHeaders(),
    credentials: 'include',
  });
  return handleResponse<Order>(response);
}

// Order API

export async function getOrders(): Promise<Order[]> {
  const response = await fetch(`${API_BASE}/orders/`, {
    credentials: 'include',
  });
  const data = await handleResponse<OrderListResponse>(response);
  return data.results;
}
