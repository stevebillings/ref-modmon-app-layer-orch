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
│   │   │   ├── workout_structure/
│   │   │   │   ├── entity.py              # WorkoutStructure aggregate root
│   │   │   │   └── repository.py          # Repository interface (ABC)
│   │   │   └── performed_workout/
│   │   │       ├── entities.py            # PerformedWorkout (root) + WorkoutInterval
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
│           │   ├── workout_structure_repository.py
│           │   └── performed_workout_repository.py
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
- One repository per aggregate root (no separate repository for WorkoutInterval)

### Data flow pattern

The backend uses a simplified pattern for returning data from API endpoints, keeping the Django layer thin and the domain logic framework-agnostic.

#### Domain entities as frozen dataclasses

Domain entities are defined as frozen (immutable) dataclasses in the domain layer:

```python
@dataclass(frozen=True)
class WorkoutStructure:
    id: UUID
    interval_count: int
    work_phase_meters: int
    rest_phase_minutes: int
    created_at: datetime

@dataclass(frozen=True)
class PerformedWorkout:
    id: UUID
    workout_structure: WorkoutStructure  # Nested dataclass
    performed_date: date
    created_at: datetime
    intervals: List[WorkoutInterval]     # Nested list of dataclasses
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
def list_workout_structures(request):
    structures = application_service.get_all_workout_structures()
    return Response({"results": [to_dict(s) for s in structures]})
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

#### WorkoutStructure
- **id** (Primary Key)
- **interval_count** (integer) - Number of intervals in the workout
- **work_phase_meters** (integer) - Length of each work phase in meters (same for all intervals)
- **rest_phase_minutes** (integer) - Duration of each rest phase in whole minutes (same for all intervals)
- **created_at** (timestamp)
- **Note**: Name is not stored. Backend generates a display name at read time (e.g., "5 x 500m / 2min rest") and includes it in API responses.
- **Uniqueness constraint**: The combination of (interval_count, work_phase_meters, rest_phase_minutes) must be unique. Attempting to create a duplicate returns an error.
- **Validation**:
  - interval_count: 1–100 inclusive
  - work_phase_meters: 1–100,000 inclusive
  - rest_phase_minutes: 1–10 inclusive

#### PerformedWorkout
- **id** (Primary Key)
- **workout_structure_id** (Foreign Key to WorkoutStructure)
- **performed_date** (date) - The date the workout was performed (user-entered)
- **created_at** (timestamp)
- **Cascade delete**: When a WorkoutStructure is deleted, all associated PerformedWorkouts are also deleted.
- **Validation**:
  - performed_date: Must not be more than one day in the future (up to and including tomorrow)

#### WorkoutInterval
- **id** (Primary Key)
- **performed_workout_id** (Foreign Key to PerformedWorkout)
- **interval_number** (integer) - The interval number (1, 2, 3, etc.)
- **time_seconds** (integer) - Total time for the work phase in seconds
- **Validation**:
  - time_seconds: Must be positive (> 0)
- **Note**: Frontend handles conversion between seconds (for API/DB) and h:mm:ss format (for user display/entry)

### Backend APIs

#### WorkoutStructure Endpoints
- **GET /api/workout-structures/** - List all workout structures
  - Response: Array of WorkoutStructure objects (each includes generated `name` field for display)
  - Ordering: Descending by created_at (newest first)
- **POST /api/workout-structures/** - Create a new workout structure
  - Request body: `{ interval_count, work_phase_meters, rest_phase_minutes }`
  - Response: Created WorkoutStructure object (includes generated `name` field)
  - Error: 400 if validation fails or if a workout structure with the same (interval_count, work_phase_meters, rest_phase_minutes) already exists
- **DELETE /api/workout-structures/{id}/** - Delete a workout structure
  - Response: 204 No Content
  - Note: Cascade deletes all associated PerformedWorkouts

#### PerformedWorkout Endpoints
- **GET /api/performed-workouts/** - List all performed workouts
  - Response: Array of PerformedWorkout objects (includes nested workout_structure details and intervals with time in seconds)
  - Ordering: Descending by created_at (newest first)
- **POST /api/performed-workouts/** - Create a new performed workout
  - Request body: `{ workout_structure_id, performed_date, intervals: [{ interval_number, time_seconds }] }`
  - Response: Created PerformedWorkout object with intervals
  - Error: 400 if validation fails (invalid date, non-positive time_seconds, etc.)
- **DELETE /api/performed-workouts/{id}/** - Delete a performed workout
  - Response: 204 No Content

## Future considerations

The following topics are intentionally deferred to keep the initial implementation simple. They may be worth revisiting as the application grows:

### Value objects

Wrapping primitive types in domain-specific value objects (e.g., `Meters`, `Minutes`, `IntervalCount`) can provide:
- Type safety (compiler catches mixing up meters vs. seconds)
- Validation at construction time
- Domain-specific behavior (e.g., formatting methods)

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
