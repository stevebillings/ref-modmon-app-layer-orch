# Reference web application

This is a reference web application. It's purpose is to demonstrate an architecture (focusing, at least for now, on the backend) for a medium complexity web application developed by a very small team (about 3 developers). The architecture that this project is demonstrating is a Domain Driven Design Modular Monolith that uses a thin application layer to orchestrate cross-aggregate operations.

The goal is to keep the application simple enough to be easy to understand, while still solving (demonstrating how to solve) a variety of problems typical of a medium complexity web application. For example: it includes solutions for:

1. Domain Driven Design Modular Monolith using Hexagonal architecture
2. Cross-aggregate operations
3. Domain events with sync/async handler support
4. Audit logging via domain event subscription

The specifications for the reference project are in the specs directory. These should always be considered, and as we change the application, we must also change the specs to keep them in sync.

Each time we prepare to introduce a new type of problem and its solution, we should consider changing or expanding the requirements and the application itself to make it better illustrate the problem and solution.

## Architecture Rules (ENFORCED)

These rules are enforced by `import-linter`. Run `lint-imports` from the backend directory to check.

### Layer Dependencies

The backend follows hexagonal architecture with strict layer separation:

```
infrastructure/ → application/ → domain/
     ↓                ↓
   (implements)    (uses ports)
```

**NEVER violate these import rules:**

| Layer | Can Import From | CANNOT Import From |
|-------|-----------------|-------------------|
| `domain/` | Standard library only | `application/`, `infrastructure/`, `django`, `rest_framework` |
| `application/` | `domain/`, standard library | `infrastructure/`, `django`, `rest_framework` |
| `infrastructure/` | `domain/`, `application/`, Django, etc. | (no restrictions) |

### Aggregate Isolation

Aggregates must NEVER import from each other:

- `domain/aggregates/cart/` must NOT import from `product/` or `order/`
- `domain/aggregates/product/` must NOT import from `cart/` or `order/`
- `domain/aggregates/order/` must NOT import from `cart/` or `product/`

Cross-aggregate coordination happens in the **application layer**, not in aggregates.

### When You Need Cross-Layer Functionality

If you need functionality from a forbidden layer, use the **Port/Adapter pattern**:

1. Define a **Port interface** in `application/ports/` (e.g., `MetricsPort`)
2. Implement an **Adapter** in `infrastructure/` (e.g., `DjangoMetricsAdapter`)
3. **Inject** the adapter via constructor in the application service

Example:
```python
# application/ports/metrics.py
class MetricsPort(ABC):
    @abstractmethod
    def time_operation(self, name: str) -> ContextManager: ...

# infrastructure/django_app/metrics.py
class DjangoMetricsAdapter(MetricsPort):
    def time_operation(self, name: str) -> ContextManager: ...

# application/services/cart_service.py
class CartService:
    def __init__(self, uow: UnitOfWork, metrics: MetricsPort): ...
```

### Authorization Location

Authorization checks belong in **application services**, not views:

```python
# CORRECT - in application service
class ProductService:
    def delete_product(self, id: str, user_context: UserContext):
        if not user_context.is_admin():
            raise PermissionDeniedError(...)

# WRONG - in view
def delete_product_view(request, user_context):
    if not user_context.is_admin():  # Don't do this!
        return Response({"error": "..."}, status=403)
```

### Verifying Architecture

Run from the backend directory:
```bash
lint-imports
```

All contracts must pass before committing code.
