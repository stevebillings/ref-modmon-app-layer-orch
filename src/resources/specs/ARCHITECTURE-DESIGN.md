# Architecture and design

This document specifies the architecture and design (primary data entities, backend APIs, etc.) for the project.

## Architecture

### Backend architecture

Architecture goals:
1. Separation of concerns
1. Fairly minimal dependence on the Django framework. We want to benefit from the way Django (like other modern framworks) makes it easy to receive a request and respond to it, but we don't want to over-rely on Django. In particular, we don't want to rely on Django capabilities that might not be provided by other frameworks (like Flask and FastAPI). We'll accomplish this by choosing to implement some things that Django might be able to do for us, and by using software patterns like the Repository Pattern.

The core business logic should have no dependencies on Django, and be clearly separate from the Django-dependent code (in its own directory).

The backend architecture should follow Domain Driven Design. We'll choose some simplifications noted below to reduce complexity.

The backend should use the Repository Pattern, and the Unit of Work Pattern, but rather than using events for eventual consistency across aggregates, the backend should achieve strong consistency across aggregate by using (a) a single database transaction per request that includes all database activity within that request, and (b) an application layer to orchistrate actions that span aggregates.

### Frontend architecture

Follow best practices for good separation of concerns in this type of application.

### Directory structure

```
project-root/
├── backend/
│   ├── domain/                    # Core business logic (NO Django dependencies)
│   │   ├── aggregates/            # Organized by aggregate
│   │   │   ├── product/
│   │   │   │   ├── entity.py              # Product aggregate root
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   ├── cart/
│   │   │   │   ├── entities.py            # Cart (root) + CartItem
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   └── order/
│   │   │       ├── entities.py            # Order (root) + OrderItem
│   │   │       └── repository.py          # Repository interface (ABC)
│   │   └── services/              # Domain services (cross-aggregate business logic)
│   ├── application/               # Application layer (use case orchestration)
│   │   └── services/              # Application services
│   └── infrastructure/            # Framework-dependent code
│       └── django_app/            # Django project
│           ├── models.py          # ORM models
│           ├── views.py           # API views
│           ├── serializers.py     # DRF serializers
│           ├── repositories/      # Repository implementations (Django ORM)
│           │   ├── product_repository.py
│           │   ├── cart_repository.py
│           │   └── order_repository.py
│           └── unit_of_work.py    # Unit of Work implementation
├── frontend/
│   └── src/
│       ├── components/            # Reusable UI components
│       ├── pages/                 # Page-level components
│       ├── services/              # API client functions
│       └── types/                 # TypeScript type definitions
```

**Key separation principles**:
- Code in `domain/` must never import from `infrastructure/` or Django
- The `infrastructure/` layer implements interfaces defined in `domain/`
- One repository per aggregate root (no separate repository for CartItem or OrderItem)

### Data flow pattern

The backend uses a simplified pattern for returning data from API endpoints, keeping the Django layer thin and the domain logic framework-agnostic.

#### Domain entities as frozen dataclasses

Domain entities are defined as frozen (immutable) dataclasses in the domain layer:

```python
@dataclass(frozen=True)
class Product:
    id: UUID
    name: str
    price: Decimal
    stock_quantity: int
    created_at: datetime

@dataclass(frozen=True)
class CartItem:
    id: UUID
    product: Product       # Nested dataclass
    quantity: int

@dataclass(frozen=True)
class Cart:
    id: UUID
    items: List[CartItem]  # Nested list of dataclasses
    created_at: datetime

@dataclass(frozen=True)
class Order:
    id: UUID
    items: List[OrderItem] # Nested list of dataclasses
    submitted_at: datetime
```

#### Recursive `to_dict()` conversion

A simple utility function recursively converts dataclasses to dictionaries at the infrastructure boundary:

```python
def to_dict(obj: Any) -> Any:
    if obj is None:
        return None
    if hasattr(obj, "__dataclass_fields__"):
        return {field.name: to_dict(getattr(obj, field.name)) for field in fields(obj)}
    if isinstance(obj, list):
        return [to_dict(item) for item in obj]
    if isinstance(obj, (UUID, date, datetime)):
        return str(obj)  # Convert to string for JSON serialization
    return obj
```

#### Thin Django views

Django views become simple pass-throughs:

```python
def list_products(request):
    products = application_service.get_all_products()
    return Response({"results": [to_dict(p) for p in products]})
```

#### Request → Response flow

```
HTTP Request
    │
    ▼
Django View (infrastructure/)
    │ Parse request, call application service
    ▼
Application Service (application/)
    │ Orchestrate use case, call repositories
    ▼
Repository Interface (domain/) ◄── implemented by ──► Repository Impl (infrastructure/)
    │                                                        │
    │                                                        ▼
    │                                                   Django ORM
    ▼
Domain Entity (frozen dataclass)
    │
    ▼
to_dict() conversion
    │
    ▼
Response(dict_data)
```

**Benefits of this approach**:
- Type safety in domain/application layers via dataclasses
- Framework-agnostic domain code (pure Python dataclasses)
- Single conversion point at the boundary
- Nested structures handled automatically
- Thin infrastructure layer with minimal Django-specific code

## Design

### Data entities

#### Product
- **id** (Primary Key, UUID)
- **name** (string) - Product name
- **price** (decimal) - Price in dollars, two decimal places
- **stock_quantity** (integer) - Available stock (not reserved in any cart)
- **created_at** (timestamp)
- **Uniqueness constraint**: Product name must be unique
- **Validation**:
  - name: 1–200 characters, non-empty
  - price: Greater than 0, max 2 decimal places
  - stock_quantity: 0 or greater
- **Immutability**: Products cannot be edited after creation; only stock_quantity changes via cart operations
- **Delete constraint**: Cannot delete if product is in any cart or referenced in any order

#### Cart
- **id** (Primary Key, UUID)
- **created_at** (timestamp)
- **Singleton**: Single cart for single-user application. One cart always exists; submitting an order clears its items but does not delete the cart.
- **Computed total**: Cart total is computed from items on read, not stored.

#### CartItem
- **id** (Primary Key, UUID)
- **cart_id** (Foreign Key to Cart)
- **product_id** (Foreign Key to Product)
- **quantity** (integer) - Quantity of this product in the cart
- **Validation**:
  - quantity: Must be positive (> 0)
  - quantity cannot exceed product's available stock_quantity
- **Uniqueness constraint**: Only one CartItem per product per cart (adding same product increases quantity)

#### Order
- **id** (Primary Key, UUID)
- **submitted_at** (timestamp) - When the order was submitted
- **Immutability**: Orders cannot be edited or deleted after creation.
- **Computed total**: Order total is computed from items on read, not stored.

#### OrderItem
- **id** (Primary Key, UUID)
- **order_id** (Foreign Key to Order)
- **product_id** (Foreign Key to Product)
- **product_name** (string) - Snapshot of product name at time of order
- **unit_price** (decimal) - Snapshot of product price at time of order
- **quantity** (integer) - Quantity ordered
- **Note**: Product name and price are copied at order time to preserve order history even if product is later deleted

### Backend APIs

#### Product Endpoints
- **GET /api/products/** - List all products
  - Response: Array of Product objects
  - Ordering: Alphabetical by name
- **POST /api/products/** - Create a new product
  - Request body: `{ name, price, stock_quantity }`
  - Response: Created Product object
  - Error: 400 if validation fails or if product with same name already exists
- **DELETE /api/products/{id}/** - Delete a product
  - Response: 204 No Content
  - Error: 400 if product is in any cart or referenced in any order

#### Cart Endpoints
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

#### Order Endpoints
- **GET /api/orders/** - List all orders
  - Response: Array of Order objects with nested items and computed total
  - Ordering: Descending by submitted_at (newest first)

## Future considerations

The following topics are intentionally deferred to keep the initial implementation simple. They may be worth revisiting as the application grows:

### Value objects

Wrapping primitive types in domain-specific value objects (e.g., `Money`, `Quantity`, `ProductName`) can provide:
- Type safety (compiler catches mixing up dollars vs. cents)
- Validation at construction time
- Domain-specific behavior (e.g., currency formatting methods)

Trade-off: Adds complexity and requires custom serialization in `to_dict()`.

### API specification-driven development

Generating backend API code from an OpenAPI/Swagger specification can provide:
- Single source of truth for API contracts
- Automatic client SDK generation
- API documentation
- Request/response validation

Trade-off: Requires additional tooling and build steps.

### Injectors / Dependency injection

Using injector classes or a DI framework to wire up dependencies (repositories, services, unit of work) can provide:
- Easier testing (swap implementations)
- Cleaner separation of object construction from use
- More explicit dependency graphs

Trade-off: Adds indirection and may be overkill for small applications.

### Django app structure: single app vs. one app per aggregate

The current implementation uses a single Django app (`infrastructure/django_app/`) containing all models, views, and repositories. An alternative approach is to create one Django app per aggregate (e.g., `infrastructure/product/`, `infrastructure/cart/`, and `infrastructure/order/`).

**Single app (current approach):**
- Simpler configuration (one entry in `INSTALLED_APPS`)
- The domain layer already enforces aggregate boundaries
- Fewer migration folders to manage
- Well-suited for small teams and rapid prototyping

**One app per aggregate:**
- Mirrors the domain structure in the infrastructure layer
- Each aggregate is independently deployable/extractable
- Better for large teams where different teams own different aggregates
- Clearer code ownership boundaries

Trade-off: The single app approach is simpler but makes it harder to extract an aggregate into a separate service later. One app per aggregate adds boilerplate (multiple `apps.py`, migrations folders) and cross-aggregate foreign keys require cross-app imports, but provides better modularity for larger codebases (10+ aggregates) or teams planning microservices extraction.
