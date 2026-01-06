# Design

This document specifies the design for the e-commerce application, including data entities and backend APIs. For architectural patterns and principles, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Directory structure

This is the application-specific directory structure following the architecture patterns:

```
project-root/
├── backend/
│   ├── domain/                    # Core business logic (NO Django dependencies)
│   │   ├── events.py              # Base DomainEvent class
│   │   ├── event_dispatcher.py    # Abstract dispatcher interface
│   │   ├── aggregates/            # Organized by aggregate
│   │   │   ├── product/
│   │   │   │   ├── entity.py              # Product aggregate root
│   │   │   │   ├── events.py              # Product domain events
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   ├── cart/
│   │   │   │   ├── entities.py            # Cart (root) + CartItem
│   │   │   │   ├── events.py              # Cart domain events
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   └── order/
│   │   │       ├── entities.py            # Order (root) + OrderItem
│   │   │       ├── events.py              # Order domain events
│   │   │       └── repository.py          # Repository interface (ABC)
│   │   └── services/              # Domain services (cross-aggregate business logic)
│   ├── application/               # Application layer (use case orchestration)
│   │   ├── services/              # Application services
│   │   ├── queries/               # Query definitions (Simple Query Separation)
│   │   │   └── product_report.py  # Product report query + result types
│   │   └── ports/                 # Port interfaces
│   │       └── product_report_reader.py  # Reader interface
│   └── infrastructure/            # Framework-dependent code
│       ├── events/                # Event dispatcher infrastructure
│       │   ├── __init__.py        # Dispatcher setup
│       │   ├── dispatcher.py      # Sync/async event dispatcher
│       │   └── audit_handler.py   # Audit logging handler
│       └── django_app/            # Django project
│           ├── models.py          # ORM models (including AuditLog)
│           ├── views.py           # API views
│           ├── serializers.py     # DRF serializers
│           ├── repositories/      # Repository implementations (Django ORM)
│           │   ├── product_repository.py
│           │   ├── cart_repository.py
│           │   └── order_repository.py
│           ├── readers/           # Reader implementations (Simple Query Separation)
│           │   └── product_report_reader.py
│           └── unit_of_work.py    # Unit of Work with event dispatch
├── frontend/
│   └── src/
│       ├── components/            # Reusable UI components
│       ├── pages/                 # Page-level components
│       ├── services/              # API client functions
│       └── types/                 # TypeScript type definitions
```

## Backend APIs

### Product Endpoints
- **GET /api/products/** - List all products
  - Response: Array of Product objects (excludes soft-deleted by default)
  - Query params: `include_deleted=true` (admin only) - Include soft-deleted products
  - Ordering: Alphabetical by name
- **POST /api/products/** - Create a new product
  - Request body: `{ name, price, stock_quantity }`
  - Response: Created Product object
  - Error: 400 if validation fails or if product with same name already exists
- **DELETE /api/products/{id}/** - Soft-delete a product
  - Response: 204 No Content
  - Effect: Sets `deleted_at` timestamp, product hidden from catalog
  - Error: 400 if product is in any cart
  - Note: Products in orders can be soft-deleted (order history preserved via snapshot)
- **POST /api/products/{id}/restore/** - Restore a soft-deleted product (Admin only)
  - Response: Restored Product object
  - Error: 400 if product is not deleted, 404 if not found
- **GET /api/products/report/** - Get product report with cross-aggregate data (Admin only)
  - Response: Paginated array of report items with product details plus aggregated data
  - Each item includes: `product_id`, `name`, `price`, `stock_quantity`, `is_deleted`, `total_sold`, `currently_reserved`
  - Pagination: `page` (1-indexed, default 1), `page_size` (default 20, max 100)
  - Query params:
    - `include_deleted=true` - Include soft-deleted products
    - `search=<term>` - Filter by product name (case-insensitive)
    - `low_stock_threshold=<n>` - Only products with stock <= n
    - `has_sales=true|false` - Filter by whether product has been sold
    - `has_reservations=true|false` - Filter by whether product is in any cart
  - Response includes pagination metadata: `page`, `page_size`, `total_count`, `total_pages`, `has_next`, `has_previous`
  - Note: Uses Simple Query Separation pattern - bypasses domain layer for efficient cross-aggregate query

### Cart Endpoints
- **GET /api/cart/** - Get current cart
  - Response: Cart object with nested items (each item includes product details, quantity, subtotal), plus computed total
  - Note: Always returns the singleton cart (may have empty items array)
- **POST /api/cart/items/** - Add item to cart (cross-aggregate operation)
  - Request body: `{ product_id, quantity }`
  - Response: Updated Cart object
  - Side effects: Reserves stock (decrements product's stock_quantity)
  - Error: 400 if quantity exceeds available stock
  - Note: If product already in cart, increases quantity (and reserves additional stock)
- **PATCH /api/cart/items/{product_id}/** - Update item quantity (cross-aggregate operation)
  - Request body: `{ quantity }`
  - Response: Updated Cart object
  - Side effects: Adjusts stock reservation (increases or decreases product's stock_quantity)
  - Error: 400 if new quantity exceeds available stock
- **DELETE /api/cart/items/{product_id}/** - Remove item from cart (cross-aggregate operation)
  - Response: Updated Cart object
  - Side effects: Releases reserved stock (increments product's stock_quantity)
- **POST /api/cart/submit/** - Submit cart as order (cross-aggregate operation)
  - Response: Created Order object
  - Side effects: Creates Order with OrderItems, empties cart (deletes CartItems, cart itself remains)
  - Error: 400 if cart is empty
  - Note: Stock remains decremented (was reserved when added to cart)

### Order Endpoints
- **GET /api/orders/** - List all orders
  - Response: Array of Order objects with nested items and computed total
  - Ordering: Descending by submitted_at (newest first)
