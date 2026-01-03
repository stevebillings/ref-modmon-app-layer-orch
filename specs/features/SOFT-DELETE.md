# Product Soft Delete

## Overview

Products support soft deletion, which hides them from the catalog while preserving database records and order history.

## Behavior

### Soft Delete
- Admin-only operation via `DELETE /api/products/{id}/`
- Sets `deleted_at` timestamp on the product
- Product no longer appears in product listings for customers
- Product cannot be added to carts
- Raises `ProductDeleted` domain event for audit logging

### Visibility After Deletion
- **Customers**: Cannot see soft-deleted products in any listing
- **Admins**: Can see soft-deleted products via `?include_deleted=true` query parameter
- **Orders**: Order history remains intact (uses snapshot pattern - product_name and unit_price are copied at order time)

### Constraints
- Cannot soft-delete products currently in any cart (reserved stock)
- CAN soft-delete products that have been ordered (order history preserved via snapshot)

### Restore
- Admin-only operation via `POST /api/products/{id}/restore/`
- Clears `deleted_at` timestamp
- Product reappears in catalog
- Raises `ProductRestored` domain event for audit logging

## Domain Events

- `ProductDeleted` - Raised when product is soft-deleted
- `ProductRestored` - Raised when product is restored

Both events include: `product_id`, `product_name`, `actor_id`

## API Changes

### GET /api/products/
- New query parameter: `include_deleted=true` (admin only)
- Response now includes `deleted_at` field (null for active products, ISO timestamp for deleted)

### DELETE /api/products/{id}/
- Now performs soft delete instead of hard delete
- Returns 204 on success
- Returns 400 if product is in a cart
- Returns 400 if product is already deleted

### POST /api/products/{id}/restore/
- New endpoint to restore soft-deleted products
- Admin only (returns 403 for non-admins)
- Returns 200 with restored product on success
- Returns 400 if product is not deleted
- Returns 404 if product doesn't exist

## Implementation Details

### Domain Layer
- `Product.deleted_at: datetime | None` - Nullable timestamp field
- `Product.is_deleted: bool` - Property returning `deleted_at is not None`
- `Product.soft_delete(actor_id)` - Sets deleted_at and raises ProductDeleted event
- `Product.restore(actor_id)` - Clears deleted_at and raises ProductRestored event

### Repository Layer
- All query methods accept `include_deleted: bool = False` parameter
- When `include_deleted=False`, filters by `deleted_at__isnull=True`

### Application Layer
- `ProductService.delete_product()` calls `product.soft_delete()` instead of hard delete
- `ProductService.restore_product()` restores soft-deleted products
- `ProductService.get_products_paginated()` accepts `include_deleted` and `user_context`

### Database
- `deleted_at` column added to `product` table
- Indexed for efficient filtering
