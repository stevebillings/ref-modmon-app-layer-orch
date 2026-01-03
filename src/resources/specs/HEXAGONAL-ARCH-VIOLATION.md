# Hexagonal Architecture Violation: UnitOfWork Dependency (RESOLVED)

## Original Problem

In `cart_service.py` (application layer), there was a direct dependency on `infrastructure.django_app.unit_of_work.UnitOfWork`, which had a dependency on `django.db.transaction`. This was a violation of hexagonal architecture principles.

Additionally, `product_service.py` imported `django.db.IntegrityError` directly, leaking framework details into the application layer.

## Why This Violated Hexagonal Architecture

In proper hexagonal architecture:

1. **Domain layer** - Pure business logic, no external dependencies
2. **Application layer** - Orchestrates use cases, depends only on abstractions (ports)
3. **Infrastructure layer** - Implements the abstractions (adapters)

The dependency rule is that inner layers should never depend on outer layers.

## Solution Implemented

### 1. Created UnitOfWork Port

A new abstract base class was created at `application/ports/unit_of_work.py`:

```python
class UnitOfWork(ABC):
    @abstractmethod
    def get_product_repository(self) -> ProductRepository: ...
    @abstractmethod
    def get_cart_repository(self) -> CartRepository: ...
    @abstractmethod
    def get_order_repository(self) -> OrderRepository: ...
    @abstractmethod
    def collect_events_from(self, aggregate: Any) -> None: ...
    @abstractmethod
    def dispatch_events(self) -> None: ...
```

### 2. Renamed Infrastructure Implementation

The concrete implementation was renamed to `DjangoUnitOfWork` and now inherits from the port:

```python
# infrastructure/django_app/unit_of_work.py
from application.ports.unit_of_work import UnitOfWork

class DjangoUnitOfWork(UnitOfWork):
    # ... implementation
```

### 3. Updated Application Services

All application services now import from the port:

```python
# application/services/cart_service.py
from application.ports.unit_of_work import UnitOfWork
```

### 4. Moved IntegrityError Handling to Repository

The `django.db.IntegrityError` handling was moved from `ProductService` to `DjangoProductRepository`, which catches the exception and raises the domain-specific `DuplicateProductError`. This keeps framework exceptions contained within the infrastructure layer.

## Current Architecture

```
application/
├── ports/
│   └── unit_of_work.py      # UnitOfWork ABC (port)
└── services/
    ├── cart_service.py      # imports from application.ports
    ├── order_service.py     # imports from application.ports
    └── product_service.py   # imports from application.ports

infrastructure/django_app/
└── unit_of_work.py          # DjangoUnitOfWork (adapter)
```

The dependency direction now correctly flows inward:
- Application layer depends on its own port abstraction
- Infrastructure layer implements the port and depends on application/domain
- Views (composition root) wire the concrete implementation
