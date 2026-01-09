// Auth types
export interface User {
  id: string;
  username: string;
  role: 'admin' | 'customer';
  capabilities: string[];
  enabled_flags: string[];
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
  deleted_at: string | null;
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

// Shipping address types
export interface ShippingAddress {
  street_line_1: string;
  street_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country?: string;
}

export interface VerifiedShippingAddress extends ShippingAddress {
  verification_id: string;
}

export interface AddressVerificationResult {
  verified: boolean;
  status: 'verified' | 'corrected' | 'invalid' | 'undeliverable' | 'service_unavailable';
  standardized_address?: VerifiedShippingAddress;
  error_message?: string;
  field_errors?: Record<string, string>;
}

export interface Order {
  id: string;
  items: OrderItem[];
  submitted_at: string;
  total: string;
  shipping_address?: VerifiedShippingAddress;
}

export interface ApiError {
  error: string;
  field?: string;
}

export interface ProductListResponse {
  results: Product[];
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface ProductFilters {
  search?: string;
  min_price?: string;
  max_price?: string;
  in_stock?: boolean;
  include_deleted?: boolean;
  page?: number;
  page_size?: number;
}

export interface OrderListResponse {
  results: Order[];
}

// Feature Flag types
export interface FeatureFlag {
  name: string;
  enabled: boolean;
  description: string;
  created_at: string;
  updated_at: string;
  target_group_ids: string[];
}

export interface FeatureFlagListResponse {
  results: FeatureFlag[];
}

export interface CreateFeatureFlagRequest {
  name: string;
  enabled?: boolean;
  description?: string;
}

export interface UpdateFeatureFlagRequest {
  enabled?: boolean;
  description?: string;
}

// User Group types
export interface UserGroup {
  id: string;
  name: string;
  description: string;
}

export interface UserGroupListResponse {
  results: UserGroup[];
}

export interface CreateUserGroupRequest {
  name: string;
  description?: string;
}

export interface UserGroupUsersResponse {
  user_ids: string[];
}

// Product Report types
export interface ProductReportItem {
  product_id: string;
  name: string;
  price: string;
  stock_quantity: number;
  is_deleted: boolean;
  total_sold: number;
  currently_reserved: number;
}

export interface ProductReportFilters {
  page?: number;
  page_size?: number;
  search?: string;
  low_stock_threshold?: number;
  has_sales?: boolean;
  has_reservations?: boolean;
  include_deleted?: boolean;
}

export interface ProductReportResponse {
  results: ProductReportItem[];
  page: number;
  page_size: number;
  total_count: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}
