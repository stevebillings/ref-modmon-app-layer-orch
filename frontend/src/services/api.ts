import type {
  Cart,
  Order,
  OrderListResponse,
  Product,
  ProductListResponse,
} from '../types';

const API_BASE = 'http://localhost:8000/api';

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'An error occurred');
  }
  return response.json();
}

// Product API

export async function getProducts(): Promise<Product[]> {
  const response = await fetch(`${API_BASE}/products/`);
  const data = await handleResponse<ProductListResponse>(response);
  return data.results;
}

export async function createProduct(
  name: string,
  price: string,
  stockQuantity: number
): Promise<Product> {
  const response = await fetch(`${API_BASE}/products/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete product');
  }
}

// Cart API

export async function getCart(): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/`);
  return handleResponse<Cart>(response);
}

export async function addToCart(
  productId: string,
  quantity: number
): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/items/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
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
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantity }),
  });
  return handleResponse<Cart>(response);
}

export async function removeFromCart(productId: string): Promise<Cart> {
  const response = await fetch(`${API_BASE}/cart/items/${productId}/remove/`, {
    method: 'DELETE',
  });
  return handleResponse<Cart>(response);
}

export async function submitCart(): Promise<Order> {
  const response = await fetch(`${API_BASE}/cart/submit/`, {
    method: 'POST',
  });
  return handleResponse<Order>(response);
}

// Order API

export async function getOrders(): Promise<Order[]> {
  const response = await fetch(`${API_BASE}/orders/`);
  const data = await handleResponse<OrderListResponse>(response);
  return data.results;
}
