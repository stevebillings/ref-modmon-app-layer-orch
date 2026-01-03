// Auth types
export interface User {
  id: string;
  username: string;
  role: 'admin' | 'customer';
}

export interface AuthResponse {
  user: User;
}

export interface SessionResponse {
  authenticated: boolean;
  user?: User;
  csrf_token: string;
}

// Product types
export interface Product {
  id: string;
  name: string;
  price: string;
  stock_quantity: number;
  created_at: string;
}

export interface CartItem {
  id: string;
  product_id: string;
  product_name: string;
  unit_price: string;
  quantity: number;
  subtotal?: string;
}

export interface Cart {
  id: string;
  items: CartItem[];
  created_at: string;
  total: string;
  item_count: number;
}

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  product_name: string;
  unit_price: string;
  quantity: number;
  subtotal?: string;
}

export interface Order {
  id: string;
  items: OrderItem[];
  submitted_at: string;
  total: string;
}

export interface ApiError {
  error: string;
  field?: string;
}

export interface ProductListResponse {
  results: Product[];
}

export interface OrderListResponse {
  results: Order[];
}
