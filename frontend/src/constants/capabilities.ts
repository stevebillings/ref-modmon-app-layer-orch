/**
 * User capability constants.
 *
 * These match the capability values returned by the backend API.
 * Use these constants instead of string literals to avoid typos
 * and enable autocomplete.
 */
export const Capabilities = {
  // Product capabilities
  PRODUCTS_VIEW: 'products:view',
  PRODUCTS_CREATE: 'products:create',
  PRODUCTS_DELETE: 'products:delete',
  PRODUCTS_RESTORE: 'products:restore',
  PRODUCTS_VIEW_DELETED: 'products:view_deleted',
  PRODUCTS_REPORT: 'products:report',

  // Cart capabilities
  CART_VIEW: 'cart:view',
  CART_MODIFY: 'cart:modify',
  CART_SUBMIT: 'cart:submit',

  // Order capabilities
  ORDERS_VIEW_OWN: 'orders:view_own',
  ORDERS_VIEW_ALL: 'orders:view_all',

  // Feature flag capabilities
  FEATURE_FLAGS_MANAGE: 'feature_flags:manage',
} as const;

export type Capability = (typeof Capabilities)[keyof typeof Capabilities];
