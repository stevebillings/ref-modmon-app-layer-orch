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
