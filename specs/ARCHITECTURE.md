# Architecture

This document specifies the architecture for the project. It is application-agnostic and contains no references to specific domain entities or endpoints.

## Backend architecture

### Description and patterns

Architecture goals:
1. Separation of concerns
1. Fairly minimal dependence on the Django framework. We want to benefit from the way Django (like other modern framworks) makes it easy to receive a request and respond to it, but we don't want to over-rely on Django. In particular, we don't want to rely on Django capabilities that might not be provided by other frameworks (like Flask and FastAPI). We'll accomplish this by choosing to implement some things that Django might be able to do for us, and by using software patterns like the Repository Pattern.

The core business logic should have no dependencies on Django, and be clearly separate from the Django-dependent code (in its own directory).

The backend architecture should follow Domain Driven Design. We'll choose some simplifications noted below to reduce complexity.

The backend should be a modular monolith that uses an application layer to achieve strong consistency by orchestrating operations that make changes across multiple aggregates (as opposed to using events for eventual consistency). It should use the Repository Pattern and the Unit of Work Pattern to keep the core business logic free of dependencies on low level concerns like the database. It should use a single database transaction per request that includes all database activity within that request (which may span multiple aggregates).

### Division of responsibilities

| Operation | Application Service | Aggregate | Repository |
|-----------|---------------------|-----------|------------|
| Create | Orchestrates creation, coordinates cross-aggregate side effects | Validates data, enforces business rules | Persists new entity |
| Read | Coordinates retrieval, may enrich with data from other aggregates | N/A (data returned directly) | Loads entity from storage |
| Update | Orchestrates update, handles cross-aggregate consistency | Validates changes, enforces invariants | Persists updated entity |
| Delete | Validates deletion is allowed, handles cross-aggregate constraints | N/A (or validates own deletion rules) | Removes entity from storage |

## Frontend architecture

Follow best practices for good separation of concerns in this type of application.

## Directory structure

```
project-root/
├── backend/
│   ├── domain/                    # Core business logic (NO Django dependencies)
│   │   ├── validation.py          # Shared validation functions
│   │   ├── exceptions.py          # Domain exceptions
│   │   ├── events.py              # Base DomainEvent class
│   │   ├── event_dispatcher.py    # Abstract dispatcher interface
│   │   ├── aggregates/            # Organized by aggregate
│   │   │   ├── <aggregate_a>/
│   │   │   │   ├── entity.py              # Aggregate root (mutable, with behavior)
│   │   │   │   ├── events.py              # Domain events for this aggregate
│   │   │   │   ├── validation.py          # Aggregate-specific validations
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   └── <aggregate_b>/
│   │   │       ├── entities.py            # Aggregate root + child value objects
│   │   │       ├── events.py              # Domain events for this aggregate
│   │   │       └── repository.py          # Repository interface (ABC)
│   │   └── services/              # Domain services (cross-aggregate business logic)
│   ├── application/               # Application layer (use case orchestration)
│   │   └── services/              # Application services (thin orchestration)
│   └── infrastructure/            # Framework-dependent code
│       ├── events/                # Event dispatcher infrastructure
│       │   ├── __init__.py        # Dispatcher setup and configuration
│       │   ├── dispatcher.py      # Sync/async event dispatcher
│       │   └── audit_handler.py   # Audit logging handler
│       └── django_app/            # Django project
│           ├── models.py          # ORM models (including AuditLog)
│           ├── views.py           # API views
│           ├── serializers.py     # DRF serializers
│           ├── repositories/      # Repository implementations (Django ORM)
│           └── unit_of_work.py    # Unit of Work with event dispatch
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
- One repository per aggregate root (no separate repository for child entities within an aggregate)
- **Aggregate isolation**: An aggregate must never import or embed entities from another aggregate. References to other aggregates must be by ID only. Any data needed from another aggregate should be passed in as snapshots (copied values) by the application layer at the time of the operation. This keeps aggregates independently evolvable and testable.

## Data flow pattern

The backend uses a simplified pattern for returning data from API endpoints, keeping the Django layer thin and the domain logic framework-agnostic.

### True DDD aggregates with encapsulated behavior

Domain aggregates are **not anemic data containers**. They are mutable classes with behavior methods that enforce invariants and encapsulate business logic. This follows the core DDD principle that aggregates are consistency boundaries responsible for maintaining their own validity.

**Aggregate roots** (e.g., `Product`, `Cart`) are mutable and contain behavior methods:

```python
@dataclass
class Product:
    id: UUID
    name: str
    price: Decimal
    stock_quantity: int
    created_at: datetime

    @classmethod
    def create(cls, name: str, price: Decimal, stock_quantity: int) -> "Product":
        """Factory method for new products with validation."""
        return cls(
            id=uuid4(),
            name=validate_product_name(name),
            price=validate_product_price(price),
            stock_quantity=validate_stock_quantity(stock_quantity),
            created_at=datetime.now(),
        )

    def reserve_stock(self, quantity: int) -> None:
        """Reserve stock. Raises InsufficientStockError if unavailable."""
        if quantity > self.stock_quantity:
            raise InsufficientStockError(...)
        self.stock_quantity -= quantity

    def release_stock(self, quantity: int) -> None:
        """Release previously reserved stock."""
        self.stock_quantity += quantity
```

**Value objects** within aggregates (e.g., `CartItem`, `OrderItem`) remain frozen since they have no independent lifecycle:

```python
@dataclass(frozen=True)
class CartItem:
    id: UUID
    product_id: UUID        # Reference by ID only
    product_name: str       # Snapshot of product name when added
    unit_price: Decimal     # Snapshot of price when added
    quantity: int

    @classmethod
    def create(cls, product_id: UUID, product_name: str,
               unit_price: Decimal, quantity: int) -> "CartItem":
        """Factory method with validation."""
        return cls(
            id=uuid4(),
            product_id=product_id,
            product_name=product_name,
            unit_price=unit_price,
            quantity=validate_positive_quantity(quantity),
        )
```

**Aggregates with child entities** manage their children through behavior methods:

```python
@dataclass
class Cart:
    id: UUID
    items: List[CartItem]   # Mutable list of immutable items
    created_at: datetime

    def add_item(self, product_id: UUID, product_name: str,
                 unit_price: Decimal, quantity: int) -> None:
        """Add item or merge with existing. Validates quantity."""
        validate_positive_quantity(quantity)
        existing = self.get_item_by_product_id(product_id)
        if existing:
            # Merge: replace with updated quantity
            new_item = existing.with_quantity(existing.quantity + quantity)
            self.items = [new_item if i.id == existing.id else i for i in self.items]
        else:
            self.items.append(CartItem.create(product_id, product_name, unit_price, quantity))

    def remove_item(self, product_id: UUID) -> CartItem:
        """Remove and return item for stock release. Raises if not found."""
        item = self.get_item_by_product_id(product_id)
        if item is None:
            raise CartItemNotFoundError(str(product_id))
        self.items = [i for i in self.items if i.id != item.id]
        return item

    def submit(self) -> Order:
        """Create Order from cart and clear items. Raises if empty."""
        if not self.items:
            raise EmptyCartError()
        # ... create order, clear self.items
```

### Factory methods and reconstitution

Aggregates use two patterns for instantiation:

1. **Factory methods (`create()`)** - For creating new instances with validation:
   ```python
   product = Product.create(name="Widget", price="19.99", stock_quantity=100)
   ```

2. **Constructor** - For reconstituting from persistence (no re-validation needed):
   ```python
   # Used by repositories when loading from database
   product = Product(id=row.id, name=row.name, price=row.price, ...)
   ```

This separation allows aggregates to enforce invariants on creation while avoiding redundant validation when loading trusted data from the database.

### Validation organization

Validation functions are organized by aggregate:

```
domain/
├── validation.py                      # Shared validations (e.g., validate_positive_quantity)
└── aggregates/
    └── product/
        └── validation.py              # Product-specific validations
```

### Recursive `to_dict()` conversion

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

### Thin Django views

Django views become simple pass-throughs:

```python
def list_entities(request):
    entities = application_service.get_all_entities()
    return Response({"results": [to_dict(e) for e in entities]})
```

### Request → Response flow

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

## Concurrency control

The application must handle concurrent requests safely to prevent race conditions that could corrupt data (e.g., overselling stock, duplicate records). This section documents the patterns used to prevent race conditions.

### Non-functional requirement

All operations that read-then-modify shared state must be protected against concurrent access. The system must prevent:
- Stock going negative due to concurrent reservations
- Duplicate records bypassing uniqueness checks
- Lost updates when multiple requests modify the same data

### Patterns and approaches

Choose the appropriate pattern based on the type of operation:

| Scenario | Pattern | Implementation |
|----------|---------|----------------|
| Read-then-modify (e.g., stock updates) | Row-level locking | `select_for_update()` before reading |
| Check-then-create singletons | Atomic get-or-create | `get_or_create()` with fixed identifier |
| Uniqueness validation | DB constraint + fallback | Unique constraint + catch `IntegrityError` |
| Multiple operations on same resource | Lock ordering | Acquire locks in consistent order |

### Row-level locking for read-then-modify

When an operation reads a value, makes a decision based on it, and then writes an update, use `select_for_update()` to acquire an exclusive lock on the row:

```python
# In repository interface (domain layer)
@abstractmethod
def get_by_id_for_update(self, entity_id: UUID) -> Entity | None:
    """Get entity with row-level lock for update."""
    pass

# In repository implementation (infrastructure layer)
def get_by_id_for_update(self, entity_id: UUID) -> Entity | None:
    try:
        model = EntityModel.objects.select_for_update().get(id=entity_id)
        return self._to_domain(model)
    except EntityModel.DoesNotExist:
        return None

# In application service
def reserve_resource(self, entity_id: str, quantity: int) -> Entity:
    entity = self.uow.entities.get_by_id_for_update(entity_id)  # Lock acquired
    # Delegate to aggregate - it validates and mutates in place
    entity.reserve(quantity)  # Raises if insufficient
    # Persist the mutated aggregate
    return self.uow.entities.save(entity)
```

The lock is held until the transaction commits, preventing other transactions from reading or modifying the row.

### Atomic get-or-create for singletons

When implementing singleton patterns (e.g., a single cart), use `get_or_create()` with a fixed identifier to prevent duplicate creation:

```python
SINGLETON_ID = UUID("00000000-0000-0000-0000-000000000001")

def get_singleton(self) -> Entity:
    model, _ = EntityModel.objects.get_or_create(id=SINGLETON_ID)
    return self._to_domain(model)
```

This is atomic at the database level - if two requests try to create simultaneously, only one succeeds and the other returns the existing record.

### Database constraints with application fallback

For uniqueness validation, rely on database constraints as the ultimate enforcement, with application-level checks for better error messages:

```python
def create_entity(self, name: str) -> Entity:
    # Fast path: application-level check for common case
    if self.uow.entities.exists_by_name(name):
        raise DuplicateEntityError(name)

    entity = Entity(id=uuid4(), name=name)

    try:
        return self.uow.entities.save(entity)
    except IntegrityError:
        # Handle race condition: another request created it after our check
        raise DuplicateEntityError(name)
```

This provides both good user experience (fast error response) and correctness (database enforces constraint atomically).

## Domain events

Domain events enable loose coupling between aggregates and support cross-cutting concerns (like audit logging) without polluting domain logic. Events are dispatched after the transaction commits, ensuring consistency.

### Event collection pattern

Aggregates collect events internally during business operations. The application layer retrieves and dispatches them after saving:

```python
@dataclass
class Product:
    # ... fields ...
    _domain_events: List[DomainEvent] = field(default_factory=list, repr=False, compare=False)

    def reserve_stock(self, quantity: int) -> None:
        if quantity > self.stock_quantity:
            raise InsufficientStockError(...)
        self.stock_quantity -= quantity
        self._raise_event(StockReserved(
            product_id=self.id,
            quantity_reserved=quantity,
            remaining_stock=self.stock_quantity,
            actor_id="anonymous",
        ))

    def _raise_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def get_domain_events(self) -> List[DomainEvent]:
        return list(self._domain_events)

    def clear_domain_events(self) -> None:
        self._domain_events = []
```

### Dispatch flow

```
Application Service saves aggregate
    ↓
Application Service collects events: uow.collect_events_from(aggregate)
    ↓
Transaction commits
    ↓
Unit of Work dispatches events: uow.dispatch_events()
    ↓
Handlers execute (sync first, then async)
```

### Sync vs async handlers

The dispatcher supports both handler types:

- **Sync handlers** (`register()`): Run immediately in the calling thread. Use for fast, critical handlers like audit logging.
- **Async handlers** (`register_async()`): Run in a background thread pool. Use for slow operations like sending emails or calling external APIs.

```python
dispatcher.register(StockReserved, audit_log_handler)           # sync
dispatcher.register_async(OrderCreated, send_confirmation_email) # async
```

Sync handlers complete before the response returns. Async handlers are submitted to a thread pool and run in the background.

### Handler resilience

Handler failures are logged but don't break operations or prevent other handlers from running. This ensures the business transaction succeeds even if a handler fails.

## Authentication and authorization

The application uses Django session-based authentication with role-based access control. The key architectural pattern is `UserContext` - a framework-agnostic representation of the authenticated user.

### UserContext pattern

The domain layer defines a `UserContext` dataclass that contains only the information needed for authorization and audit logging:

```python
@dataclass(frozen=True)
class UserContext:
    user_id: UUID
    username: str
    role: Role  # Enum: ADMIN, CUSTOMER

    def is_admin(self) -> bool
    def is_customer(self) -> bool

    @property
    def actor_id(self) -> str  # For domain event audit logging
```

This keeps the domain layer free of Django dependencies while enabling authorization decisions in the application layer.

### Layer responsibilities

| Layer | Auth Concern | Django Dependency |
|-------|-------------|-------------------|
| Domain | None - completely auth-unaware | None |
| Application | Authorization checks using UserContext | None |
| Infrastructure | Session handling, User → UserContext conversion | Yes |

### Request flow with auth

```
HTTP Request with Session Cookie
    ↓
Django SessionMiddleware (authenticates)
    ↓
@require_auth decorator
    ↓ Converts Django User → UserContext
View Function
    ↓ Passes UserContext to application service
Application Service
    ↓ Checks permissions, uses actor_id for events
Domain Aggregates (auth-unaware)
```

### Authorization in application services

Permission checks happen in application services, not in views or domain:

```python
class ProductService:
    def create_product(self, ..., user_context: UserContext) -> Product:
        if not user_context.is_admin():
            raise PermissionDeniedError("create_product", "Only admins can create products")
        # ... proceed with creation
```

This centralizes authorization logic and keeps it testable without Django.

## Future considerations

The following topics are intentionally deferred to keep the initial implementation simple. They may be worth revisiting as the application grows:

### Value objects

Wrapping primitive types in domain-specific value objects (e.g., `Money`, `Quantity`, `Name`) can provide:
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

The current implementation uses a single Django app (`infrastructure/django_app/`) containing all models, views, and repositories. An alternative approach is to create one Django app per aggregate.

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
