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
│   │   ├── aggregates/            # Organized by aggregate
│   │   │   ├── <aggregate_a>/
│   │   │   │   ├── entity.py              # Aggregate root entity
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   └── <aggregate_b>/
│   │   │       ├── entities.py            # Aggregate root + child entities
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
- One repository per aggregate root (no separate repository for child entities within an aggregate)
- **Aggregate isolation**: An aggregate must never import or embed entities from another aggregate. References to other aggregates must be by ID only. Any data needed from another aggregate should be passed in as snapshots (copied values) by the application layer at the time of the operation. This keeps aggregates independently evolvable and testable.

## Data flow pattern

The backend uses a simplified pattern for returning data from API endpoints, keeping the Django layer thin and the domain logic framework-agnostic.

### Domain entities as frozen dataclasses

Domain entities are defined as frozen (immutable) dataclasses in the domain layer:

```python
@dataclass(frozen=True)
class ExampleEntity:
    id: UUID
    name: str
    value: Decimal
    created_at: datetime

@dataclass(frozen=True)
class ChildEntity:
    id: UUID
    parent_id: UUID        # Reference by ID only (not the parent entity)
    parent_name: str       # Snapshot of parent name when created
    quantity: int

@dataclass(frozen=True)
class ParentEntity:
    id: UUID
    items: List[ChildEntity]  # Child entities contain snapshots, not parent references
    created_at: datetime
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
def update_entity(self, entity_id: str, new_value: int) -> Entity:
    entity = self.uow.entities.get_by_id_for_update(entity_id)  # Lock acquired
    # Check business rules against locked data
    if new_value > entity.available:
        raise InsufficientResourceError(...)
    # Update is safe - no other transaction can modify this row
    updated = entity.with_value(new_value)
    return self.uow.entities.save(updated)
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
